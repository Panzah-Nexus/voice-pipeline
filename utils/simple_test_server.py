"""Simple test server for audio echo testing."""
from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
import uvicorn
import asyncio

# Initialize FastAPI app
app = FastAPI(title="Voice Pipeline Test Server")

@app.get("/health")
async def health():
    """Health check endpoint for Cerebrium."""
    return {"status": "OK"}

@app.get("/ready")
async def ready():
    """Ready check endpoint for Cerebrium."""
    return PlainTextResponse("OK")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for audio echo testing."""
    await websocket.accept()
    print("Client connected to WebSocket")
    
    audio_buffer = bytearray()
    chunk_count = 0
    
    try:
        while True:
            try:
                # Check if connection is still alive
                message = await asyncio.wait_for(websocket.receive(), timeout=1.0)
                
                if message["type"] == "websocket.receive":
                    if "bytes" in message:
                        chunk_count += 1
                        audio_buffer.extend(message["bytes"])
                        print(f"Received audio chunk: {len(message['bytes'])} bytes")
                        
                        # Process every 10 chunks (~5 seconds)
                        if chunk_count >= 10:
                            print(f"Processing audio buffer: {len(audio_buffer)} bytes")
                            
                            # Echo the audio back
                            if audio_buffer:
                                await websocket.send_bytes(bytes(audio_buffer))
                                print("Audio echoed back to client")
                            
                            # Reset buffer
                            audio_buffer.clear()
                            chunk_count = 0
                            
                    elif "text" in message:
                        if message["text"] == "END":
                            print(f"Processing audio buffer: {len(audio_buffer)} bytes")
                            if audio_buffer:
                                await websocket.send_bytes(bytes(audio_buffer))
                                print("Audio echoed back to client")
                            audio_buffer.clear()
                            chunk_count = 0
                        else:
                            print(f"Received text: {message['text']}")
                            await websocket.send_text(f"Echo: {message['text']}")
                            
                elif message["type"] == "websocket.disconnect":
                    print("Client disconnected")
                    break
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_text("ping")
                except:
                    break
            except WebSocketDisconnect:
                print("WebSocket disconnected")
                break
            except Exception as e:
                print(f"Error in WebSocket loop: {e}")
                break
                
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        print("WebSocket connection closed")

async def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the FastAPI server with WebSocket support."""
    print(f"Starting test server on {host}:{port}")
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(run_server()) 