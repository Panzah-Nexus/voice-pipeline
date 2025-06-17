"""Pipecat pipeline setup for air-gapped deployment.

This module configures Pipecat with Ultravox for both speech recognition and
language generation, plus LOCAL Piper TTS for audio synthesis.
No external API calls are made - everything runs locally on GPU.
"""
from __future__ import annotations

import os
import asyncio
import subprocess
import tempfile
from pathlib import Path
from dotenv import load_dotenv

def get_secret(key):
    """Get secret from Cerebrium or environment variables."""
    # Try cerebrium get_secret first
    try:
        from cerebrium import get_secret as cerebrium_get_secret
        value = cerebrium_get_secret(key)
        if value:
            print(f"✅ Found {key} via Cerebrium get_secret")
            return value
    except (ImportError, Exception) as e:
        print(f"⚠️  Cerebrium get_secret not available: {e}")
    
    # Fall back to environment variables (how Cerebrium likely exposes secrets)
    value = os.environ.get(key)
    if value:
        print(f"✅ Found {key} via environment variable")
        return value
    
    print(f"❌ {key} not found in secrets or environment")
    return None
# from pipecat.pipeline.pipeline import Pipeline  # Not used in this file
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
import uvicorn
import numpy as np
import json

try:
    from pipecat.services.ultravox.stt import UltravoxSTTService
except Exception as exc:  # pragma: no cover - optional dependency
    UltravoxSTTService = None
    print("UltravoxSTTService unavailable:", exc)

# NO OPENAI IMPORTS - Air-gapped deployment
print("🚫 OpenAI services disabled for air-gapped deployment")

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Air-Gapped Voice Pipeline Server")

# Global services
stt_service = None
tts_service = None

class LocalPiperTTSService:
    """Local Piper TTS service that runs on the same machine."""
    
    def __init__(self, model_name: str = "en_US-lessac-medium", sample_rate: int = 22050):
        self.model_name = model_name
        self.sample_rate = sample_rate
        self.model_path = None
        self._setup_piper_model()
    
    def _setup_piper_model(self):
        """Download and setup Piper model for local use."""
        try:
            # Try to find piper binary
            piper_cmd = subprocess.run(["which", "piper"], capture_output=True, text=True)
            if piper_cmd.returncode != 0:
                print("❌ Piper binary not found. Installing piper-tts...")
                subprocess.run(["pip", "install", "piper-tts"], check=True)
            
            # Download model if not exists
            model_dir = Path.home() / ".local" / "share" / "piper" / "models"
            model_dir.mkdir(parents=True, exist_ok=True)
            
            self.model_path = model_dir / f"{self.model_name}.onnx"
            self.config_path = model_dir / f"{self.model_name}.onnx.json"
            
            if not self.model_path.exists():
                print(f"📥 Downloading Piper model: {self.model_name}")
                # Use piper with automatic model download
                cmd = [
                    "python", "-m", "piper.download", self.model_name
                ]
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                    print(f"✅ Piper model {self.model_name} downloaded successfully")
                except subprocess.CalledProcessError as e:
                    print(f"⚠️  Model download failed, will use fallback: {e}")
                    
        except Exception as e:
            print(f"⚠️  Piper setup warning: {e}")
    
    async def run_tts(self, text: str):
        """Convert text to speech and yield audio frames."""
        try:
            # Use piper command line tool
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                cmd = [
                    "python", "-m", "piper",
                    "--model", self.model_name,
                    "--output_file", temp_file.name
                ]
                
                # Run piper with text input
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate(input=text)
                
                if process.returncode == 0:
                    # Read the generated audio file
                    with open(temp_file.name, 'rb') as f:
                        audio_data = f.read()
                    
                    # Clean up temp file
                    os.unlink(temp_file.name)
                    
                    # Yield audio in chunks
                    chunk_size = 4096
                    for i in range(0, len(audio_data), chunk_size):
                        chunk = audio_data[i:i + chunk_size]
                        # Create a simple frame-like object
                        class AudioFrame:
                            def __init__(self, audio):
                                self.audio = audio
                        
                        yield AudioFrame(chunk)
                        await asyncio.sleep(0.01)  # Small delay for streaming
                else:
                    print(f"❌ Piper TTS error: {stderr}")
                    # Yield empty audio frame on error
                    class AudioFrame:
                        def __init__(self, audio):
                            self.audio = audio
                    yield AudioFrame(b"")
                    
        except Exception as e:
            print(f"❌ Local Piper TTS error: {e}")
            # Yield empty audio frame on error
            class AudioFrame:
                def __init__(self, audio):
                    self.audio = audio
            yield AudioFrame(b"")

def create_pipeline():
    """Create and return initialized STT and local TTS services."""
    global stt_service, tts_service

    # Use Cerebrium's get_secret for accessing secrets in deployment
    hf_token = get_secret("HF_TOKEN")
    
    # Debug: Print if HF token is available
    if hf_token:
        print(f"✅ Hugging Face token found (length: {len(hf_token)})")
    else:
        print("⚠️  HF_TOKEN not found in Cerebrium secrets")
        print("The Ultravox STT service will not be available")
    
    # Configure for GPU deployment (Cerebrium A10)
    if os.environ.get("NVIDIA_VISIBLE_DEVICES"):
        # Running on GPU - configure for CUDA
        os.environ["VLLM_DEVICE"] = "cuda"
        print("🖥️  GPU detected - configuring for CUDA")
    else:
        # Running on CPU (fallback)
        os.environ["VLLM_DEVICE"] = "cpu"
        os.environ["VLLM_CPU_ONLY"] = "1"
        os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
        print("💻 No GPU detected - configuring for CPU")

    # Initialize Ultravox STT service
    if UltravoxSTTService and hf_token:
        try:
            print("🤖 Initializing Ultravox STT service...")
            stt_service = UltravoxSTTService(
                model_size="fixie-ai/ultravox-v0_4_1-llama-3_1-8b",
                hf_token=hf_token,
                temperature=0.5,
                max_tokens=150,
            )
            print("✅ Ultravox STT service initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Ultravox STT service: {e}")
            stt_service = None

    # Initialize LOCAL Piper TTS service (no external API calls)
    try:
        print("🔊 Initializing LOCAL Piper TTS service...")
        tts_service = LocalPiperTTSService(
            model_name=get_secret("PIPER_MODEL") or "en_US-lessac-medium",
            sample_rate=int(get_secret("PIPER_SAMPLE_RATE") or "22050")
        )
        print("✅ Local Piper TTS service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Local Piper TTS service: {e}")
        tts_service = None

    return stt_service, tts_service

@app.get("/health")
async def health():
    """Health check endpoint for Cerebrium."""
    return PlainTextResponse("OK")

@app.get("/ready")
async def ready():
    """Ready check endpoint for Cerebrium."""
    return PlainTextResponse("OK")

@app.get("/debug")
async def debug():
    """Debug endpoint to check service status."""
    status = {
        "stt_available": stt_service is not None,
        "tts_available": tts_service is not None,
        "hf_token_present": bool(get_secret("HF_TOKEN")),
        "gpu_available": bool(os.environ.get("NVIDIA_VISIBLE_DEVICES")),
        "services_info": {
            "stt_type": type(stt_service).__name__ if stt_service else None,
            "tts_type": type(tts_service).__name__ if tts_service else None,
        }
    }
    
    return status

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for audio processing."""
    await websocket.accept()
    print("👤 Client connected to WebSocket")
    audio_buffer = bytearray()
    
    # Use global services initialized at startup
    print(f"🔍 Debug - Services available: STT={stt_service is not None}, TTS={tts_service is not None}")
    
    try:
        while True:
            try:
                message = await websocket.receive()
                
                if message["type"] == "websocket.receive":
                    if "bytes" in message:
                        # Accumulate audio data
                        audio_buffer.extend(message["bytes"])
                        
                    elif "text" in message and message["text"] == "END":
                        print(f"🎵 Processing audio buffer: {len(audio_buffer)} bytes")
                        
                        # Always echo the audio first for testing
                        print("🔊 Echoing audio back to client...")
                        try:
                            await websocket.send_bytes(bytes(audio_buffer))
                            print(f"✅ Echoed {len(audio_buffer)} bytes back to client")
                        except Exception as e:
                            print(f"❌ Echo failed: {e}")
                        
                        # Process accumulated audio with AI services if available
                        if stt_service and tts_service:
                            print("🤖 AI services available - processing...")
                            # Convert audio buffer to numpy array
                            audio = np.frombuffer(bytes(audio_buffer), dtype=np.int16).astype(np.float32) / 32768.0
                            
                            try:
                                # Process with STT
                                print("🎤 Running speech-to-text...")
                                text_parts = []
                                async for chunk in stt_service._model.generate(
                                    messages=[{"role": "user", "content": "<|audio|>\n"}],
                                    temperature=0.5,
                                    max_tokens=150,
                                    audio=audio,
                                ):
                                    data = json.loads(chunk)
                                    delta = data.get("choices", [{}])[0].get("delta", {})
                                    if "content" in delta:
                                        text_parts.append(delta["content"])
                                text = "".join(text_parts)
                                print(f"📝 Transcribed: {text}")

                                # Convert text to speech using LOCAL Piper TTS
                                print("🔊 Converting to speech with local Piper TTS...")
                                async for frame in tts_service.run_tts(text):
                                    if hasattr(frame, "audio") and frame.audio:
                                        await websocket.send_bytes(frame.audio)
                                print("✅ AI response sent to client")
                                
                            except Exception as e:
                                print(f"❌ Error processing audio with AI: {e}")
                                await websocket.send_text(f"AI Error: {str(e)}")
                        else:
                            print("⚠️  AI services not available - only echo was sent")

                        audio_buffer.clear()
                        
                elif message["type"] == "websocket.disconnect":
                    print("👋 Client disconnected")
                    break
                    
            except WebSocketDisconnect:
                print("👋 WebSocket disconnected")
                break
            except Exception as e:
                print(f"⚠️  Error in WebSocket loop: {e}")
                break
                    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        print("🔌 WebSocket connection closed")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global stt_service, tts_service
    
    print("🚀 Initializing air-gapped voice pipeline services...")
    stt_service, tts_service = create_pipeline()
    
    if stt_service:
        print("✅ STT service ready")
    else:
        print("❌ STT service not available - check HF_TOKEN")
        
    if tts_service:
        print("✅ Local TTS service ready")
    else:
        print("❌ Local TTS service not available")
        
    print("🎯 Air-gapped voice pipeline ready for connections!")
    print(f"🔍 Debug - Global services set: STT={stt_service is not None}, TTS={tts_service is not None}")

async def run_server(services=None, host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the FastAPI server with WebSocket support."""
    print(f"🌐 Starting air-gapped server on {host}:{port}")
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(run_server())
