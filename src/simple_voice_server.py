"""Simplified voice pipeline server for testing.

This server accepts raw audio over WebSocket and processes it through
Ultravox + Piper without complex frame serialization.
"""

import asyncio
import os
import logging
from fastapi import FastAPI, WebSocket
from fastapi.responses import PlainTextResponse
import numpy as np

# Import Pipecat components
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.frames.frames import (
    Frame, AudioRawFrame, OutputAudioRawFrame, 
    UserStartedSpeakingFrame, UserStoppedSpeakingFrame
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.audio.vad.silero import SileroVADAnalyzer

# Import services
try:
    from pipecat.services.ultravox.stt import UltravoxSTTService
except:
    UltravoxSTTService = None

try:
    from .piper_tts_service import PiperTTSService
except:
    from piper_tts_service import PiperTTSService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Global services
stt_service = None
tts_service = None


class WebSocketAudioTransport(FrameProcessor):
    """Simple WebSocket transport for raw audio."""
    
    def __init__(self, websocket: WebSocket):
        super().__init__()
        self.websocket = websocket
        self.vad = SileroVADAnalyzer()
        self._audio_buffer = bytearray()
        self._speaking = False
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames in the pipeline."""
        await super().process_frame(frame, direction)
        
        # Send audio output back to client
        if isinstance(frame, OutputAudioRawFrame):
            try:
                await self.websocket.send_bytes(frame.audio)
            except Exception as e:
                logger.error(f"Error sending audio: {e}")
                
        # Just pass through other frames
        await self.push_frame(frame, direction)
        
    async def receive_audio(self):
        """Receive and process audio from WebSocket."""
        try:
            while True:
                # Receive raw audio bytes
                data = await self.websocket.receive_bytes()
                
                # Add to buffer
                self._audio_buffer.extend(data)
                
                # Process in chunks of 8000 samples (0.5 seconds at 16kHz)
                while len(self._audio_buffer) >= 16000:
                    # Extract chunk
                    chunk = self._audio_buffer[:16000]
                    self._audio_buffer = self._audio_buffer[16000:]
                    
                    # Convert to numpy array
                    audio_np = np.frombuffer(chunk, dtype=np.int16)
                    
                    # Run VAD
                    speaking = await self.vad.analyze_audio(audio_np)
                    
                    # Handle speaking state changes
                    if speaking and not self._speaking:
                        self._speaking = True
                        await self.push_frame(UserStartedSpeakingFrame())
                        logger.info("🎙️ User started speaking")
                        
                    elif not speaking and self._speaking:
                        self._speaking = False
                        await self.push_frame(UserStoppedSpeakingFrame())
                        logger.info("🤐 User stopped speaking")
                    
                    # Always push audio frame
                    frame = AudioRawFrame(
                        audio=bytes(chunk),
                        sample_rate=16000,
                        num_channels=1
                    )
                    await self.push_frame(frame)
                    
        except Exception as e:
            logger.error(f"Error receiving audio: {e}")


def get_token(key: str) -> str:
    """Get token from environment."""
    return os.environ.get(key, "")


@app.get("/health")
async def health():
    return PlainTextResponse("OK")


@app.get("/ready")
async def ready():
    return PlainTextResponse("OK")


@app.on_event("startup")
async def startup():
    """Initialize services on startup."""
    global stt_service, tts_service
    
    logger.info("🚀 Initializing simple voice pipeline...")
    
    # Initialize STT
    hf_token = get_token("HF_TOKEN")
    if UltravoxSTTService and hf_token:
        try:
            stt_service = UltravoxSTTService(
                model_size="fixie-ai/ultravox-v0_4_1-llama-3_1-8b",
                hf_token=hf_token,
                temperature=0.5,
                max_tokens=150,
            )
            logger.info("✅ Ultravox STT ready")
        except Exception as e:
            logger.error(f"❌ Failed to initialize STT: {e}")
    
    # Initialize TTS
    try:
        tts_service = PiperTTSService(
            model_name="en_US-lessac-medium",
            sample_rate=16000
        )
        logger.info("✅ Piper TTS ready")
    except Exception as e:
        logger.error(f"❌ Failed to initialize TTS: {e}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections."""
    await websocket.accept()
    logger.info("✅ Client connected")
    
    try:
        # Create transport
        transport = WebSocketAudioTransport(websocket)
        
        # Build pipeline
        pipeline_components = [transport]
        
        if stt_service:
            pipeline_components.append(stt_service)
            
        if tts_service:
            pipeline_components.append(tts_service)
            
        pipeline_components.append(transport)  # Output
        
        # Create pipeline
        pipeline = Pipeline(pipeline_components)
        
        # Create task
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
            ),
        )
        
        # Run pipeline
        runner = PipelineRunner()
        
        # Start receiving audio in background
        receive_task = asyncio.create_task(transport.receive_audio())
        
        try:
            # Run the pipeline
            await runner.run(task)
        finally:
            receive_task.cancel()
            
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
    finally:
        logger.info("🔌 Client disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 