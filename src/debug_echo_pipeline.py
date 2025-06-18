"""Debug echo pipeline with extensive logging."""

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

# Enable DEBUG logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Debug Echo Pipeline")


class DebugEchoProcessor(FrameProcessor):
    """Echo processor with extensive debug logging."""
    
    def __init__(self):
        super().__init__()
        self.frame_count = 0
        logger.info("🔧 DebugEchoProcessor initialized")
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        self.frame_count += 1
        logger.info(f"🔍 Frame #{self.frame_count} - Type: {type(frame).__name__}, Direction: {direction}")
        
        # Log frame details
        if isinstance(frame, AudioRawFrame):
            logger.info(f"   📊 Audio: {len(frame.audio)} bytes, {frame.sample_rate}Hz, {frame.num_channels} ch")
            # Log first few bytes to verify it's real audio
            first_bytes = frame.audio[:20] if len(frame.audio) >= 20 else frame.audio
            logger.info(f"   📊 First bytes: {first_bytes.hex()}")
        
        # Process the frame
        await super().process_frame(frame, direction)
        
        # Echo audio frames
        if isinstance(frame, AudioRawFrame):
            logger.info(f"   🔊 Echoing audio frame #{self.frame_count}")
            try:
                await self.push_frame(frame, direction)
                logger.info(f"   ✅ Frame pushed successfully")
            except Exception as e:
                logger.error(f"   ❌ Error pushing frame: {e}")
        else:
            # Pass through other frames
            await self.push_frame(frame, direction)


@app.get("/health")
async def health():
    return PlainTextResponse("OK - Debug Echo")


@app.get("/ready")
async def ready():
    return PlainTextResponse("OK - Debug Echo Ready")


@app.get("/debug")
async def debug():
    return {
        "service": "debug_echo_pipeline",
        "status": "running",
        "description": "Debug echo with extensive logging"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint with debug logging."""
    await websocket.accept()
    logger.info("=" * 60)
    logger.info("🔌 NEW WEBSOCKET CONNECTION")
    logger.info("=" * 60)
    
    try:
        # Import serializer
        try:
            from .protobuf_serializer import SimpleProtobufSerializer
            logger.info("✅ Imported SimpleProtobufSerializer")
        except ImportError:
            from protobuf_serializer import SimpleProtobufSerializer
            logger.info("✅ Imported SimpleProtobufSerializer (fallback)")
        
        # Create VAD
        logger.info("🎤 Creating VAD analyzer...")
        vad = SileroVADAnalyzer()
        logger.info("✅ VAD created")
        
        # Create transport
        logger.info("🚀 Creating transport...")
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                add_wav_header=False,
                vad_enabled=True,
                vad_analyzer=vad,
                vad_audio_passthrough=True,
                serializer=SimpleProtobufSerializer(),
            )
        )
        logger.info("✅ Transport created")
        
        # Create echo processor
        logger.info("🔊 Creating echo processor...")
        echo = DebugEchoProcessor()
        logger.info("✅ Echo processor created")
        
        # Build pipeline
        logger.info("🔗 Building pipeline...")
        pipeline = Pipeline([
            transport.input(),
            echo,
            transport.output()
        ])
        logger.info(f"✅ Pipeline built with {len(pipeline._processors)} processors")
        
        # Create task
        logger.info("📋 Creating pipeline task...")
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
                enable_usage_metrics=False,
            ),
        )
        logger.info("✅ Task created")
        
        # Run pipeline
        runner = PipelineRunner()
        logger.info("🏃 Starting pipeline runner...")
        
        try:
            await runner.run(task)
            logger.info("✅ Pipeline completed normally")
        except Exception as e:
            logger.error(f"❌ Pipeline error: {e}", exc_info=True)
        
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}", exc_info=True)
    finally:
        logger.info("🔌 WebSocket disconnected")
        logger.info("=" * 60)


@app.on_event("startup")
async def startup_event():
    """Log startup."""
    logger.info("🚀 Debug Echo Pipeline Server Started")
    logger.info("📊 Logging level: DEBUG")
    logger.info("🔍 This server logs everything for debugging")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug") 