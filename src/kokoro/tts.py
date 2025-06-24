#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#
# This code originally written by Marmik Pandya (marmikcfc - github.com/marmikcfc)

import base64
import json
import uuid
import numpy as np
from typing import AsyncGenerator, List, Optional, Union

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
from pipecat.transcriptions.language import Language

# load Kokoro from kokoro-onnx
try:
    from kokoro_onnx import Kokoro
except ModuleNotFoundError as e:
    logger.error(f"Exception: {e}")
    logger.error(
        "In order to use Kokoro, you need to `pip install kokoro-onnx`. Also, download the model files from the Kokoro repository."
    )
    raise Exception(f"Missing module: {e}")


def language_to_kokoro_language(language: Language) -> Optional[str]:
    """Convert pipecat Language to Kokoro language code."""
    BASE_LANGUAGES = {
        Language.EN: "en-us",
        Language.FR: "fr-fr",
        Language.IT: "it",
        Language.JA: "ja",
        Language.CMN: "cmn"
        # Add more language mappings as supported by Kokoro
    }

    result = BASE_LANGUAGES.get(language)

    # If not found in base languages, try to find the base language from a variant
    if not result:
        lang_str = str(language.value)
        base_code = lang_str.split("-")[0].lower()
        # Look up the base code in our supported languages
        result = f"{base_code}-us" if base_code in ["en"] else None

    return result


class KokoroTTSService(TTSService):
    """Text-to-Speech service using Kokoro for on-device TTS.
    
    This service uses Kokoro to generate speech without requiring external API connections.
    """
    class InputParams(BaseModel):
        """Configuration parameters for Kokoro TTS service."""
        language: Optional[Language] = Language.EN
        speed: Optional[float] = 1.0

    def __init__(
        self,
        *,
        model_path: str,
        voices_path: str,
        voice_id: str = "af_sarah",
        sample_rate: Optional[int] = None,
        params: InputParams = InputParams(),
        **kwargs,
    ):
        """Initialize Kokoro TTS service.
        
        Args:
            model_path: Path to the Kokoro ONNX model file
            voices_path: Path to the Kokoro voices file
            voice_id: ID of the voice to use
            sample_rate: Output audio sample rate
            params: Additional configuration parameters
        """
        super().__init__(sample_rate=sample_rate, **kwargs)
        logger.info(
            f"Initializing Kokoro TTS service with model_path: {model_path} and voices_path: {voices_path}"
        )

        # ------------------------------------------------------------------
        # Prefer GPU execution if ONNX Runtime with CUDA is available.
        # kokoro_onnx >=0.4.4 accepts a ``providers`` kw-arg; older versions
        # can still be used by creating the InferenceSession manually and
        # calling ``Kokoro.from_session``.
        # ------------------------------------------------------------------
        providers = None
        try:
            import onnxruntime as ort  # type: ignore

            avail = ort.get_available_providers()
            if "CUDAExecutionProvider" in avail:
                providers = [
                    (
                        "CUDAExecutionProvider",
                        {"cudnn_conv_algo_search": "DEFAULT"},
                    ),
                    "CPUExecutionProvider",
                ]
                logger.info("ONNXRuntime CUDA provider detected – using GPU for Kokoro TTS")
            else:
                logger.warning("CUDAExecutionProvider not available; Kokoro will run on CPU")
        except ImportError:
            logger.warning("onnxruntime not installed – Kokoro will run on CPU")

        # Instantiate Kokoro with the chosen providers.
        try:
            if providers and "providers" in Kokoro.__init__.__code__.co_varnames:
                # Newer kokoro_onnx supports providers directly.
                self._kokoro = Kokoro(model_path, voices_path, providers=providers)  # type: ignore[arg-type]
            elif providers:
                # Fallback path for older kokoro_onnx: create a session first.
                import onnxruntime as ort  # re-import inside the fallback

                session = ort.InferenceSession(model_path, providers=providers)
                if hasattr(Kokoro, "from_session"):
                    self._kokoro = Kokoro.from_session(session, voices_path)  # type: ignore[attr-defined]
                else:
                    # Ultimate fallback – run on CPU
                    logger.warning("Kokoro `from_session` not available; falling back to CPU mode")
                    self._kokoro = Kokoro(model_path, voices_path)
            else:
                # CPU only path
                self._kokoro = Kokoro(model_path, voices_path)
        except Exception as e:
            logger.error(f"Failed to initialise Kokoro with GPU support: {e}")
            self._kokoro = Kokoro(model_path, voices_path)

        # ------------------------------------------------------------------
        logger.info("Kokoro initialized (GPU={} )".format("CUDAExecutionProvider" in (providers or [])))
        self._settings = {
            "language": self.language_to_service_language(params.language)
            if params.language
            else "en-us",
            "speed": params.speed,
        }
        self.set_voice(voice_id)  # Presumably this sets self._voice_id

        logger.info("Kokoro TTS service initialized")

    def can_generate_metrics(self) -> bool:
        return True

    def language_to_service_language(self, language: Language) -> Optional[str]:
        """Convert pipecat language to Kokoro language code."""
        return language_to_kokoro_language(language)

    async def run_tts(self, text: str) -> AsyncGenerator[Frame, None]:
        """Generate speech from text using Kokoro in a streaming fashion.
        
        Args:
            text: The text to convert to speech
            
        Yields:
            Frames containing audio data and status information.
        """
        logger.debug(f"Generating TTS: [{text}]")
        try:
            await self.start_ttfb_metrics()
            yield TTSStartedFrame()

            # Use Kokoro's streaming mode. The create_stream method is assumed to return
            # an async generator that yields (samples, sample_rate) tuples, where samples is a numpy array.
            logger.info(f"Creating stream")
            stream = self._kokoro.create_stream(
                text,
                voice=self._voice_id,
                speed=self._settings["speed"],
                lang=self._settings["language"],
            )


            await self.start_tts_usage_metrics(text)
            started = False
            async for samples, sample_rate in stream:
                if not started:
                    started = True
                    logger.info(f"Started streaming")
                # Convert the float32 samples (assumed in the range [-1, 1]) to int16 PCM format
                samples_int16 = (samples * 32767).astype(np.int16)
                yield TTSAudioRawFrame(
                    audio=samples_int16.tobytes(),
                    sample_rate=sample_rate,
                    num_channels=1,
                )

            yield TTSStoppedFrame()

        except Exception as e:
            logger.error(f"{self} exception: {e}")
            yield ErrorFrame(f"Error generating audio: {str(e)}")