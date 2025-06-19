"""
Air-gapped voice pipeline with enhanced Pipecat components
Ultravox (STT + LLM) ▶ Piper (TTS)
Everything runs locally on a Cerebrium A10.

NOTE: This pipeline requires GPU resources to run efficiently.
The Ultravox model is compute-intensive and performs best with GPU acceleration.
Based on the official Pipecat Ultravox example.
"""

import os
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.ultravox.stt import UltravoxSTTService
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketParams, FastAPIWebsocketTransport
from pipecat.audio.vad.silero import SileroVADAnalyzer

from src.piper_tts_service import PiperTTSService
from src.simple_serializer import SimpleFrameSerializer

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Voice Pipeline - Air-Gapped")

# Configuration from environment
HF_TOKEN = os.environ.get("HF_TOKEN", "")
PIPER_MODEL = os.environ.get("PIPER_MODEL", "en_US-lessac-medium")
SAMPLE_RATE = 16000

# Initialize Ultravox processor globally for better performance
# (model loading takes time, so we do it once)
try:
    logger.info("Initializing Ultravox model... This may take a moment.")
    ultravox_processor = UltravoxSTTService(
        model_name="fixie-ai/ultravox-v0_5-llama-3_1-8b",
        hf_token=HF_TOKEN,
        temperature=0.6,
        max_tokens=150
    )
    logger.info("Ultravox model initialized successfully!")
except Exception as e:
    logger.error(f"Failed to initialize Ultravox model: {e}")
    ultravox_processor = None


@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "service": "Voice Pipeline - Air-Gapped",
        "status": "ready",
        "components": {
            "stt_llm": "Ultravox (combined STT+LLM)",
            "tts": "Piper TTS (local)",
            "framework": "Pipecat"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    """Readiness check endpoint."""
    return {"status": "ready"}


@app.get("/debug")
async def debug():
    """Debug endpoint with system info."""
    import torch
    return {
        "cuda_available": torch.cuda.is_available(),
        "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "hf_token_set": bool(HF_TOKEN),
        "piper_model": PIPER_MODEL
    }


async def create_pipeline(websocket: WebSocket) -> tuple:
    """Create the Pipecat pipeline with Ultravox and Piper."""
    
    # Check if Ultravox is initialized
    if ultravox_processor is None:
        raise RuntimeError("Ultravox model failed to initialize. Check your HF_TOKEN and internet connection.")
    
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
            serializer=SimpleFrameSerializer()
        )
    )
    
    # Create Piper TTS service
    tts = PiperTTSService(
        model=PIPER_MODEL,
        sample_rate=SAMPLE_RATE
    )
    
    # Build the pipeline
    pipeline = Pipeline([
        transport.input(),
        ultravox_processor,  # Use the pre-initialized Ultravox processor
        tts,
        transport.output()
    ])
    
    # Create runner
    runner = PipelineRunner()
    
    # Create task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=False,
            enable_usage_metrics=False
        )
    )
    
    return runner, task


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for voice pipeline."""
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    
    try:
        # Create and run pipeline
        runner, task = await create_pipeline(websocket)
        
        # Run the pipeline
        await runner.run(task)
        
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        try:
            await websocket.close(code=1000, reason=str(e))
        except:
            pass  # WebSocket might already be closed
    finally:
        logger.info("WebSocket connection closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
