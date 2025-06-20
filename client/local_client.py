#!/usr/bin/env python3
"""
Voice pipeline client using Pipecat ProtobufFrameSerializer.
Connects to Cerebrium deployment and streams audio.
"""

import asyncio
import logging
import os
import sys

import numpy as np
import sounddevice as sd
import websockets

# Simple binary serializer implementation for client
import struct

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Audio configuration
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.02  # 20ms chunks
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
DTYPE = np.int16


class VoicePipelineClient:
    """WebSocket client for voice pipeline using simple binary format."""
    
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
                    
                    # Create binary audio frame using our simple format
                    # Format: type_id(4), sample_rate(4), channels(4), length(4), audio_data
                    audio_bytes = audio_data.tobytes()
                    header = struct.pack(
                        '>IIII',  # Big-endian, 4 unsigned ints
                        1,  # AUDIO_RAW_FRAME_ID
                        SAMPLE_RATE,
                        CHANNELS,
                        len(audio_bytes)
                    )
                    
                    serialized = header + audio_bytes
                    await self.websocket.send(serialized)
                    
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
                    # Receive message (binary)
                    message = await self.websocket.recv()
                    
                    # Deserialize binary audio frame
                    if len(message) >= 16:  # Minimum header size
                        try:
                            # Unpack header
                            frame_type, sample_rate, num_channels, audio_length = struct.unpack('>IIII', message[:16])
                            
                            if frame_type == 1 and len(message) >= 16 + audio_length:  # AudioRawFrame
                                # Extract audio data
                                audio_bytes = message[16:16 + audio_length]
                                
                                # Convert to numpy array and play
                                audio_data = np.frombuffer(audio_bytes, dtype=DTYPE)
                                self.output_stream.write(audio_data)
                            else:
                                logger.debug(f"Received non-audio frame or incomplete data")
                        except Exception as e:
                            logger.error(f"Error processing received audio: {e}")
                    else:
                        logger.debug(f"Received message too small: {len(message)} bytes")
                        
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Connection closed by server")
                    break
                except Exception as e:
                    logger.error(f"Error receiving: {e}")
                    
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
    # Enable tracemalloc for debugging
    import tracemalloc
    tracemalloc.start()
    
    print("🎯 Voice Pipeline Local Client")
    print("=" * 40)
    
    # Default URL for your deployment
    DEFAULT_WS_URL = "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws"
    
    # Get WebSocket URL (use environment variable or default)
    ws_url = os.environ.get("WS_SERVER", DEFAULT_WS_URL)
    if ws_url == DEFAULT_WS_URL:
        print(f"📌 Using default server URL")
    else:
        print(f"📌 Using custom server from WS_SERVER env var")
        
    print(f"🔗 Server: {ws_url}")
    print(f"📡 Using simple binary audio serializer")
    print("🎙️ Speak into your microphone. Press Ctrl+C to stop.")
    print()
    
    # Check audio devices
    try:
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

