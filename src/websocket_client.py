"""WebSocket client for streaming microphone audio to the server."""
from __future__ import annotations

import asyncio
import os
import websockets
# import json  # Not used in this file
import signal
import sys

from . import audio_utils

WS_SERVER = os.environ.get("WS_SERVER", "ws://localhost:8000/ws")

# Global flag for graceful shutdown
shutdown_flag = asyncio.Event()

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\n🛑 Stopping audio stream...")
    shutdown_flag.set()

async def stream_microphone():
    """Capture microphone audio and stream to the WebSocket server."""
    print(f"🔗 Connecting to {WS_SERVER}")
    
    try:
        async with websockets.connect(WS_SERVER) as ws:
            print("✅ Connected! Starting audio streaming...")
            print("🎙️  Speak into your microphone. Press Ctrl+C to stop.")
            
            # Start audio capture in background
            audio_generator = audio_utils.microphone_chunks()
            
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
                        print("🔄 Processing audio...")
                        
                        # Receive and play audio response chunks
                        try:
                            response_timeout = 5.0  # 5 second timeout
                            while True:
                                try:
                                    response = await asyncio.wait_for(ws.recv(), timeout=response_timeout)
                                    if isinstance(response, bytes) and len(response) > 0:
                                        audio_utils.play_audio_chunk(response)
                                        print("🔊 Playing response...")
                                    else:
                                        # If we get a text message or empty response, break
                                        break
                                except asyncio.TimeoutError:
                                    # No more audio chunks coming
                                    break
                                    
                        except Exception as e:
                            print(f"⚠️  Error receiving response: {e}")
                        
                        print("✨ Response complete. Continue speaking...")
                        chunk_count = 0
                        
            except KeyboardInterrupt:
                print("\n🛑 Stopping audio stream...")
            except Exception as e:
                print(f"❌ Error during streaming: {e}")
                
    except websockets.exceptions.ConnectionRefused:
        print(f"❌ Cannot connect to {WS_SERVER}")
        print("💡 Make sure the server is running:")
        print("   python -m src.main")
        print("   or")
        print("   python -m src.simple_test_server")
    except Exception as e:
        print(f"❌ Connection error: {e}")


def main() -> None:
    """Main entry point with signal handling."""
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
