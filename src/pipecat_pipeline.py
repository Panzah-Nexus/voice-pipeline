"""
Air-gapped Pipecat bot with RTVI compatibility for Runpod deployment
====================================================================
This module provides the run_bot function that works with
the standard Pipecat web clients, while running completely air-gapped models:

* **UltravoxSTTService** – combined STT + LLM (local)
* **PiperTTSService**   – offline TTS (local)

All AI processing happens on Runpod GPU infrastructure without external API calls.
"""

import os
import sys

from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

from pipecat.services.ultravox.stt import UltravoxSTTService

# Import PiperTTSService - handle both direct run and import from main.py
try:
    from src.piper_tts_service import PiperTTSService
except ImportError:
    from piper_tts_service import PiperTTSService

# ---------------------------------------------------------------------------
# Initialisation & configuration
# ---------------------------------------------------------------------------
# Configure loguru logger
logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

# Configuration from environment variables
HF_TOKEN: str = os.getenv("HF_TOKEN", "")
PIPER_MODEL: str = os.getenv("PIPER_MODEL", "en_US-lessac-medium")
SAMPLE_RATE: int = 16_000

SYSTEM_INSTRUCTION: str = (
    "You are an AI assistant running entirely on local infrastructure. "
    "Greet the user warmly and keep responses concise – no more than two "
    "sentences. Avoid special characters so the TTS remains clear."
)

# ---------------------------------------------------------------------------
# Model services – loaded once at startup
# ---------------------------------------------------------------------------
logger.info("Loading UltravoxSTTService... this can take a while on first run.")
try:
    ULTRAVOX = UltravoxSTTService(
        model_name="fixie-ai/ultravox-v0_5-llama-3_1-8b",
        hf_token=HF_TOKEN,
        temperature=0.6,
        max_tokens=150,
    )
    logger.info("Ultravox model initialized successfully!")
except Exception as e:
    logger.error(f"Could not initialise Ultravox. Check HF_TOKEN and GPU: {e}")
    ULTRAVOX = None  # we fail later with a clearer message


async def run_bot(websocket_client):
    """Entry-point used by Pipecat example clients."""
    
    if ULTRAVOX is None:
        raise RuntimeError(
            "Ultravox failed to initialise at startup – server cannot serve requests."
        )

    # 1️⃣ WebSocket transport – identical params to reference example
    ws_transport = FastAPIWebsocketTransport(
        websocket=websocket_client,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_analyzer=SileroVADAnalyzer(),
            serializer=ProtobufFrameSerializer(),
        ),
    )

    # 2️⃣ Local TTS (Piper)
    tts = PiperTTSService(model=PIPER_MODEL, sample_rate=SAMPLE_RATE)

    # 3️⃣ RTVI signalling layer – required for Pipecat web client
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # 4️⃣ Assemble minimalist pipeline: User audio -> Ultravox -> Piper -> output
    pipeline = Pipeline(
        [
            ws_transport.input(),
            rtvi,
            ULTRAVOX,  # Combined STT+LLM
            tts,       # TTS
            ws_transport.output(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
        observers=[RTVIObserver(rtvi)],
    )

    # ---------- Event handlers ----------
    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        logger.info("Pipecat client ready.")
        await rtvi.set_bot_ready()
        # Send an initial greeting via TTS once pipeline ready
        await tts.say("Hello! I'm your AI assistant. How can I help you today?")

    @ws_transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Pipecat Client connected")

    @ws_transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Pipecat Client disconnected")
        await task.cancel()

    # ---------- Runner ----------
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
