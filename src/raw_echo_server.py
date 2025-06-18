"""Ultra-simple WebSocket echo server - no frameworks, just echo."""

import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import PlainTextResponse
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Raw Echo Server")

@app.get("/health")
async def health():
    return PlainTextResponse("OK - Raw Echo")

@app.get("/ready")
async def ready():
    return PlainTextResponse("OK - Raw Echo Ready")

@app.get("/debug")
async def debug():
    return {"service": "raw_echo", "status": "running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Simple echo - whatever comes in, goes back out."""
    await websocket.accept()
    logger.info("✅ WebSocket connected - Raw Echo Mode")
    
    try:
        message_count = 0
        while True:
            # Receive data
            data = await websocket.receive()
            message_count += 1
            
            # Log what we received
            if "bytes" in data:
                bytes_data = data["bytes"]
                logger.info(f"📥 Received bytes #{message_count}: {len(bytes_data)} bytes")
                # Echo it back immediately
                await websocket.send_bytes(bytes_data)
                logger.info(f"📤 Echoed bytes #{message_count} back")
            elif "text" in data:
                text_data = data["text"]
                logger.info(f"📝 Received text #{message_count}: {text_data}")
                # Echo text back as text
                await websocket.send_text(f"Echo: {text_data}")
                logger.info(f"📤 Echoed text #{message_count} back")
                
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        logger.info("🔌 WebSocket disconnected")

@app.on_event("startup")
async def startup():
    logger.info("🔊 Raw Echo Server Started")
    logger.info("This server echoes everything back immediately")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 