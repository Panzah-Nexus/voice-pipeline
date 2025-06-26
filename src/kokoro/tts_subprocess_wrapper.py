import asyncio
import base64
import json
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, List, Optional

from loguru import logger
from pydantic import BaseModel

from pipecat.frames.frames import (
    ErrorFrame,
    Frame,
    TTSAudioRawFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
)
from pipecat.services.tts_service import TTSService


class KokoroSubprocessTTSService(TTSService):
    """Run Kokoro TTS inside an *external* Python interpreter.

    Heavy dependencies such as *onnxruntime-gpu* live in a dedicated virtual
    environment referenced by *python_path*.  We launch
    ``tts_subprocess_server.py`` in that environment and communicate with it via
    a newline-delimited JSON protocol.
    """

    class InputParams(BaseModel):
        python_path: Path  # Path to python interpreter in TTS virtual-env
        model_path: Path
        voices_path: Path
        voice_id: str = "af_sarah"
        language: str = "en-us"
        speed: float = 1.0
        sample_rate: Optional[int] = None
        debug: bool = False

    def __init__(self, params: "KokoroSubprocessTTSService.InputParams", **kwargs):
        super().__init__(sample_rate=params.sample_rate, **kwargs)
        self._params = params
        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._start_lock = asyncio.Lock()

    # ---------------------------------------------------------------------
    #   public helpers
    # ---------------------------------------------------------------------
    def can_generate_metrics(self) -> bool:  # noqa: D401 – Pipecat signature
        return True

    async def run_tts(self, text: str) -> AsyncGenerator[Frame, None]:  # noqa: D401
        """Generate TTS frames for *text* using the subprocess."""
        try:
            await self._ensure_subprocess()
        except Exception as e:
            logger.error(f"Failed to start subprocess: {e}")
            yield ErrorFrame(str(e))
            return

        assert self._writer and self._reader and self._process

        await self.start_ttfb_metrics()
        # send request
        request = {
            "text": text,
            "voice_id": self._params.voice_id,
            "language": self._params.language,
            "speed": self._params.speed,
        }
        self._writer.write(json.dumps(request, separators=(",", ":")).encode() + b"\n")
        await self._writer.drain()

        await self.start_tts_usage_metrics(text)

        yield TTSStartedFrame()

        # process responses until "eof"
        while True:
            try:
                line = await self._reader.readline()
            except Exception as e:
                logger.error(f"Error reading from TTS subprocess: {e}")
                yield ErrorFrame(str(e))
                return

            if not line:
                yield ErrorFrame("TTS subprocess terminated unexpectedly")
                await self._terminate_subprocess()
                return

            try:
                msg = json.loads(line.decode())
            except json.JSONDecodeError:
                logger.warning(f"Subprocess sent invalid JSON: {line[:100]}…")
                continue

            mtype = msg.get("type")

            if mtype == "audio_chunk":
                try:
                    raw = base64.b64decode(msg["data"])
                    sample_rate = int(msg["sample_rate"])
                except Exception as e:
                    logger.warning(f"Malformed audio_chunk from subprocess: {e}")
                    continue
                yield TTSAudioRawFrame(audio=raw, sample_rate=sample_rate, num_channels=1)
            elif mtype == "started":
                # already emitted a TTSStartedFrame; ignore
                pass
            elif mtype == "stopped":
                yield TTSStoppedFrame()
            elif mtype == "error":
                yield ErrorFrame(msg.get("message", "Unknown error"))
            elif mtype == "eof":
                # request complete
                break
            # else: ignore unknown

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    async def _ensure_subprocess(self) -> None:
        if self._process and self._process.returncode is None:
            return  # already running

        async with self._start_lock:
            # double-check inside lock
            if self._process and self._process.returncode is None:
                return

            # Build command
            server_script = Path(__file__).with_name("tts_subprocess_server.py")
            cmd = [
                str(self._params.python_path),
                str(server_script),
                "--model-path",
                str(self._params.model_path),
                "--voices-path",
                str(self._params.voices_path),
                "--voice-id",
                self._params.voice_id,
                "--language",
                self._params.language,
                "--speed",
                str(self._params.speed),
            ]
            if self._params.sample_rate:
                cmd.extend(["--sample-rate", str(self._params.sample_rate)])
            if self._params.debug:
                cmd.append("--debug")

            env = os.environ.copy()
            # Ensure CUDA visible etc.  Could add custom env tweaks here.

            logger.info(f"Starting Kokoro TTS subprocess: {' '.join(cmd)}")

            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=sys.stderr if self._params.debug else asyncio.subprocess.DEVNULL,
                env=env,
            )

            # The asyncio API already provides *StreamReader*/*StreamWriter* objects
            # attached to the subprocess via the ``stdout`` / ``stdin`` attributes.
            # Use them directly – no need for additional transport plumbing.
            self._reader = self._process.stdout  # type: ignore[assignment]
            self._writer = self._process.stdin  # type: ignore[assignment]

    async def _terminate_subprocess(self) -> None:
        if self._process and self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
        self._process = None
        self._reader = None
        self._writer = None 