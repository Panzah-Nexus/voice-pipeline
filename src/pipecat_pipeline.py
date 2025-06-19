"""
Air-gapped voice pipeline with enhanced Pipecat components
Ultravox (STT + LLM) ▶ Piper (TTS)
Everything runs locally on a Cerebrium A10.
"""

import asyncio
import os
import logging
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.frames.frames import AudioRawFrame, Frame, SystemFrame, TranscriptionFrame, TextFrame
from pipecat.services.ultravox import UltravoxService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.websocket_server import WebsocketServerParams, WebsocketServerTransport
from pipecat.vad.silero import SileroVADAnalyzer

from src.piper_tts_service import PiperTTSService

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Voice Pipeline - Air-Gapped")

# Configuration from environment
HF_TOKEN = os.environ.get("HF_TOKEN", "")
PIPER_MODEL = os.environ.get("PIPER_MODEL", "en_US-lessac-medium")
SAMPLE_RATE = 16000


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
    
    # Create transport
    transport = WebsocketServerTransport(
        websocket=websocket,
        params=WebsocketServerParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_server_time_to_messages=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            vad_start_s=0.2,
            transcription_enabled=False  # Ultravox handles this internally
        )
    )
    
    # System prompt for the assistant
    system_prompt = """You are a helpful voice assistant. Keep your responses concise and conversational.
    You're running on an air-gapped system with no internet access. Be friendly and helpful."""
    
    # Create Ultravox service (combines STT + LLM)
    # Using the 8B model for A10 GPU
    ultravox = UltravoxService(
        api_key=HF_TOKEN,
        model="fixie-ai/ultravox-v0_4_1-llama-3_1-8b",
        temperature=0.6,
        max_tokens=150,
        sample_rate=SAMPLE_RATE,
        system_prompt=system_prompt
    )
    
    # Create Piper TTS service
    tts = PiperTTSService(
        model=PIPER_MODEL,
        sample_rate=SAMPLE_RATE
    )
    
    # Build the pipeline
    pipeline = Pipeline([
        transport.input(),
        ultravox,  # Ultravox handles both STT and LLM in one
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
        await websocket.close(code=1000, reason=str(e))
    finally:
        logger.info("WebSocket connection closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
