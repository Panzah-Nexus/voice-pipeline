#!/usr/bin/env python3
"""
Simple raw audio client for voice pipeline.
Connects to Cerebrium deployment and streams raw audio.
"""

import asyncio
import os
import sys
import json
import numpy as np
import sounddevice as sd
import websockets
import aiohttp
from typing import Optional
import logging
import struct

# Configuration
WS_SERVER = os.environ.get("WS_SERVER", "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws")
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.02  # 20ms chunks
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RawAudioClient:
    def __init__(self):
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        self.audio_queue = asyncio.Queue(maxsize=100)
        
    async def check_health(self) -> bool:
        """Check if the server is healthy."""
        health_url = WS_SERVER.replace("wss://", "https://").replace("/ws", "/health")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=5) as response:
                    if response.status == 200:
                        logger.info("✅ Server health check passed")
                        return True
                    else:
                        logger.error(f"❌ Server returned status {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio input stream."""
        if status:
            logger.warning(f"Audio status: {status}")
        
        # Convert to 16-bit PCM
        audio_data = (indata * 32767).astype(np.int16).tobytes()
        
        # Put in queue without blocking
        try:
            self.audio_queue.put_nowait(audio_data)
        except asyncio.QueueFull:
            pass  # Drop frame if queue is full
    
    async def send_audio_task(self):
        """Send audio frames to the server."""
        logger.info("🎤 Starting audio sender...")
        
        while self.running:
            try:
                # Get audio from queue
                audio_data = await asyncio.wait_for(self.audio_queue.get(), timeout=0.1)
                
                # Send raw audio bytes
                await self.websocket.send(audio_data)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Send error: {e}")
                break
    
    async def receive_audio_task(self):
        """Receive and play audio from the server."""
        logger.info("🔊 Starting audio receiver...")
        
        while self.running:
            try:
                # Receive data
                data = await self.websocket.recv()
                
                if isinstance(data, bytes) and len(data) > 0:
                    # Assume it's raw audio and play it
                    try:
                        audio_array = np.frombuffer(data, dtype=np.int16)
                        audio_float = audio_array.astype(np.float32) / 32767.0
                        sd.play(audio_float, SAMPLE_RATE)
                    except Exception as e:
                        logger.debug(f"Audio playback error: {e}")
                        
                elif isinstance(data, str):
                    # Log text messages
                    logger.info(f"📝 Server message: {data}")
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed")
                break
            except Exception as e:
                if self.running:
                    logger.error(f"Receive error: {e}")
                break
    
    async def run(self):
        """Run the voice client."""
        # Optional health check
        await self.check_health()
        
        logger.info(f"🔌 Connecting to {WS_SERVER}...")
        
        try:
            async with websockets.connect(WS_SERVER) as websocket:
                self.websocket = websocket
                self.running = True
                
                logger.info("✅ Connected! Start speaking...")
                logger.info("Press Ctrl+C to stop\n")
                
                # Start audio input stream
                stream = sd.InputStream(
                    channels=CHANNELS,
                    samplerate=SAMPLE_RATE,
                    callback=self.audio_callback,
                    blocksize=CHUNK_SIZE,
                    dtype='float32'
                )
                
                with stream:
                    # Run send and receive tasks
                    tasks = [
                        asyncio.create_task(self.send_audio_task()),
                        asyncio.create_task(self.receive_audio_task()),
                    ]
                    
                    try:
                        await asyncio.gather(*tasks)
                    except KeyboardInterrupt:
                        logger.info("\n👋 Shutting down...")
                        
        except websockets.exceptions.InvalidStatusCode as e:
            logger.error(f"❌ Connection failed: {e}")
            logger.error("The server might be expecting a different protocol.")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
        finally:
            self.running = False
            logger.info("Client stopped")

def main():
    """Main entry point."""
    print("🎯 Raw Audio Voice Pipeline Client")
    print("=" * 40)
    
    if WS_SERVER.startswith("ws://localhost"):
        print("⚠️  Using localhost server. For Cerebrium deployment, set:")
        print("   export WS_SERVER='wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws'")
        print()
    else:
        print(f"🌐 Server: {WS_SERVER}")
        print()
    
    # List audio devices
    print("🎤 Available Audio Devices:")
    print("-" * 50)
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"  [{i}] {device['name']} (inputs: {device['max_input_channels']})")
    print()
    
    try:
        client = RawAudioClient()
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 