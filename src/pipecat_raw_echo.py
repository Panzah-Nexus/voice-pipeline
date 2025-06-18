"""Pipecat echo pipeline that handles raw binary audio."""

import logging
from fastapi import FastAPI, WebSocket
from fastapi.responses import PlainTextResponse
import uvicorn

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketTransport, 
    FastAPIWebsocketParams
)
from pipecat.frames.frames import AudioRawFrame, Frame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.audio.vad.silero import SileroVADAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Pipecat Raw Audio Echo")


class SimpleAudioEcho(FrameProcessor):
    """Simple processor that echoes audio frames."""
    
    def __init__(self):
        super().__init__()
        self.frame_count = 0
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        if isinstance(frame, AudioRawFrame):
            self.frame_count += 1
            logger.info(f"🎵 Echo: Processing audio frame #{self.frame_count}: {len(frame.audio)} bytes")
            
            # Echo it back
            await self.push_frame(frame, direction)
            logger.info(f"🔊 Echo: Pushed audio frame #{self.frame_count}")
        else:
            # Pass through other frames
            logger.info(f"📦 Echo: Passing through {type(frame).__name__}")
            await self.push_frame(frame, direction)


@app.get("/health")
async def health():
    return PlainTextResponse("OK - Pipecat Raw Echo")


@app.get("/ready")
async def ready():
    return PlainTextResponse("OK - Pipecat Raw Echo Ready")


@app.get("/debug")
async def debug():
    return {
        "service": "pipecat_raw_echo",
        "status": "running",
        "description": "Pipecat echo with raw audio serializer"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint using Pipecat with raw audio."""
    await websocket.accept()
    logger.info("✅ WebSocket connected - Pipecat Raw Echo")
    
    try:
        # Import our raw audio serializer
        try:
            from .raw_audio_serializer import RawAudioSerializer
        except ImportError:
            from raw_audio_serializer import RawAudioSerializer
        
        # Create transport with raw audio serializer
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                add_wav_header=False,
                vad_enabled=False,  # Disable VAD for now
                serializer=RawAudioSerializer(),
            )
        )
        logger.info("✅ Transport created with RawAudioSerializer")
        
        # Create echo processor
        echo = SimpleAudioEcho()
        
        # Build pipeline
        pipeline = Pipeline([
            transport.input(),
            echo,
            transport.output()
        ])
        logger.info("✅ Pipeline created")
        
        # Create task
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=False,
            ),
        )
        
        # Run pipeline
        runner = PipelineRunner()
        logger.info("🚀 Starting pipeline...")
        await runner.run(task)
        
    except Exception as e:
        logger.error(f"❌ Pipeline error: {e}", exc_info=True)
    finally:
        logger.info("🔌 Pipeline disconnected")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 