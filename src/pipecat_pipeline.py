"""
Air-gapped Pipecat bot with RTVI compatibility for Local deployment
===================================================================
This module wires together a proper cascaded pipeline:

* **WhisperSTTService** – local offline STT with CUDA support
* **OLLamaLLMService**   – local LLM with full conversation memory
* **KokoroTTSService**   – offline TTS (existing, working great)

All AI processing happens locally with no external dependencies.
"""

import os
import sys

from loguru import logger

# --- VAD --------------------------------------------------------------
# Aggressive VAD for fast interruption detection
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

FAST_VAD = SileroVADAnalyzer(
    params=VADParams(
        min_silence_ms=150,      # Fast interruption detection
        speech_pad_ms=100,       # Minimal padding
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

# Local STT (Whisper)
from pipecat.services.whisper.stt import WhisperSTTService, Model as WhisperModel

# Local LLM (Ollama) with conversation context
from pipecat.services.ollama.llm import OLLamaLLMService
from pipecat.processors.aggregators.openai_llm_context import (
    OpenAILLMContext,
)

# Keep existing TTS service
from src.kokoro_tts_service import KokoroTTSService

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Configure loguru logger
try:
    logger.remove(0)
except ValueError:
    pass

logger.add(sys.stderr, level="DEBUG")

# Environment variables for TTS
KOKORO_MODEL_PATH: str = os.getenv("KOKORO_MODEL_PATH", "/models/kokoro/model_fp16.onnx") 
KOKORO_VOICES_PATH: str = os.getenv("KOKORO_VOICES_PATH", "/models/kokoro/voices-v1.0.bin")
KOKORO_VOICE_ID: str = os.getenv("KOKORO_VOICE_ID", "af_bella")
SAMPLE_RATE: int = int(os.getenv("KOKORO_SAMPLE_RATE", "24000"))

# Ollama configuration  
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")  # Fast, good quality
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

# Strong English-only system prompt with conversation instructions
SYSTEM_PROMPT = """You are a helpful AI assistant having a real-time voice conversation.

CRITICAL INSTRUCTIONS:
1. ALWAYS respond in English only - never Chinese, Japanese, Korean, or other languages
2. If user speaks another language, understand it but respond in English
3. Keep responses conversational and under 2 sentences for voice interaction
4. Be natural, helpful, and engaging
5. Remember our conversation context
6. If you detect non-English generation starting, immediately switch to English

You are knowledgeable and can help with various topics while maintaining engaging conversation."""

# ---------------------------------------------------------------------------
# Initialize services at module level for faster startup
# ---------------------------------------------------------------------------

logger.info("🔧 Initializing local cascaded pipeline components...")

# 1. Local STT (Whisper) - fast model with CUDA support
logger.info("📝 Loading WhisperSTTService...")
stt_service = WhisperSTTService(
    model=WhisperModel.DISTIL_MEDIUM_EN,  # Fast English model ~400MB
    device="cuda" if os.getenv("CUDA_AVAILABLE", "true").lower() == "true" else "auto",
    no_speech_prob=0.4,  # Filter out non-speech
)
logger.info("✅ Whisper STT initialized successfully!")

# 2. Local LLM (Ollama) with proper conversation context
logger.info("🧠 Loading Ollama LLM service...")
llm_service = OLLamaLLMService(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    params=OLLamaLLMService.InputParams(
        temperature=0.7,          # Balanced creativity
        max_tokens=150,           # Reasonable length for voice
        frequency_penalty=0.3,    # Reduce repetition
        presence_penalty=0.3,     # Encourage variety
    )
)
logger.info("✅ Ollama LLM initialized successfully!")

# 3. Conversation context with system prompt
conversation_context = OpenAILLMContext(
    messages=[],
    system=SYSTEM_PROMPT,
    tools=[],  # Ready for function calling later!
)

# 4. Context aggregators for proper conversation flow
context_aggregators = OLLamaLLMService.create_context_aggregator(
    conversation_context,
    assistant_expect_stripped_words=True  # Better for voice responses
)

logger.info("🎯 All local pipeline components ready!")

async def run_bot(websocket_client):
    """Entry-point for the local cascaded voice bot."""
    
    logger.info("🚀 Starting local cascaded voice pipeline...")

    # 1️⃣ WebSocket transport with fast VAD
    ws_transport = FastAPIWebsocketTransport(
        websocket=websocket_client,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_analyzer=FAST_VAD,
            serializer=ProtobufFrameSerializer(),
        ),
    )

    # 2️⃣ Local TTS (Kokoro) - keep what works!
    tts = KokoroTTSService(
        model_path=KOKORO_MODEL_PATH,
        voices_path=KOKORO_VOICES_PATH,
        voice_id=KOKORO_VOICE_ID,
        sample_rate=SAMPLE_RATE,
    )

    # 3️⃣ RTVI signalling layer
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # 4️⃣ PERFECT CASCADED PIPELINE 🎯
    # Input → STT → User_Aggregator → LLM → Assistant_Aggregator → TTS → Output
    pipeline = Pipeline([
        ws_transport.input(),           # Audio input
        rtvi,                          # RTVI compatibility  
        stt_service,                   # 🎙️  Whisper STT (local)
        context_aggregators.user(),    # 👤  User message handling
        llm_service,                   # 🧠  Ollama LLM (local)  
        context_aggregators.assistant(), # 🤖  Assistant message handling
        tts,                           # 🗣️  Kokoro TTS (local)
        ws_transport.output(),         # Audio output
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
            allow_interruptions=True,  # Smooth interruptions!
            report_only_initial_ttfb=False,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    # ---------- Event handlers ----------
    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        logger.info("✅ Client ready - local cascaded pipeline active!")
        await rtvi.set_bot_ready()

    @ws_transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("🔗 Client connected to local pipeline")

    @ws_transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("👋 Client disconnected")
        await task.cancel()
        
    # ---------- Interruption tracking ----------
    @ws_transport.event_handler("on_interruption_start")
    async def on_interruption_start(transport):
        logger.info("🛑 INTERRUPTION: User speaking - stopping current TTS")
        
    @ws_transport.event_handler("on_interruption_end")  
    async def on_interruption_end(transport):
        logger.info("▶️  INTERRUPTION: User stopped - processing input")
        
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

    # ---------- Performance monitoring ----------
    async def log_performance():
        """Monitor performance of the cascaded pipeline"""
        import asyncio
        while True:
            try:
                await asyncio.sleep(8)
                if hasattr(task, '_pipeline') and hasattr(task._pipeline, '_processors'):
                    logger.info("📊 === LOCAL PIPELINE PERFORMANCE ===")
                    
                    # Log conversation context stats
                    logger.info(f"💬 Conversation messages: {len(conversation_context.messages)}")
                    
                    # Log component performance
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
                    logger.info("📊 ================================")
            except Exception as e:
                logger.debug(f"Performance monitoring error: {e}")
                break
    
    # Start performance monitoring
    import asyncio
    asyncio.create_task(log_performance())

    # ---------- Runner ----------
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
