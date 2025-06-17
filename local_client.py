#!/usr/bin/env python3
"""
Standalone local client for voice pipeline.
Connects to remote Cerebrium deployment and streams audio.
"""

import asyncio
import os
import websockets
import signal
import sys
import sounddevice as sd
import numpy as np
from typing import Iterator

# Configuration
WS_SERVER = os.environ.get("WS_SERVER", "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws")
SAMPLE_RATE = 16000
CHUNK_DURATION_SEC = 0.5
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_SEC)

# Global flag for graceful shutdown
shutdown_flag = asyncio.Event()

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\n🛑 Stopping audio stream...")
    shutdown_flag.set()

def microphone_chunks() -> Iterator[bytes]:
    """Yield raw microphone audio chunks using sounddevice."""
    print("🎙️  Opening microphone...")
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=CHUNK_SIZE) as stream:
        print("✅ Microphone ready!")
        while not shutdown_flag.is_set():
            try:
                audio, _ = stream.read(CHUNK_SIZE)
                yield audio.tobytes()
            except Exception as e:
                print(f"⚠️  Microphone error: {e}")
                break

def play_audio_chunk(chunk: bytes) -> None:
    """Play a chunk of audio through speakers using sounddevice."""
    try:
        audio = np.frombuffer(chunk, dtype=np.int16)
        sd.play(audio, samplerate=SAMPLE_RATE)
        sd.wait()
    except Exception as e:
        print(f"⚠️  Speaker error: {e}")

async def stream_microphone():
    """Capture microphone audio and stream to the WebSocket server."""
    print(f"🔗 Connecting to {WS_SERVER}")
    
    try:
        async with websockets.connect(WS_SERVER) as ws:
            print("✅ Connected to voice pipeline!")
            print("🎙️  Speak into your microphone. Press Ctrl+C to stop.")
            
            # Start audio capture
            audio_generator = microphone_chunks()
            
            chunk_count = 0
            try:
                for chunk in audio_generator:
                    if shutdown_flag.is_set():
                        break
                        
                    # Send audio chunk
                    await ws.send(chunk)
                    chunk_count += 1
                    
                    # Every 10 chunks (~5 seconds), send END signal and wait for response
                    if chunk_count >= 10:
                        await ws.send("END")
                        print("🤖 Processing your speech...")
                        
                        # Receive and play audio response
                        try:
                            response_timeout = 10.0  # 10 second timeout for AI processing
                            response_received = False
                            
                            while True:
                                try:
                                    response = await asyncio.wait_for(ws.recv(), timeout=response_timeout)
                                    if isinstance(response, bytes) and len(response) > 0:
                                        if not response_received:
                                            print("🔊 Playing AI response...")
                                            response_received = True
                                        play_audio_chunk(response)
                                    else:
                                        # Text message or empty response
                                        if isinstance(response, str):
                                            print(f"📝 Server message: {response}")
                                        break
                                except asyncio.TimeoutError:
                                    if not response_received:
                                        print("⏰ No response from server (timeout)")
                                    break
                                    
                        except Exception as e:
                            print(f"⚠️  Error receiving response: {e}")
                        
                        print("✨ Ready for next input. Continue speaking...")
                        chunk_count = 0
                        
            except KeyboardInterrupt:
                print("\n🛑 Stopping audio stream...")
            except Exception as e:
                print(f"❌ Error during streaming: {e}")
                
    except websockets.exceptions.ConnectionRefused:
        print(f"❌ Cannot connect to {WS_SERVER}")
        print("💡 Make sure your Cerebrium deployment is running!")
        print("   Check your deployment URL and try again.")
    except Exception as e:
        print(f"❌ Connection error: {e}")

def main():
    """Main entry point."""
    print("🎯 Voice Pipeline Local Client")
    print("=" * 40)
    
    # Check if server URL is configured
    if WS_SERVER.startswith("ws://localhost"):
        print("⚠️  Using localhost server. For Cerebrium deployment, set:")
        print("   export WS_SERVER='wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws'")
        print()
    else:
        print(f"🌐 Connecting to: {WS_SERVER}")
        print()
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        asyncio.run(stream_microphone())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 