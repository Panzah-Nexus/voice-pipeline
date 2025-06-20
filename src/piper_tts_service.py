"""Pipecat-compatible Piper TTS service for air-gapped deployment.

This service runs Piper TTS directly via subprocess, avoiding the need
for an HTTP server in the air-gapped environment.
"""

import asyncio
import logging
import os
import tempfile
from typing import AsyncGenerator

import numpy as np
from scipy import signal

from pipecat.frames.frames import AudioRawFrame, Frame, ErrorFrame
# Pipecat v0.0.70+ moves base service classes to dedicated modules.
# Fallback to the old path for older versions to avoid breaking deployments.
try:
    from pipecat.services.tts_service import TTSService  # New path (≥0.0.70)
except ModuleNotFoundError:  # pragma: no cover
    from pipecat.services.ai_services import TTSService  # Back-compat for ≤0.0.69
from pipecat.transcriptions.language import Language

logger = logging.getLogger(__name__)


class PiperTTSService(TTSService):
    """Local Piper TTS service using subprocess."""
    
    def __init__(
        self,
        model: str = "en_US-lessac-medium",
        sample_rate: int = 16000,
        piper_path: str = "/usr/local/bin/piper",
        model_dir: str = "/models",
        **kwargs
    ):
        super().__init__(sample_rate=sample_rate, **kwargs)
        self._model = model
        self._piper_path = piper_path
        self._model_dir = model_dir
        self._piper_sample_rate = 22050  # Piper's native sample rate
        
        # Verify Piper binary exists
        if not os.path.exists(self._piper_path):
            raise FileNotFoundError(f"Piper binary not found at {self._piper_path}")
            
        # Verify model exists
        model_path = os.path.join(self._model_dir, f"{model}.onnx")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Piper model not found at {model_path}")
            
        logger.info(f"Initialized Piper TTS with model: {model}")

    def can_generate_metrics(self) -> bool:
        return False

    async def set_voice(self, voice: str):
        """Change the TTS voice/model."""
        self._model = voice
        logger.info(f"Switched to voice: {voice}")

    async def set_language(self, language: Language):
        """Set language (if supported by current model)."""
        # For now, we just log. In production, you'd map languages to models
        logger.info(f"Language set to: {language}")

    async def run_tts(self, text: str) -> AsyncGenerator[Frame, None]:
        """Generate speech from text using Piper."""
        try:
            logger.info(f"Generating speech for: {text[:50]}...")
            
            # Create temporary files for Piper I/O
            with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as text_file:
                text_file.write(text)
                text_file.flush()
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
                    wav_path = wav_file.name
                    
                    # Run Piper subprocess
                    model_path = os.path.join(self._model_dir, f"{self._model}.onnx")
                    cmd = [
                        self._piper_path,
                        "--model", model_path,
                        "--output_file", wav_path,
                        "--quiet"
                    ]
                    
                    # Run Piper
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdin=open(text_file.name, 'r'),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode != 0:
                        error_msg = f"Piper failed with code {process.returncode}: {stderr.decode()}"
                        logger.error(error_msg)
                        yield ErrorFrame(error=error_msg)
                        return
                    
                    # Read the generated WAV file
                    import wave
                    with wave.open(wav_path, 'rb') as wf:
                        # Get audio parameters
                        width = wf.getsampwidth()
                        framerate = wf.getframerate()
                        
                        # Read audio data
                        audio_data = wf.readframes(wf.getnframes())
                        
                    # Convert to numpy array
                    if width == 2:
                        audio_np = np.frombuffer(audio_data, dtype=np.int16)
                    else:
                        raise ValueError(f"Unsupported sample width: {width}")
                    
                    # Convert to float32 normalized to [-1, 1]
                    audio_float = audio_np.astype(np.float32) / 32768.0
                    
                    # Resample if necessary
                    if framerate != self._sample_rate:
                        # Calculate resampling ratio
                        resample_ratio = self._sample_rate / framerate
                        
                        # Resample using scipy
                        resampled_length = int(len(audio_float) * resample_ratio)
                        audio_float = signal.resample(audio_float, resampled_length)
                        
                        logger.info(f"Resampled audio from {framerate}Hz to {self._sample_rate}Hz")
                    
                    # Chunk audio for streaming
                    chunk_size = int(self._sample_rate * 0.1)  # 100ms chunks
                    
                    for i in range(0, len(audio_float), chunk_size):
                        chunk = audio_float[i:i + chunk_size]
                        if len(chunk) > 0:
                            # Convert back to int16 for output
                            chunk_int16 = (chunk * 32768).astype(np.int16)
                            yield AudioRawFrame(
                                audio=chunk_int16.tobytes(),
                                sample_rate=self._sample_rate,
                                num_channels=1
                            )
                    
                    # Clean up temporary files
                    os.unlink(text_file.name)
                    os.unlink(wav_path)
                    
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            yield ErrorFrame(error=str(e))

