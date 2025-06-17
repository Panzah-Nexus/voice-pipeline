"""WebSocket server that streams audio through the Pipecat pipeline."""
from __future__ import annotations

import asyncio
import websockets

from .pipecat_pipeline import create_pipeline


async def process_connection(ws: websockets.WebSocketServerProtocol):
    """Handle a single websocket connection."""
    pipeline = create_pipeline()
    async for message in ws:
        # `message` contains raw PCM audio from the client
        # In a real implementation we would convert this into frames that
        # UltravoxSTTService expects. Here we simply echo the bytes back as a
        # placeholder.
        # TODO: integrate pipecat pipeline processing
        await ws.send(message)


async def main() -> None:
    async with websockets.serve(process_connection, "0.0.0.0", 8000):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
