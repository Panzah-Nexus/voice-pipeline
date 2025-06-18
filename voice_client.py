#!/usr/bin/env python3
"""
Voice client for Pipecat WebSocket server using protobuf protocol.
"""

import asyncio
import logging
import sys
import queue
from typing import Optional
import sounddevice as sd
import numpy as np
import websockets
import aiohttp

# Install protobuf if needed: pip install protobuf
try:
    import pipecat.frames.protobufs.frames_pb2 as frame_protos
except ImportError:
    print("Please install Pipecat: pip install pipecat-ai")
    sys.exit(1)

# Audio configuration
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.04  # 40ms chunks
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
DEVICE_INDEX = None  # Use default device

# Cerebrium deployment
WS_URL = "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws"
HEALTH_URL = "https://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/health"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VoiceClient:
    def __init__(self):
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.audio_queue = queue.Queue(maxsize=50)
        self.running = False
        
    async def check_health(self) -> bool:
        """Check if the server is healthy."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(HEALTH_URL, timeout=5) as response:
                    if response.status == 200:
                        logger.info("✅ Server health check passed")
                        return True
                    else:
                        logger.error(f"❌ Server returned status {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    def serialize_audio_frame(self, audio_data: bytes) -> bytes:
        """Serialize audio data into Pipecat protobuf format."""
        frame = frame_protos.Frame()
        frame.audio.audio = audio_data
        frame.audio.sample_rate = SAMPLE_RATE
        frame.audio.num_channels = CHANNELS
        return frame.SerializeToString()
    
    def deserialize_frame(self, data: bytes) -> Optional[tuple[str, any]]:
        """Deserialize incoming protobuf frame."""
        try:
            frame = frame_protos.Frame()
            frame.ParseFromString(data)
            
            which = frame.WhichOneof("frame")
            if which == "audio":
                return ("audio", frame.audio.audio)
            elif which == "text":
                return ("text", frame.text.text)
            elif which == "transcription":
                return ("transcription", frame.transcription.text)
            elif which == "message":
                return ("message", frame.message.data)
            else:
                return (which, None)
        except Exception as e:
            logger.error(f"Failed to deserialize frame: {e}")
            return None
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio input - runs in audio thread."""
        if status:
            print(f"Audio status: {status}")
        
        # Convert to 16-bit PCM
        audio_data = (indata * 32767).astype(np.int16).tobytes()
        
        # Check if there's actual sound
        amplitude = np.abs(indata).max()
        if amplitude > 0.01:  # Threshold
            try:
                # Put in queue without blocking
                self.audio_queue.put_nowait(audio_data)
            except queue.Full:
                pass  # Drop frame if queue is full
    
    async def send_audio_task(self):
        """Send audio frames to the server."""
        logger.info("🎤 Starting audio sender...")
        
        try:
            while self.running:
                try:
                    # Get audio with timeout
                    audio_data = self.audio_queue.get(timeout=0.5)
                    
                    # Serialize and send
                    frame_data = self.serialize_audio_frame(audio_data)
                    await self.websocket.send(frame_data)
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Send error: {e}")
                    if not self.running:
                        break
                    
        except Exception as e:
            logger.error(f"Audio sender error: {e}")
    
    async def receive_frames_task(self):
        """Receive and process frames from the server."""
        logger.info("👂 Starting frame receiver...")
        
        try:
            while self.running:
                try:
                    # Receive frame
                    data = await self.websocket.recv()
                    
                    # Deserialize
                    result = self.deserialize_frame(data)
                    if result:
                        frame_type, content = result
                        
                        if frame_type == "audio":
                            # Play audio
                            audio_array = np.frombuffer(content, dtype=np.int16)
                            audio_float = audio_array.astype(np.float32) / 32767.0
                            sd.play(audio_float, SAMPLE_RATE)
                            logger.info("🔊 Playing audio response")
                            
                        elif frame_type == "text":
                            logger.info(f"📝 Text: {content}")
                            
                        elif frame_type == "transcription":
                            logger.info(f"🗣️ You said: {content}")
                            
                        elif frame_type == "message":
                            logger.info(f"💬 Message: {content}")
                            
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("Connection closed")
                    break
                except Exception as e:
                    logger.error(f"Receive error: {e}")
                    if not self.running:
                        break
                        
        except Exception as e:
            logger.error(f"Frame receiver error: {e}")
    
    async def run(self):
        """Run the voice client."""
        # Check health (optional)
        try:
            if not await self.check_health():
                logger.warning("Server health check failed, continuing anyway...")
        except Exception as e:
            logger.warning(f"Health check error: {e}, continuing anyway...")
        
        logger.info(f"🔌 Connecting to WebSocket...")
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                self.websocket = websocket
                self.running = True
                
                logger.info("✅ Connected! Start speaking...")
                logger.info("Press Ctrl+C to stop\n")
                
                # Start audio stream
                stream = sd.InputStream(
                    device=DEVICE_INDEX,
                    channels=CHANNELS,
                    samplerate=SAMPLE_RATE,
                    callback=self.audio_callback,
                    blocksize=CHUNK_SIZE,
                )
                
                with stream:
                    # Run tasks
                    tasks = [
                        self.send_audio_task(),
                        self.receive_frames_task(),
                    ]
                    
                    await asyncio.gather(*tasks)
                    
        except websockets.exceptions.InvalidStatusCode as e:
            logger.error(f"❌ Connection failed: {e}")
        except KeyboardInterrupt:
            logger.info("\n👋 Shutting down...")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
        finally:
            self.running = False
            logger.info("Client stopped")


def list_audio_devices():
    """List available audio devices."""
    print("\n🎤 Available Audio Devices:")
    print("-" * 50)
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        in_ch = device['max_input_channels']
        out_ch = device['max_output_channels']
        print(f"[{i}] {device['name']} - {in_ch} in, {out_ch} out")
    print("-" * 50)


async def main():
    # List devices
    list_audio_devices()
    
    # Run client
    client = VoiceClient()
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
