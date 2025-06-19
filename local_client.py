#!/usr/bin/env python3
"""
Simple raw audio client for voice pipeline.
Connects to Cerebrium deployment and streams raw audio.
"""

"""
Very thin demo client:
* Captures 16-kHz mono mic audio with sounddevice
* Sends raw int16 PCM frames over ws://HOST:PORT/ws
* Plays any binary payloads it receives (no serializer needed)
"""
import asyncio, websockets, sounddevice as sd, numpy as np

URI = "ws://localhost:8000/ws"
SR = 16_000
FRAMES = int(SR * 0.5)               # 0.5 s chunks

async def producer(ws):
    q = asyncio.Queue()
    def _cb(indata, frames, t, status):
        asyncio.get_event_loop().call_soon_threadsafe(q.put_nowait, bytes(indata))
    with sd.InputStream(samplerate=SR, channels=1, dtype="int16",
                        blocksize=FRAMES, callback=_cb):
        while True:
            await ws.send(await q.get())

async def consumer(ws):
    while True:
        data = await ws.recv()        # raw int16 PCM
        sd.play(np.frombuffer(data, np.int16), SR, blocking=False)

async def main():
    async with websockets.connect(URI, ping_interval=None) as ws:
        await asyncio.gather(producer(ws), consumer(ws))

if __name__ == "__main__":
    asyncio.run(main())
