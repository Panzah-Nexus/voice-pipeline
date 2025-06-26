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

import onnxruntime as ort
import os

privders = ort.get_available_providers()
logger.info("Available providers:", privders)  # Make sure CUDAExecutionProvider is listed
logger.info(f'Is CUDA available: {"CUDAExecutionProvider" in privders}')

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
        logger.info(f"Initializing Kokoro TTS service with model_path: {model_path} and voices_path: {voices_path}")
        
        # Initialise Kokoro session – TensorRT > CUDA > CPU
        providers = ort.get_available_providers()
        logger.info(f"Available ONNX Runtime providers: {providers}")

        provider_configs = []
        use_gpu = False

        # Prioritize TensorRT for best performance
        if "TensorrtExecutionProvider" in providers:
            logger.info("Configuring TensorrtExecutionProvider")
            # Create cache directory if it doesn't exist
            cache_path = "/tmp/kokoro_tensorrt_cache"
            os.makedirs(cache_path, exist_ok=True)
            logger.info(f"TensorRT engine cache path: {cache_path}")
            provider_configs = [
                (
                    'TensorrtExecutionProvider', {
                        'trt_fp16_enable': True,
                        'trt_engine_cache_enable': True,
                        'trt_engine_cache_path': cache_path,
                    }
                ),
                'CUDAExecutionProvider',  # Fallback for ops not supported by TRT
            ]
            use_gpu = True
        elif "CUDAExecutionProvider" in providers:
            logger.info("TensorRT not available, configuring CUDAExecutionProvider")
            provider_configs = [
                (
                    "CUDAExecutionProvider",
                    {"cudnn_conv_algo_search": "EXHAUSTIVE"},
                ),
                "CPUExecutionProvider",
            ]
            use_gpu = True
        else:
            logger.info("GPU providers not available, using CPUExecutionProvider")
            provider_configs = ["CPUExecutionProvider"]

        if use_gpu:
            # Check for older Kokoro version that needs a pre-made session
            if hasattr(Kokoro, "from_session"):
                logger.info("Using Kokoro.from_session factory")
                sess = ort.InferenceSession(model_path, providers=provider_configs)
                self._kokoro = Kokoro.from_session(sess, voices_path)
            else:
                # Newer Kokoro versions take providers in constructor
                logger.info("Passing providers to Kokoro constructor")
                self._kokoro = Kokoro(model_path, voices_path, providers=provider_configs)
        else:
            self._kokoro = Kokoro(model_path, voices_path)
            
        logger.info(f"Kokoro initialized")
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