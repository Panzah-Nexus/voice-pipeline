#!/usr/bin/env python
"""Kokoro TTS subprocess server

This module is **not** imported by the main application. Instead, it is executed
as a standalone **sub-process** from within `KokoroSubprocessTTSService`.
It loads the Kokoro ONNX model (and, by extension, heavy CUDA / onnxruntime-gpu
libraries) in *its own* Python interpreter / virtual-environment so that those
DLL/SO dependencies never clash with the main process.

The protocol is newline-delimited JSON (a.k.a. *jsonl*):

1. The parent process sends a single JSON object per line of **UTF-8** text on
   *stdin* with the following shape::

       {"text": "Hello world", "voice_id": "af_sarah", "language": "en-us", "speed": 1.0}

   Only the ``text`` key is mandatory – the other keys fall back to the values
   originally supplied on the command-line.

2. For every request the server writes a series of JSON objects to *stdout*
   (each terminated by a ``\n``)::

       {"type": "started"}
       {"type": "audio_chunk", "sample_rate": 24000, "data": "<base64 pcm>"}
       ... (0-n more "audio_chunk" messages) ...
       {"type": "stopped"}
       {"type": "eof"}

   The parent treats them as a *stream* and converts them into Pipecat frames.

Errors are returned as::

       {"type": "error", "message": "<description>"}

One request is processed at a time.  Parallelism is left to the parent process
(which can spin up several subprocesses if required).
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import sys
from typing import Optional

import numpy as np
from loguru import logger

# kokoro-onnx and onnxruntime-gpu live **in this environment** so importing them
# here is safe and isolated from the parent interpreter.
try:
    from kokoro_onnx import Kokoro  # type: ignore
except ModuleNotFoundError as e:
    print(json.dumps({"type": "error", "message": f"Missing dependency: {e}"}), flush=True)
    sys.exit(1)

import onnxruntime as ort  # noqa: E402


def parse_args() -> argparse.Namespace:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Run Kokoro TTS as a subprocess server")
    parser.add_argument("--model-path", required=True, help="Path to kokoro-vX.Y.onnx model file")
    parser.add_argument("--voices-path", required=True, help="Path to voices-vX.Y.bin file")
    parser.add_argument("--voice-id", default="af_sarah", help="Voice ID to use by default")
    parser.add_argument("--language", default="en-us", help="Language code (e.g., en-us)")
    parser.add_argument("--speed", type=float, default=1.0, help="Base speaking speed (1.0 = normal)")
    parser.add_argument("--sample-rate", type=int, default=None, help="Force output sample-rate")
    parser.add_argument("--debug", action="store_true", help="Enable verbose logging on stderr")
    return parser.parse_args()


class KokoroServer:
    def __init__(
        self,
        model_path: str,
        voices_path: str,
        *,
        voice_id: str = "af_sarah",
        language: str = "en-us",
        speed: float = 1.0,
        sample_rate: Optional[int] = None,
    ) -> None:
        # Initialise Kokoro session – CUDA if available, else CPU.
        providers = ort.get_available_providers()
        use_cuda = "CUDAExecutionProvider" in providers

        if use_cuda:
            sess = ort.InferenceSession(
                model_path,
                providers=[
                    (
                        "CUDAExecutionProvider",
                        {"cudnn_conv_algo_search": "EXHAUSTIVE"},
                    ),
                    "CPUExecutionProvider",
                ],
            )
            if hasattr(Kokoro, "from_session"):
                self._kokoro = Kokoro.from_session(sess, voices_path)
            else:
                self._kokoro = Kokoro(
                    model_path,
                    voices_path,
                    providers=[
                        (
                            "CUDAExecutionProvider",
                            {"cudnn_conv_algo_search": "EXHAUSTIVE"},
                        ),
                        "CPUExecutionProvider",
                    ],
                )
        else:
            self._kokoro = Kokoro(model_path, voices_path)

        self._voice_id = voice_id
        self._language = language
        self._speed = speed
        self._sample_rate = sample_rate

    async def run_forever(self) -> None:  # pragma: no cover
        """Process stdin forever until EOF."""

        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            try:
                line = await reader.readline()
            except Exception as e:  # pragma: no cover – catastrophic
                logger.error(f"Error reading stdin: {e}")
                break

            if not line:  # EOF
                break

            try:
                request = json.loads(line.decode())
            except json.JSONDecodeError:
                self._send_json({"type": "error", "message": "Invalid JSON"})
                continue

            text = request.get("text")
            if not text:
                self._send_json({"type": "error", "message": "Request missing 'text' field"})
                continue

            voice_id = request.get("voice_id", self._voice_id)
            language = request.get("language", self._language)
            speed = float(request.get("speed", self._speed))

            await self._process_text(text, voice_id, language, speed)

            # Signal request finished.  Having an explicit sentinel makes life
            # easier for the parent side – especially if we ever decide to
            # support persistent connections processing multiple requests
            # concurrently.
            self._send_json({"type": "eof"})

    def _send_json(self, payload: dict) -> None:
        """Serialize *payload* and write it to stdout followed by a newline."""
        sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
        sys.stdout.flush()

    async def _process_text(
        self,
        text: str,
        voice_id: str,
        language: str,
        speed: float,
    ) -> None:
        """Generate speech for *text* and emit streaming chunks."""
        try:
            self._send_json({"type": "started"})

            stream = self._kokoro.create_stream(
                text,
                voice=voice_id,
                speed=speed,
                lang=language,
            )

            MAX_RAW_BYTES = 16 * 1024  # 16 KB raw PCM ⇒ ~22 KB base64, < 64 KB limit

            async for samples, sample_rate in stream:
                # Convert to 16-bit PCM little-endian
                samples_int16 = (samples * 32767).astype(np.int16)
                raw = samples_int16.tobytes()

                # Split into manageable chunks so that the encoded line length
                # never exceeds asyncio.StreamReader's default 64 KB limit.
                for offset in range(0, len(raw), MAX_RAW_BYTES):
                    sub = raw[offset : offset + MAX_RAW_BYTES]
                    chunk_b64 = base64.b64encode(sub).decode()
                    self._send_json(
                        {
                            "type": "audio_chunk",
                            "sample_rate": sample_rate,
                            "data": chunk_b64,
                        }
                    )

            self._send_json({"type": "stopped"})
        except Exception as e:  # pragma: no cover
            logger.exception("Error generating TTS")
            self._send_json({"type": "error", "message": str(e)})


def entrypoint() -> None:  # pragma: no cover
    args = parse_args()

    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.disable("__main__")

    server = KokoroServer(
        model_path=args.model_path,
        voices_path=args.voices_path,
        voice_id=args.voice_id,
        language=args.language,
        speed=args.speed,
        sample_rate=args.sample_rate,
    )

    asyncio.run(server.run_forever())


if __name__ == "__main__":  # pragma: no cover
    entrypoint() 