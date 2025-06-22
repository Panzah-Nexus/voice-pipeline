"""
Air-gapped Pipecat bot with RTVI compatibility for Runpod deployment
====================================================================
This module wires together:

* **UltravoxSTTService** – speech-to-speech service (local) with conversation context
* **KokoroTTSService**   – offline TTS (local)

All AI processing happens on Runpod GPU infrastructure without external API calls.

Note: UltravoxSTTService is a speech-to-speech service similar to Gemini Multimodal Live,
not just an STT service. It handles both speech-to-text AND language model generation
internally, so it doesn't need external context aggregators.
"""

import os
import sys

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
from pipecat.processors.metrics.frame_processor_metrics import (
    FrameProcessorMetrics,
)
from pipecat.frames.frames import (
    TranscriptionFrame,
    TTSTextFrame,
    TextFrame,
    Frame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    LLMFullResponseEndFrame,
)
from pipecat.processors.aggregators.openai_llm_context import (
    OpenAILLMContext,
    OpenAILLMContextFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from pipecat.services.ultravox.stt import UltravoxSTTService

# Kokoro TTS service (preferred over Piper)
from src.kokoro_tts_service import KokoroTTSService


# ---------------------------------------------------------------------------
# Conversation history manager for Ultravox
# ---------------------------------------------------------------------------
class UltravoxConversationHistory:
    """
    Manages conversation history for Ultravox.
    
    Since Ultravox is a speech-to-speech service (like Gemini Multimodal Live),
    it handles context internally. This class tracks conversation for monitoring
    and provides context when needed.
    """
    
    def __init__(self, system_instruction: str, max_history: int = 10):
        self.system_instruction = system_instruction
        self.max_history = max_history
        self.messages = [{"role": "system", "content": system_instruction}]
        
    def add_user_message(self, content: str):
        """Add a user message to conversation history."""
        self.messages.append({"role": "user", "content": content})
        self._trim_history()
        
    def add_assistant_message(self, content: str):
        """Add an assistant message to conversation history."""
        self.messages.append({"role": "assistant", "content": content})
        self._trim_history()
        
    def get_messages(self):
        """Get current conversation messages."""
        return self.messages.copy()
        
    def _trim_history(self):
        """Keep only recent messages to avoid context overflow."""
        if len(self.messages) > self.max_history:
            # Always keep system message + recent messages
            self.messages = [self.messages[0]] + self.messages[-(self.max_history-1):]
            
    def get_summary(self):
        """Get a summary of current conversation state."""
        total = len(self.messages)
        user_count = sum(1 for m in self.messages if m['role'] == 'user')
        assistant_count = sum(1 for m in self.messages if m['role'] == 'assistant')
        return {
            'total_messages': total,
            'user_messages': user_count,
            'assistant_messages': assistant_count
        }


# ---------------------------------------------------------------------------
# Context injection processor for Ultravox
# ---------------------------------------------------------------------------
class UltravoxContextProcessor(FrameProcessor):
    """
    Processor that injects conversation context into Ultravox.
    
    This processor:
    1. Maintains conversation history for monitoring
    2. Injects context via OpenAILLMContextFrame before audio processing
    3. Tracks responses for conversation history
    """
    
    def __init__(self, conversation_history: UltravoxConversationHistory):
        super().__init__()
        self.conversation_history = conversation_history
        self.current_response = ""
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames to maintain conversation context."""
        
        # Handle user speech events - inject context before processing
        if isinstance(frame, UserStoppedSpeakingFrame):
            # User finished speaking - inject conversation context for Ultravox
            context = OpenAILLMContext(messages=self.conversation_history.get_messages())
            context_frame = OpenAILLMContextFrame(context=context)
            
            # Push context frame first, then the user stopped speaking frame
            await self.push_frame(context_frame, direction)
            logger.info(f"🔄 Injected context with {len(self.conversation_history.get_messages())} messages")
            
            # Add placeholder for user message to history (audio input)
            self.conversation_history.add_user_message("[Audio input]")
            logger.info("📤 Added user audio input to conversation history")
            
        # Handle assistant response text accumulation
        elif isinstance(frame, TextFrame) and direction == FrameDirection.DOWNSTREAM:
            # Accumulate assistant response text
            self.current_response += frame.text
            
        # Handle end of assistant response
        elif isinstance(frame, LLMFullResponseEndFrame):
            # Complete response received - add to conversation history
            if self.current_response.strip():
                self.conversation_history.add_assistant_message(self.current_response.strip())
                summary = self.conversation_history.get_summary()
                logger.info(f"🤖 Added assistant response to history. Total: {summary['total_messages']} messages")
                self.current_response = ""
        
        # Always pass frame through
        await self.push_frame(frame, direction)


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

# Ultra-aggressive English-only system instructions (prevents Chinese switching)
ENGLISH_ONLY_SYSTEM = (
    "Follow these eight instructions in ALL your responses:\n"
    "1. Use English language ONLY in all responses;\n"
    "2. Never switch to Chinese, Japanese, Korean, or any other language;\n"
    "3. If you detect Chinese characters, immediately switch back to English;\n"
    "4. Use Latin alphabet exclusively in all text output;\n"
    "5. Translate any non-English input to English before responding;\n"
    "6. Keep responses conversational and natural in English;\n"
    "7. Maintain context from previous conversation turns;\n"
    "8. Respond with helpful information in clear English only."
)

# ---------------------------------------------------------------------------
# Initialize components once at module level
# ---------------------------------------------------------------------------
logger.info("Initializing conversation history manager...")
conversation_history = UltravoxConversationHistory(
    system_instruction=ENGLISH_ONLY_SYSTEM,
    max_history=10
)

logger.info("Loading UltravoxSTTService... this can take a while on first run.")
# Note: UltravoxSTTService is actually a speech-to-speech service, not just STT
ultravox_service = UltravoxSTTService(
    model_name="fixie-ai/ultravox-v0_5-llama-3_1-8b",
    hf_token=HF_TOKEN,
    temperature=0.3,  # Lower temperature = faster inference + more consistent
    max_tokens=40,    # Shorter responses = much faster + less chance for language drift
    system_instruction=ENGLISH_ONLY_SYSTEM,  # Strong language constraints
)
logger.info("Ultravox model initialized successfully!")


async def run_bot(websocket_client):
    """Entry-point used by Pipecat example clients."""
    
    logger.info("Starting bot with Ultravox speech-to-speech conversation context")

    # 1️⃣ WebSocket transport – identical params to reference example
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

    # 2️⃣ Local TTS (Kokoro) - Note: Ultravox generates text, Kokoro converts to speech
    tts = KokoroTTSService(
        model_path=KOKORO_MODEL_PATH,
        voices_path=KOKORO_VOICES_PATH,
        voice_id=KOKORO_VOICE_ID,
        sample_rate=SAMPLE_RATE,
    )

    # 3️⃣ RTVI signalling layer – required for Pipecat web client
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # 4️⃣ Context processor for conversation management
    context_processor = UltravoxContextProcessor(conversation_history)

    # 5️⃣ Clean, simple pipeline with proper speech-to-speech architecture
    pipeline = Pipeline(
        [
            ws_transport.input(),
            rtvi,           
            context_processor,    # Manages conversation context injection
            ultravox_service,     # Speech-to-speech (STT + LLM combined)
            tts,                  # Text-to-speech for audio output
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
        logger.info("Pipecat client ready.")
        await rtvi.set_bot_ready()
        # Pipeline is ready - initial greeting will happen when user speaks

    @ws_transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")

    @ws_transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    # ---------- Conversation monitoring ----------
    async def monitor_conversation():
        """Monitor conversation context for debugging"""
        import asyncio
        while True:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                summary = conversation_history.get_summary()
                if summary['total_messages'] > 1:  # More than just system message
                    logger.info(f"💬 CONVERSATION: {summary}")
                    # Show last 2 messages for debugging
                    recent_messages = conversation_history.get_messages()[-2:]
                    for msg in recent_messages:
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')[:100] + "..." if len(msg.get('content', '')) > 100 else msg.get('content', '')
                        logger.info(f"   {role}: {content}")
                else:
                    logger.debug("💬 CONVERSATION: Only system message")
            except Exception as e:
                logger.debug(f"Conversation monitoring error: {e}")
                break
    
    # Start conversation monitoring
    import asyncio
    asyncio.create_task(monitor_conversation())

    # ---------- Metrics monitoring ----------
    async def log_metrics():
        """Log performance metrics every 10 seconds"""
        import asyncio
        while True:
            try:
                await asyncio.sleep(10)
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
    
    # Start metrics logging in background
    asyncio.create_task(log_metrics())

    # ---------- Runner ----------
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
