"""Pipecat-compatible Piper TTS service for air-gapped deployment.

This service runs Piper TTS directly via subprocess, avoiding the need
for an HTTP server in the air-gapped environment.
"""

from typing import AsyncGenerator

from pipecat.frames.frames import TTSAudioRawFrame, TTSStartedFrame, TTSStoppedFrame
from pipecat.services.tts_service import TTSService
from piper.voice import PiperVoice
import asyncio

class LocalPiperTTSService(TTSService):
    """
    Tiny wrapper so we don't need a separate HTTP server.
    Streams raw PCM from PiperVoice.synthesize_stream_raw().
    """
    def __init__(self, voice_id: str = "en_US-lessac-medium", use_cuda: bool = True, **kw):
        self.voice = PiperVoice.load(voice_id, cuda=use_cuda)           # Piper API :contentReference[oaicite:3]{index=3}
        super().__init__(sample_rate=self.voice.config.sample_rate, **kw)

    async def run_tts(self, text: str) -> AsyncGenerator:
        yield TTSStartedFrame()
        for chunk in self.voice.synthesize_stream_raw(text):            # Streams ~200 ms chunks
            yield TTSAudioRawFrame(chunk, self.sample_rate, 1)
            await asyncio.sleep(0)                                      # keep loop responsive
        yield TTSStoppedFrame()
