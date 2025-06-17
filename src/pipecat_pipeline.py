"""Pipecat pipeline setup.

This module configures Pipecat with Ultravox for both speech recognition and
language generation, plus an external TTS service for audio synthesis.
"""
from __future__ import annotations


import os
from dotenv import load_dotenv
from pipecat import Pipeline

try:
    from pipecat.services.ultravox import UltravoxSTTService
except Exception as exc:  # pragma: no cover - optional dependency
    UltravoxSTTService = None
    print("UltravoxSTTService unavailable:", exc)

try:
    from pipecat.services.openai.tts import OpenAITTSService
except Exception as exc:  # pragma: no cover - optional dependency
    OpenAITTSService = None
    print("OpenAI TTS service unavailable:", exc)

try:
    from pipecat.services.piper.tts import PiperTTSService
    import aiohttp
except Exception as exc:  # pragma: no cover - optional dependency
    PiperTTSService = None
    aiohttp = None
    print("Piper TTS service unavailable:", exc)

# Load environment variables from .env file
load_dotenv()

def create_pipeline():
    """Create and return initialized STT and TTS services."""

    hf_token = os.environ.get("HUGGING_FACE_TOKEN")

    stt = None
    if UltravoxSTTService:
        stt = UltravoxSTTService(
            model_size="1b",
            hf_token=hf_token,
            temperature=0.5,
            max_tokens=150,
        )

    tts = None
    if os.environ.get("PIPER_BASE_URL") and PiperTTSService:
        session = aiohttp.ClientSession()
        tts = PiperTTSService(
            base_url=os.environ["PIPER_BASE_URL"],
            aiohttp_session=session,
            sample_rate=(
                int(os.environ["PIPER_SAMPLE_RATE"])
                if os.environ.get("PIPER_SAMPLE_RATE")
                else None
            ),
        )
    elif OpenAITTSService:
        tts = OpenAITTSService(
            api_key=os.environ.get("OPENAI_API_KEY"),
            voice=os.environ.get("OPENAI_TTS_VOICE", "nova"),
            model=os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        )

    return stt, tts


async def run_server(services, host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run a simple WebSocket server that processes audio through Ultravox and TTS."""
    stt, tts = services
    import asyncio
    import websockets
    import numpy as np
    import json

    async def handler(ws):
        audio_buffer = bytearray()
        async for message in ws:
            if isinstance(message, bytes):
                audio_buffer.extend(message)
                continue
            if message == "END":
                if not stt or not tts:
                    await ws.send(bytes(audio_buffer))
                    audio_buffer.clear()
                    continue

                audio = np.frombuffer(bytes(audio_buffer), dtype=np.int16).astype(np.float32) / 32768.0
                text_parts = []
                async for chunk in stt._model.generate(
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

                async for frame in tts.run_tts(text):
                    if hasattr(frame, "audio"):
                        await ws.send(frame.audio)

                audio_buffer.clear()

    async with websockets.serve(handler, host, port):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    services = create_pipeline()
    import asyncio
    asyncio.run(run_server(services))
