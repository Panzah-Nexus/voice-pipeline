"""
Air-gapped Pipecat bot with RTVI compatibility for Runpod deployment
====================================================================
This module wires together:

* **UltravoxWithContextService** – combined STT + LLM with conversation memory
* **KokoroTTSService**   – offline TTS (local)

All AI processing happens on Runpod GPU infrastructure without external API calls.
Now with full conversation context and memory!
"""

import os
import sys
import asyncio

from loguru import logger

# --- VAD --------------------------------------------------------------
# Tune Silero so it fires sooner and streams shorter chunks
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

FAST_VAD = SileroVADAnalyzer(
    params=VADParams(
        min_silence_ms=100,      # Even faster - was 200ms
        speech_pad_ms=50,        # Minimal padding - was 120ms
        window_ms=160,           # Keep same
    )
)

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

# Import our context-aware Ultravox service
from src.ultravox_with_context import UltravoxWithContextService, ContextManager

# Kokoro TTS service (preferred over Piper)
from src.kokoro_tts_service import KokoroTTSService

# Import context management
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

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
KOKORO_VOICE_ID: str = os.getenv("KOKORO_VOICE_ID", "af_bella")
SAMPLE_RATE: int = int(os.getenv("KOKORO_SAMPLE_RATE", "24000"))

# ---------------------------------------------------------------------------
# Initialize Ultravox processor once at module level with context awareness
# ---------------------------------------------------------------------------
logger.info("Loading UltravoxWithContextService... this can take a while on first run.")

# Create a context-aware system instruction that encourages building on previous conversation
SYSTEM_INSTRUCTION = """You are a helpful AI assistant with full memory of our conversation. 

Key behaviors:
1. Remember and reference previous parts of our conversation naturally
2. Build on what we've discussed before without repeating yourself
3. If the user refers to something we discussed earlier, acknowledge it
4. Keep responses concise (1-2 sentences) unless more detail is needed
5. Maintain conversational continuity and flow
6. If context seems missing or unclear, politely ask for clarification

You have access to our full conversation history, so use it to provide contextual, relevant responses."""

ultravox_processor = UltravoxWithContextService(
    model_name="fixie-ai/ultravox-v0_5-llama-3_1-8b",
    hf_token=HF_TOKEN,
    temperature=0.3,  # Lower temperature = more consistent responses
    max_tokens=50,    # Slightly more tokens for contextual responses
    system_instruction=SYSTEM_INSTRUCTION,
)

# Create context manager for trimming conversation history
context_manager = ContextManager(max_messages=20)  # Keep last 20 messages

logger.info("Ultravox model with context initialized successfully!")


async def run_bot(websocket_client):
    """Entry-point used by Pipecat example clients."""
    
    logger.info("Starting bot with conversation memory")

    # 1️⃣ WebSocket transport – identical params to reference example
    ws_transport = FastAPIWebsocketTransport(
        websocket=websocket_client,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=True,
            vad_analyzer=FAST_VAD,
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

    # 4️⃣ Pipeline with context-aware Ultravox
    pipeline = Pipeline(
        [
            ws_transport.input(),
            rtvi,           
            ultravox_processor,    # Context-aware STT+LLM
            tts,
            ws_transport.output(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
            allow_interruptions=True,
            # Enable immediate interruption
            report_only_initial_ttfb=False,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    # ---------- Event handlers ----------
    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        logger.info("Pipecat client ready with conversation memory.")
        await rtvi.set_bot_ready()
        # The bot now maintains context across the entire conversation

    @ws_transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected - conversation memory active")
        # Optionally reset context for new connections
        # ultravox_processor.set_context(OpenAILLMContext())

    @ws_transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()
        
    # ---------- Interruption tracking ----------
    @ws_transport.event_handler("on_interruption_start")
    async def on_interruption_start(transport):
        logger.info("🔴 INTERRUPTION: User started speaking - stopping TTS")
        
    @ws_transport.event_handler("on_interruption_end")  
    async def on_interruption_end(transport):
        logger.info("🟢 INTERRUPTION: User stopped speaking - ready for response")
        
    # Track speech events
    @ws_transport.event_handler("on_user_started_speaking")
    async def on_user_started_speaking(transport):
        logger.info("👤 USER: Started speaking")
        
    @ws_transport.event_handler("on_user_stopped_speaking")
    async def on_user_stopped_speaking(transport):
        logger.info("👤 USER: Stopped speaking")
        
    @ws_transport.event_handler("on_bot_started_speaking")
    async def on_bot_started_speaking(transport):
        logger.info("🤖 BOT: Started speaking")
        
    @ws_transport.event_handler("on_bot_stopped_speaking")
    async def on_bot_stopped_speaking(transport):
        logger.info("🤖 BOT: Stopped speaking")

    # ---------- Context monitoring ----------
    async def monitor_context():
        """Monitor and log conversation context periodically"""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                context = ultravox_processor.get_context()
                messages = context.get_messages()
                logger.info(f"📝 CONTEXT: {len(messages)} messages in conversation")
                
                # Optionally trim context if it gets too large
                if len(messages) > 25:
                    trimmed_context = context_manager.trim_context(context)
                    ultravox_processor.set_context(trimmed_context)
                    logger.info(f"✂️ Trimmed context to {len(trimmed_context.get_messages())} messages")
                    
            except Exception as e:
                logger.debug(f"Context monitoring error: {e}")
                break

    # ---------- Metrics monitoring ----------
    async def log_metrics():
        """Log performance metrics every 5 seconds"""
        while True:
            try:
                await asyncio.sleep(5)  # More frequent - was 10 seconds
                # Get metrics from the task
                if hasattr(task, '_pipeline') and hasattr(task._pipeline, '_processors'):
                    logger.info("📊 === PERFORMANCE METRICS ===")
                    for processor in task._pipeline._processors:
                        if hasattr(processor, '_metrics') and processor._metrics:
                            metrics = processor._metrics
                            name = processor.__class__.__name__
                            if hasattr(metrics, 'ttfb_metrics') and metrics.ttfb_metrics:
                                avg_ttfb = sum(metrics.ttfb_metrics) / len(metrics.ttfb_metrics)
                                logger.info(f"⚡ {name} - Avg TTFB: {avg_ttfb:.3f}s")
                            if hasattr(metrics, 'processing_metrics') and metrics.processing_metrics:
                                avg_processing = sum(metrics.processing_metrics) / len(metrics.processing_metrics)
                                logger.info(f"🔄 {name} - Avg Processing: {avg_processing:.3f}s")
                    logger.info("📊 ========================")
            except Exception as e:
                logger.debug(f"Metrics logging error: {e}")
                break
    
    # Start background tasks
    asyncio.create_task(log_metrics())
    asyncio.create_task(monitor_context())

    # ---------- Runner ----------
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)