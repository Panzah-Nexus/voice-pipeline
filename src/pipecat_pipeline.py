"""
Air-gapped voice pipeline with enhanced Pipecat components
Ultravox (STT + LLM) ▶ Piper (TTS)
Everything runs locally on a Cerebrium A10.
"""

import os
import aiohttp
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
from pipecat.services.stt.ultravox import UltravoxSTTService          # STT+LLM :contentReference[oaicite:5]{index=5}
from .piper_tts_service import LocalPiperTTSService

ULTRAVOX_MODEL = os.getenv("ULTRAVOX_MODEL", "ultravox-v0_4_1-llama-3_1-8b")
PIPER_VOICE   = os.getenv("PIPER_VOICE",   "en_US-lessac-medium")

def build_pipeline(websocket):
    """Returns (pipeline, runner) for each WebSocket session."""
    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),                          # built-in VAD :contentReference[oaicite:6]{index=6}
        ),
    )

    stt  = UltravoxSTTService(model=ULTRAVOX_MODEL)                    # ∴ no STT→LLM latency :contentReference[oaicite:7]{index=7}
    tts  = LocalPiperTTSService(voice_id=PIPER_VOICE)

    return Pipeline([transport.input(), stt, tts, transport.output()])
