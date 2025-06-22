"""
Air-gapped Pipecat bot with RTVI compatibility for Runpod deployment
====================================================================
This module wires together:

* **UltravoxSTTService** – combined STT + LLM (local) with context
* **KokoroTTSService**   – offline TTS (local)

All AI processing happens on Runpod GPU infrastructure without external API calls.
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
# Context-aware Ultravox processor
# ---------------------------------------------------------------------------
class UltravoxContextProcessor(FrameProcessor):
    """
    Processor that manages conversation context for Ultravox.
    
    This sits between the transport and Ultravox service to:
    1. Maintain conversation history in OpenAILLMContext
    2. Pass context to Ultravox for each audio processing
    3. Update context with responses
    """
    
    def __init__(self, ultravox_service: UltravoxSTTService, context: OpenAILLMContext):
        super().__init__()
        self._ultravox = ultravox_service
        self._context = context
        self._processing_audio = False
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        # Pass through most frames
        if isinstance(frame, UserStartedSpeakingFrame):
            logger.info("👤 User started speaking")
            self._processing_audio = True
            
        elif isinstance(frame, UserStoppedSpeakingFrame):
            logger.info("👤 User stopped speaking - processing with context")
            # Inject context before Ultravox processes the audio
            await self._inject_context_to_ultravox()
            
        elif isinstance(frame, TextFrame):
            # This is likely a response from Ultravox - add to context
            await self._handle_ultravox_response(frame)
            
        elif isinstance(frame, LLMFullResponseEndFrame):
            # Complete response from Ultravox - finalize context
            await self._finalize_response_context(frame)
            self._processing_audio = False
            
        # Always pass frame downstream
        await self.push_frame(frame, direction)
    
    async def _inject_context_to_ultravox(self):
        """Inject current conversation context into Ultravox before processing."""
        try:
            # Get current conversation messages
            messages = self._context.get_messages()
            
            # Set up Ultravox with conversation history
            if hasattr(self._ultravox, 'model') and hasattr(self._ultravox.model, 'format_prompt'):
                # Format the conversation for Ultravox
                formatted_prompt = self._ultravox.model.format_prompt(messages)
                logger.info(f"📝 Injected {len(messages)} messages into Ultravox context")
                logger.debug(f"Context preview: {formatted_prompt[:200]}...")
                
        except Exception as e:
            logger.error(f"Failed to inject context to Ultravox: {e}")
    
    async def _handle_ultravox_response(self, frame: TextFrame):
        """Handle streaming response from Ultravox."""
        # For now, just log the streaming text
        # We'll accumulate the full response in _finalize_response_context
        logger.debug(f"Ultravox streaming: {frame.text[:50]}...")
    
    async def _finalize_response_context(self, frame: LLMFullResponseEndFrame):
        """Add the complete response to conversation context."""
        try:
            if frame.text and frame.text.strip():
                # Add user message (placeholder for audio input)
                self._context.add_message({
                    "role": "user", 
                    "content": "[Audio input]"  # Could be enhanced with actual transcription
                })
                
                # Add assistant response
                self._context.add_message({
                    "role": "assistant",
                    "content": frame.text.strip()
                })
                
                total_messages = len(self._context.get_messages())
                logger.info(f"✅ Added response to context. Total messages: {total_messages}")
                
                # Log recent conversation for debugging
                messages = self._context.get_messages()
                for msg in messages[-4:]:  # Last 4 messages
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:100]
                    logger.debug(f"  {role}: {content}...")
                    
        except Exception as e:
            logger.error(f"Failed to finalize response context: {e}")

# ---------------------------------------------------------------------------
# Enhanced Ultravox service with direct context integration
# ---------------------------------------------------------------------------
class ContextAwareUltravoxService(UltravoxSTTService):
    """
    Enhanced Ultravox service that can receive and use conversation context.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_context_messages = []
        
    def set_conversation_context(self, messages):
        """Set the current conversation context for the next audio processing."""
        self._current_context_messages = messages
        logger.info(f"🔄 Context updated: {len(messages)} messages")
        
    async def _process_audio_buffer(self):
        """Override to use conversation context when processing audio."""
        buffer = self._audio_buffer
        if not buffer or not buffer.frames:
            logger.warning("Empty audio buffer received")
            return
            
        try:
            logger.info("🎙️ Processing audio with conversation context...")
            
            # Use current context messages or fall back to system instruction
            messages = self._current_context_messages if self._current_context_messages else []
            if not messages and hasattr(self, '_system_instruction') and self._system_instruction:
                messages = [{"role": "system", "content": self._system_instruction}]
            
            logger.info(f"📝 Using {len(messages)} context messages")
            
            # Convert audio frames to numpy array
            import numpy as np
            audio_data = b''.join([frame.audio for frame in buffer.frames])
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Generate response using conversation history
            full_response = ""
            async for chunk in self.model.generate(
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                audio=audio_array
            ):
                # Parse JSON response from Ultravox
                import json
                try:
                    chunk_data = json.loads(chunk)
                    if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                        choice = chunk_data['choices'][0]
                        if 'delta' in choice and 'content' in choice['delta']:
                            content = choice['delta']['content']
                            if content:
                                full_response += content
                                yield TextFrame(content)
                except json.JSONDecodeError:
                    # Fallback: treat as plain text
                    if chunk.strip():
                        full_response += chunk
                        yield TextFrame(chunk)
            
            # Send final response
            if full_response.strip():
                logger.info(f"✅ Generated full response: {full_response[:100]}...")
                yield LLMFullResponseEndFrame(full_response)
                
        except Exception as e:
            logger.error(f"Error processing audio buffer: {e}")
            import traceback
            logger.error(traceback.format_exc())

# ---------------------------------------------------------------------------
# Context bridge processor
# ---------------------------------------------------------------------------
class ContextBridgeProcessor(FrameProcessor):
    """
    Bridges the OpenAI context to the Ultravox service.
    """
    
    def __init__(self, ultravox_service: ContextAwareUltravoxService, context: OpenAILLMContext):
        super().__init__()
        self._ultravox = ultravox_service
        self._context = context
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        if isinstance(frame, UserStoppedSpeakingFrame):
            # Before audio processing, update Ultravox with latest context
            messages = self._context.get_messages()
            self._ultravox.set_conversation_context(messages)
            
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
# Initialize Ultravox processor once at module level
# ---------------------------------------------------------------------------
# Want to initialize the ultravox processor since it takes time to load the model and dont
# want to load it every time the pipeline is run
logger.info("Loading ContextAwareUltravoxService... this can take a while on first run.")
ultravox_service = ContextAwareUltravoxService(
    model_name="fixie-ai/ultravox-v0_5-llama-3_1-8b",
    hf_token=HF_TOKEN,
    temperature=0.3,  # Lower temperature = faster inference + more consistent
    max_tokens=40,    # Shorter responses = much faster + less chance for language drift
    system_instruction=ENGLISH_ONLY_SYSTEM,  # Strong language constraints
)
logger.info("Ultravox model initialized successfully!")


async def run_bot(websocket_client):
    """Entry-point used by Pipecat example clients."""
    
    logger.info("Starting bot with context management")

    # 1️⃣ Create conversation context with system instruction
    context = OpenAILLMContext(
        messages=[
            {
                "role": "system", 
                "content": ENGLISH_ONLY_SYSTEM
            }
        ]
    )

    # 2️⃣ WebSocket transport – identical params to reference example
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

    # 3️⃣ Local TTS (Kokoro)
    tts = KokoroTTSService(
        model_path=KOKORO_MODEL_PATH,
        voices_path=KOKORO_VOICES_PATH,
        voice_id=KOKORO_VOICE_ID,
        sample_rate=SAMPLE_RATE,
    )

    # 4️⃣ RTVI signalling layer – required for Pipecat web client
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # 5️⃣ Context management processors
    context_bridge = ContextBridgeProcessor(ultravox_service, context)
    context_processor = UltravoxContextProcessor(ultravox_service, context)

    # 6️⃣ Pipeline with proper context management
    pipeline = Pipeline(
        [
            ws_transport.input(),
            rtvi,           
            context_bridge,       # Injects context into Ultravox
            context_processor,    # Manages conversation history
            ultravox_service,     # Enhanced STT+LLM with context
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

    # ---------- Context monitoring ----------
    async def monitor_context():
        """Monitor conversation context for debugging"""
        import asyncio
        while True:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                messages = context.get_messages()
                msg_count = len(messages)
                if msg_count > 1:  # More than just system message
                    logger.info(f"📝 CONVERSATION: {msg_count} messages")
                    # Show last 2 messages for debugging
                    for msg in messages[-2:]:
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')[:100] + "..." if len(msg.get('content', '')) > 100 else msg.get('content', '')
                        logger.info(f"   {role}: {content}")
                else:
                    logger.debug("📝 CONVERSATION: Only system message")
            except Exception as e:
                logger.debug(f"Context monitoring error: {e}")
                break
    
    # Start context monitoring
    import asyncio
    asyncio.create_task(monitor_context())

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
