"""Simple audio echo server that handles raw binary audio."""

import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import PlainTextResponse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Simple Audio Echo Server")

@app.get("/health")
async def health():
    return PlainTextResponse("OK - Simple Audio Echo")

@app.get("/ready")
async def ready():
    return PlainTextResponse("OK - Simple Audio Echo Ready")

@app.get("/debug")
async def debug():
    return {"service": "simple_audio_echo", "status": "running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint that echoes raw audio."""
    await websocket.accept()
    logger.info("✅ WebSocket connection accepted")
    
    try:
        while True:
            # Receive data using FastAPI's WebSocket API
            data = await websocket.receive()
            
            # Check what type of data we received
            if "bytes" in data:
                # Raw binary audio data
                audio_bytes = data["bytes"]
                logger.info(f"📥 Received audio: {len(audio_bytes)} bytes")
                
                # Echo it back immediately
                await websocket.send_bytes(audio_bytes)
                logger.info(f"📤 Echoed audio back")
                
            elif "text" in data:
                # Text message
                text = data["text"]
                logger.info(f"📝 Received text: {text}")
                
                if text == "END":
                    logger.info("🔚 Received END signal")
                    break
                    
                # Echo text back
                await websocket.send_text(f"Echo: {text}")
                
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        logger.info("🔌 WebSocket disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 