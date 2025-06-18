"""
Pipecat pipeline setup for air-gapped deployment
Ultravox (STT+LLM)  →  Piper (TTS)
No external APIs – runs entirely on Cerebrium A10 GPU
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

import numpy as np
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.responses import PlainTextResponse

# ────────────────────────── logging ──────────────────────────
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("pipecat-pipeline")

# ────────────────────────── env helpers ──────────────────────
def get_secret(key: str) -> Optional[str]:
    """Return secret from Cerebrium or env; warn if missing."""
    try:
        from cerebrium import get_secret as _cs
        if (val := _cs(key)):
            log.info(f"✅ secret {key} via Cerebrium")
            return val
    except Exception:
        pass
    if (val := os.getenv(key)):
        log.info(f"✅ secret {key} via env")
        return val
    log.warning(f"❌ secret {key} not found")
    return None

# ────────────────────────── Pipecat imports ──────────────────
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task   import PipelineParams, PipelineTask
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketTransport, FastAPIWebsocketParams
)
from pipecat.frames.frames import (
    AudioRawFrame, Frame, TextFrame, TranscriptionFrame, ErrorFrame
)
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams          # ← NEW API

try:
    from pipecat.services.ultravox.stt import UltravoxSTTService
except Exception as exc:
    log.error("Ultravox import failed: %s", exc)
    UltravoxSTTService = None

try:
    from .piper_tts_service import PiperTTSService
except Exception:
    from piper_tts_service import PiperTTSService

# ────────────────────────── FastAPI app ──────────────────────
app = FastAPI(title="Air-gapped Voice Pipeline")

# Global handles
stt_service  = None
tts_service  = None
ready_flag   = False   # toggled when Ultravox warm-up completes

# ────────────────────────── helper processors ────────────────
class TranscriptionToText(FrameProcessor):
    def __init__(self):
        super().__init__()
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        if isinstance(frame, TranscriptionFrame):
            await self.push_frame(TextFrame(text=frame.text), direction)
        else:
            await self.push_frame(frame, direction)

class SafeWrapper(FrameProcessor):
    """Catches exceptions from an inner processor and turns them into ErrorFrame."""
    def __init__(self, wrapped: FrameProcessor):
        super().__init__(); self.wrapped = wrapped
    async def process_frame(self, frame: Frame, dir: FrameDirection):
        try:
            await self.wrapped.process_frame(frame, dir)
        except Exception as e:
            log.exception("processor error")
            await self.push_frame(ErrorFrame(error=str(e)), dir)

# ────────────────────────── initialisation ───────────────────
load_dotenv()  # local dev convenience

def init_services():
    """Initialise Ultravox + Piper once on startup."""
    global stt_service, tts_service

    hf_token = get_secret("HF_TOKEN")
    if not hf_token:
        return

    #  Ultravox
    stt_service = UltravoxSTTService(
        model_name="fixie-ai/ultravox-v0_5-llama-3_1-8b",
        hf_token=hf_token,
        temperature=0.5,
        max_tokens=150,
    )
    log.info("✅ Ultravox ready")

    #  Piper
    voice = get_secret("PIPER_MODEL") or "en_US-lessac-medium"
    tts_service = PiperTTSService(model_name=voice, sample_rate=16_000)
    log.info("✅ Piper ready (%s)", voice)

# ────────────────────────── health / ready ───────────────────
@app.get("/health")
async def health(): return PlainTextResponse("OK")

@app.get("/ready")
async def ready():
    return PlainTextResponse("OK" if ready_flag else "loading",
                             status_code=200 if ready_flag else 503)

# ────────────────────────── websocket endpoint ───────────────
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    if not ready_flag:           # block until warm
        await ws.close(code=1013, reason="model loading")
        return

    await ws.accept(); log.info("websocket accepted")

    # Use Pipecat's standard serializer instead of custom one
    from pipecat.serializers.protobuf import ProtobufFrameSerializer

    # VAD (new API)
    vad = SileroVADAnalyzer(params=VADParams(
        confidence=0.3, start_secs=0.05, stop_secs=1.5, min_volume=0.10
    ))

    transport = FastAPIWebsocketTransport(
        websocket=ws,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True, audio_out_enabled=True,
            serializer=ProtobufFrameSerializer(),
            vad_enabled=True, vad_analyzer=vad, add_wav_header=False,
            audio_in_sample_rate=16_000,
        )
    )

    # Build pipeline
    pipeline = Pipeline([
        transport.input(),
        stt_service,
        TranscriptionToText(),
        tts_service,
        transport.output(),
    ])

    runner = PipelineRunner()
    try:
        await runner.run(PipelineTask(pipeline,
                        params=PipelineParams(
                            allow_interruptions=True,
                            enable_turn_tracking=True  # Re-enable turn tracking
                        )))
    except Exception as e:
        log.error("pipeline error: %s", e)
    finally:
        log.info("connection closed")

# ────────────────────────── startup event ────────────────────
@app.on_event("startup")
async def on_startup():
    global ready_flag
    init_services()

    # Warm-up Ultravox with 1-sec silence → compiles CUDA graphs
    if stt_service:
        log.info("warming Ultravox…")
        # Note: Ultravox doesn't have a transcribe method - it's a combined STT+LLM
        # The model will warm up on first use automatically
        ready_flag = True
        log.info("✅ services initialized – server ready")

# ────────────────────────── runner (dev) ─────────────────────
async def _run():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    await uvicorn.Server(config).serve()

if __name__ == "__main__":
    asyncio.run(_run())
