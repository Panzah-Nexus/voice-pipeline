"""Simple echo pipeline for testing - just echoes audio back."""

import os
import asyncio
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

app = FastAPI(title="Echo Pipeline Test Server")


class AudioEchoProcessor(FrameProcessor):
    """Simple processor that echoes audio frames with logging."""
    
    def __init__(self):
        super().__init__()
        self.frame_count = 0
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        if isinstance(frame, AudioRawFrame):
            self.frame_count += 1
            logger.info(f"🎵 Echo: Received audio frame #{self.frame_count}: {len(frame.audio)} bytes")
            
            # Echo it back immediately
            await self.push_frame(frame, direction)
            logger.info(f"🔊 Echo: Sent audio frame #{self.frame_count} back")
        else:
            logger.info(f"📦 Echo: Received {type(frame).__name__}")
            await self.push_frame(frame, direction)


@app.get("/health")
async def health():
    return PlainTextResponse("OK - Echo Pipeline")


@app.get("/ready")
async def ready():
    return PlainTextResponse("OK - Echo Pipeline Ready")


@app.get("/debug")
async def debug():
    return {
        "service": "echo_pipeline",
        "status": "running",
        "description": "Simple audio echo for testing"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint that echoes audio."""
    await websocket.accept()
    logger.info("✅ Echo WebSocket connected")
    
    try:
        # Import serializer
        try:
            from .protobuf_serializer import SimpleProtobufSerializer
        except ImportError:
            from protobuf_serializer import SimpleProtobufSerializer
        
        # Create transport
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                add_wav_header=False,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                vad_audio_passthrough=True,
                serializer=SimpleProtobufSerializer(),
            )
        )
        logger.info("✅ Transport created")
        
        # Create echo processor
        echo = AudioEchoProcessor()
        
        # Build simple pipeline: input -> echo -> output
        pipeline = Pipeline([
            transport.input(),
            echo,
            transport.output()
        ])
        logger.info("✅ Echo pipeline created")
        
        # Create and run task
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
            ),
        )
        
        runner = PipelineRunner()
        logger.info("🚀 Starting echo pipeline...")
        await runner.run(task)
        
    except Exception as e:
        logger.error(f"❌ Echo pipeline error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("🔌 Echo pipeline disconnected")


@app.on_event("startup")
async def startup_event():
    """Initialize echo pipeline on startup."""
    logger.info("🔊 Echo Pipeline Server Started")
    logger.info("This server simply echoes audio back for testing")
    

async def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the echo server."""
    logger.info(f"🌐 Starting echo server on {host}:{port}")
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run_server()) 