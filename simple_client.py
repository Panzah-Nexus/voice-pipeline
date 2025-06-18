#!/usr/bin/env python3
"""
Simple voice pipeline client that sends raw audio bytes.
Works with the simplified server.
"""

import asyncio
import os
import websockets
import signal
import sys
import sounddevice as sd
import numpy as np

# Configuration
WS_SERVER = os.environ.get("WS_SERVER", "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws")
SAMPLE_RATE = 16000
CHUNK_DURATION_SEC = 0.5
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_SEC)

# Global flag
shutdown_flag = asyncio.Event()

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\n🛑 Stopping...")
    shutdown_flag.set()

async def audio_streamer():
    """Stream audio to/from server."""
    print(f"🔗 Connecting to {WS_SERVER}")
    
    try:
        async with websockets.connect(WS_SERVER) as websocket:
            print("✅ Connected!")
            print("🎙️  Speak into your microphone (the AI will detect when you stop)")
            print("     Press Ctrl+C to exit.")
            print()
            
            # Create tasks for sending and receiving
            async def send_audio():
                """Send microphone audio to server."""
                with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=CHUNK_SIZE) as stream:
                    while not shutdown_flag.is_set():
                        try:
                            audio, _ = stream.read(CHUNK_SIZE)
                            await websocket.send(audio.tobytes())
                        except Exception as e:
                            if not shutdown_flag.is_set():
                                print(f"⚠️  Send error: {e}")
                            break
            
            async def receive_audio():
                """Receive and play audio from server."""
                while not shutdown_flag.is_set():
                    try:
                        data = await websocket.recv()
                        if isinstance(data, bytes) and len(data) > 0:
                            # Play received audio
                            audio = np.frombuffer(data, dtype=np.int16)
                            sd.play(audio, samplerate=SAMPLE_RATE)
                            print("🔊 Playing AI response...")
                    except websockets.exceptions.ConnectionClosed:
                        break
                    except Exception as e:
                        if not shutdown_flag.is_set():
                            print(f"⚠️  Receive error: {e}")
                        break
            
            # Run both tasks concurrently
            send_task = asyncio.create_task(send_audio())
            receive_task = asyncio.create_task(receive_audio())
            
            # Wait for either to complete
            done, pending = await asyncio.wait(
                [send_task, receive_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                
    except Exception as e:
        print(f"❌ Connection error: {e}")

def main():
    """Main entry point."""
    print("🎯 Simple Voice Pipeline Client")
    print("=" * 40)
    print("📌 Raw audio streaming - no complex protocols")
    print()
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        asyncio.run(audio_streamer())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main() 