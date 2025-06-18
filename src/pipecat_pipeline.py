"""Pipecat pipeline setup for air-gapped deployment.

This module configures Pipecat with Ultravox for both speech recognition and
language generation, plus LOCAL Piper TTS for audio synthesis.
No external API calls are made - everything runs locally on GPU.
"""
from __future__ import annotations

import os
import asyncio
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

from fastapi import FastAPI, WebSocket
from fastapi.responses import PlainTextResponse
import uvicorn

# Import Pipecat services
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketTransport, 
    FastAPIWebsocketParams
)
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

try:
    from pipecat.services.ultravox.stt import UltravoxSTTService
except Exception as exc:
    UltravoxSTTService = None
    print("UltravoxSTTService unavailable:", exc)

# Use our Piper TTS service (no HTTP server needed)
try:
    from .piper_tts_service import PiperTTSService
except Exception as exc:
    PiperTTSService = None
    print("PiperTTSService unavailable:", exc)

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Air-Gapped Voice Pipeline Server")

# Global services
stt_service = None
tts_service = None
context_aggregator = None
transport = None

def create_pipeline():
    """Create and return initialized services."""
    global stt_service, tts_service, context_aggregator

    # Use Cerebrium's get_secret for accessing secrets in deployment
    hf_token = get_secret("HF_TOKEN")
    
    # Debug: Print if HF token is available
    if hf_token:
        print(f"✅ Hugging Face token found (length: {len(hf_token)})")
    else:
        print("⚠️  HF_TOKEN not found in Cerebrium secrets")
        print("The Ultravox STT service will not be available")
    
    # Configure for GPU deployment (Cerebrium A10)
    # Force CUDA for Cerebrium deployment
    if os.environ.get("CUDA_VISIBLE_DEVICES") or os.environ.get("NVIDIA_VISIBLE_DEVICES"):
        # Running on GPU - configure for CUDA
        os.environ["CUDA_VISIBLE_DEVICES"] = os.environ.get("CUDA_VISIBLE_DEVICES", "0")
        print("🖥️  GPU detected - configuring for CUDA")
    else:
        # Check if we're on Cerebrium (they provide GPUs)
        if os.environ.get("CEREBRIUM_ENV") or os.path.exists("/usr/local/cuda"):
            os.environ["CUDA_VISIBLE_DEVICES"] = "0"
            print("🖥️  Cerebrium environment detected - configuring for CUDA")
        else:
            # Running on CPU (fallback)
            os.environ["VLLM_CPU_ONLY"] = "1"
            os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
            print("💻 No GPU detected - configuring for CPU")

    # Initialize Ultravox STT service (handles both STT and LLM)
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
    
    # Initialize context aggregator for proper conversation flow
    context_aggregator = OpenAILLMContext()
    
    # Initialize TTS service globally
    if PiperTTSService:
        try:
            model_name = get_secret("PIPER_MODEL") or "en_US-lessac-medium"
            tts_service = PiperTTSService(
                model_name=model_name,
                sample_rate=16000  # Match audio pipeline sample rate
            )
            print(f"✅ Global Piper TTS service initialized with model: {model_name}")
        except Exception as e:
            print(f"❌ Failed to initialize global Piper TTS service: {e}")
            import traceback
            traceback.print_exc()
            tts_service = None

    return stt_service, tts_service, context_aggregator

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
    """WebSocket endpoint for audio processing using proper Pipecat pipeline."""
    
    # Accept the WebSocket connection first!
    await websocket.accept()
    print("✅ WebSocket connection accepted")
    
    # Import our simple serializer
    try:
        from .protobuf_serializer import SimpleProtobufSerializer
    except ImportError:
        from protobuf_serializer import SimpleProtobufSerializer
    
    try:
        # Create transport for this WebSocket connection
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
        print("✅ Transport created")

        # Build the pipeline
        pipeline_components = [transport.input()]
        
        if stt_service:
            pipeline_components.extend([
                context_aggregator.user(),
                stt_service,  # Ultravox handles both STT and LLM
            ])
        else:
            print("⚠️  STT service not available")
        
        if tts_service:
            pipeline_components.extend([
                tts_service,
                context_aggregator.assistant(),
            ])
        else:
            print("⚠️  TTS service not available")
        
        pipeline_components.append(transport.output())
        
        # Create and run pipeline
        pipeline = Pipeline(pipeline_components)
        print(f"✅ Pipeline created with {len(pipeline_components)} components")
        
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
                enable_usage_metrics=True,
            ),
        )
        
        runner = PipelineRunner()
        
        try:
            print("🚀 Starting Pipecat pipeline...")
            await runner.run(task)
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        print(f"❌ WebSocket endpoint error: {e}")
        import traceback
        traceback.print_exc()
        # Try to close the WebSocket gracefully
        try:
            await websocket.close()
        except:
            pass
    finally:
        # Clean up
        print("🔌 Pipeline connection closed")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global stt_service, tts_service, context_aggregator
    
    print("🚀 Initializing air-gapped voice pipeline services...")
    stt_service, tts_service, context_aggregator = create_pipeline()
    
    if stt_service:
        print("✅ STT service ready")
    else:
        print("❌ STT service not available - check HF_TOKEN")
    
    if tts_service:
        print("✅ TTS service ready")
    else:
        print("❌ TTS service not available")
        
    print("🎯 Air-gapped voice pipeline ready for connections!")
    print("🔍 Debug - Global services initialized")

async def run_server(services=None, host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the FastAPI server with WebSocket support."""
    print(f"🌐 Starting air-gapped server on {host}:{port}")
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(run_server())
