"""WebSocket client for streaming microphone audio to the server."""
from __future__ import annotations

import asyncio
import os
import websockets

from . import audio_utils

WS_SERVER = os.environ.get("WS_SERVER", "ws://localhost:8000")


async def stream_microphone():
    """Capture microphone audio and stream to the WebSocket server."""
    async with websockets.connect(WS_SERVER) as ws:
        for chunk in audio_utils.microphone_chunks():
            await ws.send(chunk)
            response = await ws.recv()
            audio_utils.play_audio_chunk(response)


def main() -> None:
    asyncio.run(stream_microphone())


if __name__ == "__main__":
    main()
