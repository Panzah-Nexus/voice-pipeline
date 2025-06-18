"""
Air-gapped voice pipeline with enhanced Pipecat components
Ultravox (STT + LLM) ▶ Piper (TTS)
Everything runs locally on a Cerebrium A10.
"""
from __future__ import annotations
import asyncio, logging, os
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.responses import PlainTextResponse

# ── logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("voice-srv")

# ── env helpers ────────────────────────────────────────────────────────────
def get_secret(key: str) -> Optional[str]:
    try:
        from cerebrium import get_secret as _cs
        if val := _cs(key):
            log.info("✅ secret %s (cerebrium)", key)
            return val
    except Exception:
        ...
    if val := os.getenv(key):
        log.info("✅ secret %s (env)", key)
        return val
    log.warning("❌ secret %s not found", key)
    return None

# ── Pipecat imports ────────────────────────────────────────────────────────
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner  import PipelineRunner
from pipecat.pipeline.task    import PipelineParams, PipelineTask

# Transport and serializers
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketTransport, FastAPIWebsocketParams,
)
from pipecat.serializers.protobuf import ProtobufFrameSerializer

# Audio processing
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

# Frame types and processors
from pipecat.frames.frames import ErrorFrame, StartFrame, EndFrame
from pipecat.processors.frame_processor import FrameDirection

# Context aggregators for conversation management
from pipecat.processors.aggregators.openai_llm_context import (
    OpenAILLMContext,
    OpenAILLMContextFrame,
)

# Frame loggers for debugging
from pipecat.processors.logger import FrameLogger

# Metrics collection
from pipecat.processors.metrics.frame_processor_metrics import FrameProcessorMetrics

# Audio filters (optional noise reduction)
try:
    from pipecat.audio.filters.noisereduce_filter import NoiseReduceFilter
except ImportError:
    NoiseReduceFilter = None

# Services
try:
    from pipecat.services.ultravox.stt import UltravoxSTTService
except Exception as exc:
    UltravoxSTTService = None
    log.error("Ultravox import failed: %s", exc)

# TTS Service Options
# Option 1: Custom Piper TTS (runs Piper directly, no HTTP server needed)
try:
    from .piper_tts_service import PiperTTSService         # when packaged
except Exception:
    from piper_tts_service import PiperTTSService          # when run locally

# Option 2: Official Pipecat Piper TTS (requires HTTP server)
# Uncomment to use: from pipecat.services.piper.tts import PiperTTSService as OfficialPiperTTS

# ── FastAPI app ────────────────────────────────────────────────────────────
app          = FastAPI(title="Air-gapped Voice Server")
stt_service  = None
tts_service  = None
ready_flag   = False          # exposed at /ready

# ── optional VAD (can be disabled via env) ────────────────────────────────
def build_vad() -> SileroVADAnalyzer:
    return SileroVADAnalyzer(params=VADParams(
        confidence = 0.3,
        start_secs = 0.05,
        stop_secs  = 1.2,
        min_volume = 0.10,
    ))

# ── context aggregator for conversation management ─────────────────────────
def create_context_aggregator(initial_messages=None):
    """Create context aggregator for managing conversation state"""
    context = OpenAILLMContext(
        messages=initial_messages or [
            {
                "role": "system",
                "content": "You are a helpful voice assistant. Keep responses concise and conversational."
            }
        ]
    )
    context_aggregator = context.create_context_aggregator()
    return context_aggregator

# ── startup ────────────────────────────────────────────────────────────────
load_dotenv()          # dev-time convenience

@app.on_event("startup")
async def _startup() -> None:
    global stt_service, tts_service, ready_flag

    hf = get_secret("HF_TOKEN")
    if not hf or not UltravoxSTTService:
        log.error("Ultravox not configured – pipeline disabled")
        return

    # Initialize STT service (Ultravox includes LLM)
    stt_service = UltravoxSTTService(
        model_name="fixie-ai/ultravox-v0_5-llama-3_1-8b",
        hf_token=hf,
        temperature=0.5,
        max_tokens=150,
    )
    log.info("✅ Ultravox initialised")

    # Initialize TTS service
    voice = get_secret("PIPER_MODEL") or "en_US-lessac-medium"
    tts_service = PiperTTSService(model_name=voice, sample_rate=16_000)
    log.info("✅ Piper initialised (%s)", voice)

    # first real request will compile the CUDA graph, so mark ready now
    ready_flag = True
    log.info("🏁 pipeline ready")

# ── health probes ──────────────────────────────────────────────────────────
@app.get("/health")
async def _health(): return PlainTextResponse("OK")

@app.get("/ready")
async def _ready():
    return PlainTextResponse("OK" if ready_flag else "loading",
                             status_code=200 if ready_flag else 503)

# ── websocket endpoint ────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    if not ready_flag:
        await ws.close(code=1013, reason="model loading")
        return
    await ws.accept()
    log.info("🌐 client connected")

    # Create transport with built-in VAD if enabled
    enable_vad = os.getenv("ENABLE_VAD", "false").lower() == "true"
    
    # Check if client wants raw audio (no protobuf)
    # This can be determined by WebSocket subprotocol or headers
    use_protobuf = os.getenv("USE_PROTOBUF", "true").lower() == "true"
    
    transport_params = FastAPIWebsocketParams(
        audio_in_enabled = True,
        audio_out_enabled= True,
        vad_enabled      = enable_vad,
        vad_analyzer     = build_vad() if enable_vad else None,
    )
    
    # Only use protobuf serializer if enabled
    if use_protobuf:
        transport_params.serializer = ProtobufFrameSerializer()
    
    transport = FastAPIWebsocketTransport(
        websocket=ws,
        params=transport_params,
    )

    # Create context aggregator for conversation management
    context_aggregator = create_context_aggregator()

    # Build pipeline with enhanced components
    pipeline_components = []
    
    # Input transport
    pipeline_components.append(transport.input())
    
    # Optional noise reduction filter
    if NoiseReduceFilter and os.getenv("ENABLE_NOISE_REDUCTION", "false").lower() == "true":
        pipeline_components.append(NoiseReduceFilter())
        log.info("✅ Noise reduction enabled")
    
    # Optional frame logger for debugging
    if os.getenv("DEBUG_FRAMES", "false").lower() == "true":
        pipeline_components.append(FrameLogger("input"))
    
    # Context management for user input
    pipeline_components.append(context_aggregator.user())
    
    # STT service (Ultravox handles both STT and LLM)
    pipeline_components.append(stt_service)
    
    # Context management for assistant output
    pipeline_components.append(context_aggregator.assistant())
    
    # Optional metrics collection
    if os.getenv("ENABLE_METRICS", "false").lower() == "true":
        pipeline_components.append(FrameProcessorMetrics(name="tts_metrics"))
    
    # TTS service
    pipeline_components.append(tts_service)
    
    # Optional frame logger for debugging output
    if os.getenv("DEBUG_FRAMES", "false").lower() == "true":
        pipeline_components.append(FrameLogger("output"))
    
    # Output transport
    pipeline_components.append(transport.output())

    # Create pipeline
    pipeline = Pipeline(pipeline_components)

    # Pipeline parameters with enhanced options
    pipeline_params = PipelineParams(
        allow_interruptions=True,
        enable_metrics=os.getenv("ENABLE_METRICS", "false").lower() == "true",
        enable_usage_metrics=os.getenv("ENABLE_USAGE_METRICS", "false").lower() == "true",
        send_initial_empty_metrics=False,
        report_only_initial_ttfb=True,
    )

    try:
        await PipelineRunner().run(
            PipelineTask(pipeline, params=pipeline_params)
        )
    except Exception as exc:
        log.error("pipeline error: %s", exc)
        # bubble an ErrorFrame so the websocket stays open
        await transport.output().push_frame(ErrorFrame(error=str(exc)), FrameDirection.DOWNSTREAM)
    finally:
        log.info("🌐 client disconnected")

# ── local dev entry-point ─────────────────────────────────────────────────
async def _dev():
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info" if os.getenv("DEBUG", "false").lower() == "false" else "debug"
    )
    await uvicorn.Server(config).serve()

if __name__ == "__main__":
    asyncio.run(_dev())
