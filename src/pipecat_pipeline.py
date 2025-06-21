"""
Air-gapped Pipecat bot with RTVI compatibility for Runpod deployment
====================================================================
This module wires together:

* **UltravoxSTTService** – combined STT + LLM (local)
* **KokoroTTSService**   – offline TTS (local)

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

# Kokoro TTS service (preferred over Piper)
from src.kokoro_tts_service import KokoroTTSService

# ---------------------------------------------------------------------------
# Initialisation & configuration
# ---------------------------------------------------------------------------
# Configure loguru logger (id=0 might have been removed by upstream Pipecat)
try:
    logger.remove(0)
except ValueError:
    # Either already removed or replaced by another module – proceed silently
    pass

logger.add(sys.stderr, level="DEBUG")

# Configuration from environment variables
HF_TOKEN: str = os.getenv("HF_TOKEN", "")
KOKORO_MODEL_PATH: str = os.getenv("KOKORO_MODEL_PATH", "/models/kokoro/model_fp16.onnx")
KOKORO_VOICES_PATH: str = os.getenv("KOKORO_VOICES_PATH", "/models/kokoro/voices-v1.0.bin")
KOKORO_VOICE_ID: str = os.getenv("KOKORO_VOICE_ID", "af_sarah")
SAMPLE_RATE: int = int(os.getenv("KOKORO_SAMPLE_RATE", "24000"))

SYSTEM_INSTRUCTION: str = (
    "You are an AI assistant running entirely on local infrastructure. "
    "When the user first connects, greet them warmly with 'Hello! I'm your AI assistant. How can I help you today?' "
    "Keep all responses concise – no more than two sentences. Avoid special characters so the TTS remains clear."
)

# ---------------------------------------------------------------------------
# Model services – loaded once at startup
# ---------------------------------------------------------------------------
_ultravox_singleton = None  # Lazily initialised model backend


def _get_ultravox():
    """Return a *fresh* UltravoxSTTService for a new connection.

    The heavy model weights are cached by the underlying library after the
    first load, so instantiating a new service for each WebSocket session is
    cheap while avoiding re-using the same FrameProcessor across pipelines.
    """

    global _ultravox_singleton

    if _ultravox_singleton is None:
        logger.info("Loading UltravoxSTTService... this can take a while on first run.")
        try:
            _ultravox_singleton = UltravoxSTTService(
                model_name="fixie-ai/ultravox-v0_5-llama-3_1-8b",
                hf_token=HF_TOKEN,
                temperature=0.6,
                max_tokens=150,
                system_instruction=SYSTEM_INSTRUCTION,
            )
            logger.info("Ultravox model initialized successfully!")
        except Exception as e:
            logger.error(f"Could not initialise Ultravox. Check HF_TOKEN and GPU: {e}")
            raise

    # Create a *new* service instance that shares weights (cheap)
    # Some versions expose `.clone()`; fallback to re-instantiation.
    try:
        return _ultravox_singleton.clone()
    except AttributeError:
        return UltravoxSTTService(
            model_name=_ultravox_singleton.model_name if hasattr(_ultravox_singleton, "model_name") else "fixie-ai/ultravox-v0_5-llama-3_1-8b",
            hf_token=HF_TOKEN,
            temperature=0.6,
            max_tokens=150,
            system_instruction=SYSTEM_INSTRUCTION,
        )


async def run_bot(websocket_client):
    """Entry-point used by Pipecat example clients."""
    
    # Create a *connection-local* Ultravox service to avoid re-use across pipelines
    ULTRAVOX = _get_ultravox()

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

    # 2️⃣ Local TTS (Kokoro)
    tts = KokoroTTSService(
        model_path=KOKORO_MODEL_PATH,
        voices_path=KOKORO_VOICES_PATH,
        voice_id=KOKORO_VOICE_ID,
        sample_rate=SAMPLE_RATE,
    )

    # 3️⃣ RTVI signalling layer – required for Pipecat web client
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # 4️⃣ Assemble minimalist pipeline: User audio -> Ultravox -> Kokoro -> output
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
        # Pipeline is ready - initial greeting will happen when user speaks

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
