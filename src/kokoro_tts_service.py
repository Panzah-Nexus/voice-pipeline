from __future__ import annotations

"""Pipecat-compatible Kokoro TTS service.

This module provides `KokoroTTSService`, an **offline** text-to-speech
implementation that relies on the open-weight `kokoro` (PyTorch) library.  It
streams raw 16-bit PCM audio back to Pipecat in real-time so that the
surrounding pipeline can forward audio to connected clients without
waiting for the entire utterance to finish.
"""

from typing import AsyncGenerator, Optional

import numpy as np
from loguru import logger
import torch

# Pipecat frame & base-service imports -------------------------------------------------
from pipecat.frames.frames import (
    ErrorFrame,
    Frame,
    TTSAudioRawFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
)

try:
    # Pipecat ≥0.0.70 location
    from pipecat.services.tts_service import TTSService
except ModuleNotFoundError:  # pragma: no cover – legacy path
    from pipecat.services.ai_services import TTSService

from pipecat.transcriptions.language import Language

# Third-party -------------------------------------------------------------------------
try:
    from kokoro import KPipeline  # type: ignore
except ModuleNotFoundError as e:  # pragma: no cover
    raise RuntimeError(
        "The `kokoro` package is not installed. Add `kokoro` to requirements.txt and rebuild the image."  # noqa: E501
    ) from e

# ------------------------------------------------------------------------------------
# Helper utilities
# ------------------------------------------------------------------------------------


def _language_to_kokoro_code(language: Language) -> Optional[str]:
    """Map Pipecat `Language` enum to Kokoro language code.

    Kokoro v1.0 currently supports English only, exposed as ``en-us``.  We keep
    the function generic so that adding languages later only requires updating
    this mapping table.
    """

    mapping = {Language.EN: "en-us"}

    # Exact match first
    if language in mapping:
        return mapping[language]

    # Fall-back: try to derive base ISO-639-1 code from a variant like
    # ``en-GB`` → ``en-us`` (so that at least something plays).
    lang_str = str(language.value).lower()
    base = lang_str.split("-")[0]
    if base == "en":
        return "en-us"

    return None


# ------------------------------------------------------------------------------------
# TTS service
# ------------------------------------------------------------------------------------


class KokoroTTSService(TTSService):
    """Text-to-Speech service powered by Kokoro-ONNX.

    Parameters
    ----------
    model_path:
        Path to the Kokoro ONNX model (e.g. ``model_fp16.onnx``).
    voices_path:
        Path to the *voices binary* (``voices-v1.0.bin``).
    voice_id:
        Which voice embedding to use.  Consult ``Kokoro.list_voices()`` for
        available IDs.  Defaults to ``af_sarah``.
    sample_rate:
        Output sample-rate for the generated PCM stream.  Kokoro's native rate
        is **24 000 Hz**.
    language:
        Desired language for the utterance (currently affects only the phoneme
        pipeline).  Unsupported languages will fall back to English.
    speed:
        Playback speed multiplier (1.0 = original pitch).
    """

    # Custom parameter container for TTS settings (kept small & explicit)
    class InputParams:  # noqa: D401 – simple namespace, not a full dataclass to avoid extra deps
        """Runtime-tuneable synthesis parameters."""

        def __init__(
            self,
            language: Optional[Language] = Language.EN,
            speed: float = 1.0,
        ) -> None:
            self.language = language
            self.speed = speed

    DEFAULT_SAMPLE_RATE = 24_000

    def __init__(
        self,
        *,
        model_path: str,
        voices_path: str,
        voice_id: str = "af_sarah",
        sample_rate: Optional[int] = None,
        params: Optional["KokoroTTSService.InputParams"] = None,
        **kwargs,
    ) -> None:
        super().__init__(sample_rate=sample_rate or self.DEFAULT_SAMPLE_RATE, **kwargs)

        params = params or self.InputParams()

        logger.info(
            "Initialising Kokoro TTS (model='{}', voices='{}', voice='{}')",
            model_path,
            voices_path,
            voice_id,
        )

        # Initialise Kokoro pipeline (automatically loads GPU weights if available)
        self._language_code: str = (
            _language_to_kokoro_code(params.language) if params.language else "en-us"
        )

        # Kokoro offers both a native PyTorch and an ONNX inference backend. The
        # GPU-accelerated PyTorch path is preferred here.  If the caller passes
        # a *.onnx file we deliberately ignore it (to avoid pulling the ONNX
        # runtime and clashing with the kokoro_onnx wheel).

        model_path_arg = None
        if model_path and not model_path.lower().endswith(".onnx"):
            model_path_arg = model_path

        try:
            self._pipeline = KPipeline(
                lang_code=self._language_code,
                model_path=model_path_arg,
                voices_path=voices_path if voices_path else None,
                repo_id=None,  # Use local cache / $KOKORO_HOME if set
            )
        except TypeError:
            # Older kokoro versions didn't expose model_path/voices_path –
            # retry with minimal kwargs for compatibility.
            self._pipeline = KPipeline(lang_code=self._language_code)

        self._voice_id = voice_id
        self._speed: float = params.speed

        logger.info("Kokoro pipeline initialised successfully (backend=PyTorch)")

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------

    async def set_voice(self, voice: str):  # noqa: D401
        """Change the voice on the fly (thread-safe)."""
        self._voice_id = voice

    # Pipecat hooks --------------------------------------------------------

    def can_generate_metrics(self) -> bool:  # pragma: no cover
        # Kokoro provides deterministic synthesis; we can expose timing later.
        return False

    async def run_tts(self, text: str) -> AsyncGenerator[Frame, None]:
        """Generate speech and stream PCM chunks back to Pipecat."""

        logger.debug("Kokoro generating for: %s", text.replace("\n", " ")[:120])
        try:
            yield TTSStartedFrame()

            # `KPipeline.__call__` yields (graphemes, phonemes, audio) tuples.
            for _, _, audio in self._pipeline(
                text,
                voice=self._voice_id,
                speed=self._speed,
                split_pattern=None,
            ):
                # Convert torch.Tensor → numpy → int16 and stream out
                if isinstance(audio, torch.Tensor):
                    samples = audio.cpu().numpy()
                else:
                    samples = audio

                pcm_i16 = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
                yield TTSAudioRawFrame(
                    audio=pcm_i16.tobytes(),
                    sample_rate=self._sample_rate,
                    num_channels=1,
                )

            yield TTSStoppedFrame()

        except Exception as exc:
            logger.exception("Kokoro TTS failed: %s", exc)
            yield ErrorFrame(error=f"Kokoro TTS error: {exc}") 