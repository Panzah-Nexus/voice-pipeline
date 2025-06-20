"""
Entry point for the air-gapped voice pipeline demo.
Follows official Pipecat server pattern.
"""

import asyncio
import os
import sys
import logging
import tracemalloc
from contextlib import asynccontextmanager
from typing import Any, Dict
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware

# Enable tracemalloc for debugging
tracemalloc.start()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.pipecat_pipeline import run_bot


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles FastAPI startup and shutdown."""
    yield  # Run app


# Initialize FastAPI app with lifespan manager
app = FastAPI(title="Voice Pipeline - Air-gapped", lifespan=lifespan)

# Configure CORS to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "service": "Voice Pipeline - Air-gapped",
        "status": "ready",
        "components": {
            "stt_llm": "Ultravox v0.5 (Llama-3-8B)",
            "tts": "en_US-lessac-medium",
            "framework": "Pipecat + RTVI"
        }
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted")
    try:
        await run_bot(websocket)
    except Exception as e:
        print(f"Exception in run_bot: {e}")


@app.post("/connect")
async def bot_connect(request: Request) -> Dict[Any, Any]:
    """Connect endpoint - returns WebSocket connection details."""
    # Check if we're running on Runpod by looking for proxy headers
    x_forwarded_host = request.headers.get("x-forwarded-host")
    x_forwarded_proto = request.headers.get("x-forwarded-proto")
    
    if x_forwarded_host and "proxy.runpod.net" in x_forwarded_host:
        # We're on Runpod, use the forwarded host
        scheme = "wss" if x_forwarded_proto == "https" else "wss"  # Always use wss for Runpod
        ws_url = f"{scheme}://{x_forwarded_host}/ws"
    else:
        # Local development or other deployment
        host = request.headers.get("host", "localhost:8000")
        scheme = "wss" if request.url.scheme == "https" else "ws"
        ws_url = f"{scheme}://{host}/ws"
    
    logging.info(f"Connect request - returning WebSocket URL: {ws_url}")
    logging.info(f"Request headers: x-forwarded-host={x_forwarded_host}, x-forwarded-proto={x_forwarded_proto}")
    return {"ws_url": ws_url}


async def main():
    """Main server startup function."""
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logging.info(f"Starting voice pipeline server on {host}:{port}")
    
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except asyncio.CancelledError:
        print("Server cancelled (probably due to shutdown).")


if __name__ == "__main__":
    asyncio.run(main())
