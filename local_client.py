#!/usr/bin/env python3
"""
Simple raw audio client for voice pipeline.
Connects to Cerebrium deployment and streams raw audio.
"""

import asyncio
import json
import logging
import os
import struct
import sys
import time
from typing import Optional

import numpy as np
import sounddevice as sd
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Audio configuration
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.1  # 100ms chunks
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
DTYPE = np.int16


class VoicePipelineClient:
    """WebSocket client for voice pipeline."""
    
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.websocket = None
        self.audio_queue = asyncio.Queue()
        self.is_running = False
        self.output_stream = None
        
    async def connect(self):
        """Connect to WebSocket server."""
        logger.info(f"Connecting to {self.ws_url}")
        self.websocket = await websockets.connect(self.ws_url)
        logger.info("Connected to voice pipeline!")
        
    async def disconnect(self):
        """Disconnect from WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from voice pipeline")
            
    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio input stream."""
        if status:
            logger.warning(f"Audio input status: {status}")
        
        # Put audio data in queue
        try:
            self.audio_queue.put_nowait(indata.copy())
        except asyncio.QueueFull:
            logger.warning("Audio queue full, dropping frame")
            
    async def send_audio(self):
        """Send audio from microphone to server."""
        logger.info("Starting audio capture...")
        
        # Open microphone stream
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=self.audio_callback,
            blocksize=CHUNK_SIZE
        ):
            while self.is_running:
                try:
                    # Get audio from queue
                    audio_data = await self.audio_queue.get()
                    
                    # Prepare message
                    message = {
                        "type": "audio",
                        "data": audio_data.tobytes().hex(),
                        "sample_rate": SAMPLE_RATE,
                        "channels": CHANNELS
                    }
                    
                    # Send to server
                    await self.websocket.send(json.dumps(message))
                    
                except Exception as e:
                    logger.error(f"Error sending audio: {e}")
                    break
                    
    async def receive_audio(self):
        """Receive and play audio from server."""
        logger.info("Ready to receive audio...")
        
        # Open speaker stream
        self.output_stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE
        )
        self.output_stream.start()
        
        try:
            while self.is_running:
                try:
                    # Receive message
                    message = await self.websocket.recv()
                    
                    # Parse message
                    if isinstance(message, str):
                        data = json.loads(message)
                        
                        if data.get("type") == "audio":
                            # Decode audio data
                            audio_bytes = bytes.fromhex(data["data"])
                            audio_data = np.frombuffer(audio_bytes, dtype=DTYPE)
                            
                            # Play audio
                            self.output_stream.write(audio_data)
                            
                        elif data.get("type") == "transcript":
                            logger.info(f"Transcript: {data.get('text', '')}")
                            
                        elif data.get("type") == "message":
                            logger.info(f"Message: {data.get('message', '')}")
                            
                    else:
                        # Binary message (raw audio)
                        audio_data = np.frombuffer(message, dtype=DTYPE)
                        self.output_stream.write(audio_data)
                        
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Connection closed by server")
                    break
                except Exception as e:
                    logger.error(f"Error receiving audio: {e}")
                    
        finally:
            if self.output_stream:
                self.output_stream.stop()
                self.output_stream.close()
                
    async def run(self):
        """Run the voice pipeline client."""
        try:
            await self.connect()
            self.is_running = True
            
            # Start send and receive tasks
            send_task = asyncio.create_task(self.send_audio())
            receive_task = asyncio.create_task(self.receive_audio())
            
            # Wait for tasks
            await asyncio.gather(send_task, receive_task)
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Client error: {e}")
        finally:
            self.is_running = False
            await self.disconnect()


def main():
    """Main entry point."""
    print("🎯 Voice Pipeline Local Client")
    print("=" * 40)
    
    # Get WebSocket URL
    ws_url = os.environ.get("WS_SERVER")
    if not ws_url:
        print("❌ Error: WS_SERVER environment variable not set!")
        print("Please set: export WS_SERVER='wss://your-deployment.cerebrium.app/ws'")
        sys.exit(1)
        
    print(f"🔗 Server: {ws_url}")
    print("🎙️ Speak into your microphone. Press Ctrl+C to stop.")
    print()
    
    # Check audio devices
    try:
        devices = sd.query_devices()
        logger.info(f"Default input device: {sd.query_devices(kind='input')['name']}")
        logger.info(f"Default output device: {sd.query_devices(kind='output')['name']}")
    except Exception as e:
        logger.error(f"Audio device error: {e}")
        print("❌ Error: Could not access audio devices!")
        print("Make sure you have a microphone and speakers connected.")
        sys.exit(1)
    
    # Create and run client
    client = VoicePipelineClient(ws_url)
    
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()

