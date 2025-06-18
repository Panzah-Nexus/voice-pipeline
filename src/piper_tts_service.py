"""Pipecat-compatible Piper TTS service for air-gapped deployment.

This service runs Piper TTS directly via subprocess, avoiding the need
for an HTTP server in the air-gapped environment.
"""

import os
import asyncio
import subprocess
import tempfile
import logging
from typing import Optional, AsyncIterator
from pathlib import Path
import requests
import numpy as np

from pipecat.frames.frames import AudioRawFrame, Frame, TTSStartedFrame, TTSStoppedFrame
try:
    from pipecat.services.tts_service import TTSService
except ImportError:
    # Fallback to old import for compatibility
    from pipecat.services.ai_services import TTSService
try:
    from pipecat.audio.utils import resample_audio
except ImportError:
    # Fallback resample implementation using scipy
    from scipy import signal
    
    def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio from orig_sr to target_sr."""
        if orig_sr == target_sr:
            return audio
        # Calculate the resampling ratio
        num_samples = int(len(audio) * target_sr / orig_sr)
        # Use scipy's resample function
        return signal.resample(audio, num_samples).astype(np.int16)

logger = logging.getLogger(__name__)

class PiperTTSService(TTSService):
    """Direct Piper TTS service for Pipecat (no HTTP server required)."""
    
    def __init__(
        self,
        *,
        model_name: Optional[str] = None,
        sample_rate: int = 16000,
        **kwargs
    ):
        """Initialize Piper TTS service.
        
        Args:
            model_name: Piper model name (e.g., 'en_US-lessac-medium')
            sample_rate: Output sample rate (will resample from Piper's 22050 Hz)
        """
        super().__init__(sample_rate=sample_rate, **kwargs)
        
        self._model_name = model_name or os.environ.get("PIPER_MODEL", "en_US-lessac-medium")
        self._piper_sample_rate = 22050  # Piper's native output rate
        
        # Model paths
        self._setup_model_paths()
        
        logger.info(f"✅ Initialized PiperTTSService with model: {self._model_name}")
    
    def _setup_model_paths(self):
        """Setup model paths, downloading if necessary."""
        # Check for pre-downloaded models (Cerebrium deployment)
        pre_downloaded_dir = Path("/models")
        if pre_downloaded_dir.exists():
            self.models_dir = pre_downloaded_dir
            logger.info(f"✅ Using pre-downloaded models from {self.models_dir}")
        else:
            # Fall back to user directory
            self.models_dir = Path.home() / ".local" / "share" / "piper" / "models"
            self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Get model paths
        self.model_path = self._ensure_model_exists()
    
    def _ensure_model_exists(self) -> Path:
        """Ensure model files exist, downloading if necessary."""
        model_file = self.models_dir / f"{self._model_name}.onnx"
        config_file = self.models_dir / f"{self._model_name}.onnx.json"
        
        if not (model_file.exists() and config_file.exists()):
            logger.info(f"📥 Model {self._model_name} not found, downloading...")
            self._download_model()
        
        return model_file
    
    def _download_model(self):
        """Download Piper model from Hugging Face."""
        base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
        
        # Parse model name (e.g., en_US-lessac-medium)
        parts = self._model_name.split("-")
        if len(parts) < 2:
            raise ValueError(f"Invalid model name format: {self._model_name}")
        
        lang = parts[0]  # e.g., en_US
        voice_quality = "-".join(parts[1:])  # e.g., lessac-medium
        voice = voice_quality.rsplit("-", 1)[0]  # e.g., lessac
        quality = voice_quality.rsplit("-", 1)[1]  # e.g., medium
        
        # Download both model and config files
        for suffix in [".onnx", ".onnx.json"]:
            filename = f"{self._model_name}{suffix}"
            url = f"{base_url}/{lang[:2]}/{lang}/{voice}/{quality}/{filename}"
            path = self.models_dir / filename
            
            try:
                logger.info(f"📥 Downloading {url}")
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                with open(path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"✅ Downloaded {filename}")
            except Exception as e:
                logger.error(f"❌ Failed to download {url}: {e}")
                raise
    
    async def run_tts(self, text: str) -> AsyncIterator[Frame]:
        """Generate TTS audio frames from text."""
        try:
            logger.debug(f"🔊 Generating TTS for: {text[:50]}...")
            
            # Yield TTS started frame
            yield TTSStartedFrame()
            
            # Generate audio
            audio_data = await self._synthesize(text)
            
            if audio_data:
                # Extract raw audio from WAV
                raw_audio = audio_data[44:] if audio_data[:4] == b'RIFF' else audio_data
                
                # Resample if needed
                if self._piper_sample_rate != self.sample_rate:
                    samples = np.frombuffer(raw_audio, dtype=np.int16)
                    resampled = resample_audio(
                        samples,
                        self._piper_sample_rate,
                        self.sample_rate
                    )
                    raw_audio = resampled.astype(np.int16).tobytes()
                
                # Yield audio frame
                yield AudioRawFrame(
                    audio=raw_audio,
                    sample_rate=self.sample_rate,
                    num_channels=1
                )
            
            # Yield TTS stopped frame
            yield TTSStoppedFrame()
            
            logger.debug("✅ TTS generation complete")
            
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
            yield TTSStoppedFrame()
    
    async def _synthesize(self, text: str) -> bytes:
        """Synthesize speech using Piper subprocess."""
        try:
            # Create temporary file for output
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Run Piper
            cmd = [
                "piper",
                "--model", str(self.model_path),
                "--output_file", temp_path,
                "--sentence-silence", "0.2",
            ]
            
            # Run synthesis
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate(input=text.encode())
            
            if process.returncode != 0:
                raise RuntimeError(f"Piper synthesis failed: {stderr.decode()}")
            
            # Read generated audio
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            # Clean up
            os.unlink(temp_path)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            raise
    
    def can_generate_metrics(self) -> bool:
        """Indicate this service can generate metrics."""
        return True 