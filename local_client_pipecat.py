#!/usr/bin/env python3
"""
Pipecat-compatible local client for voice pipeline.
Sends audio in the format expected by FastAPIWebsocketTransport.
"""

import asyncio
import os
import websockets
import json
import base64
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

def play_audio_chunk(audio_data: bytes, sample_rate: int = SAMPLE_RATE) -> None:
    """Play a chunk of audio through speakers using sounddevice."""
    try:
        audio = np.frombuffer(audio_data, dtype=np.int16)
        sd.play(audio, samplerate=sample_rate)
        sd.wait()
    except Exception as e:
        print(f"⚠️  Speaker error: {e}")

async def stream_microphone():
    """Capture microphone audio and stream to the WebSocket server."""
    print(f"🔗 Connecting to {WS_SERVER}")
    
    try:
        # Configure WebSocket with proper keepalive settings
        async with websockets.connect(
            WS_SERVER,
            ping_interval=20,  # Send ping every 20 seconds
            ping_timeout=10,   # Wait 10 seconds for pong
            close_timeout=10   # Wait 10 seconds for close
        ) as ws:
            print("✅ Connected to voice pipeline!")
            print("🎙️  Speak into your microphone. Press Ctrl+C to stop.")
            
            # Send start frame
            start_msg = json.dumps({"type": "start"})
            await ws.send(start_msg)
            
            # Start audio capture
            audio_generator = microphone_chunks()
            
            chunk_count = 0
            try:
                for chunk in audio_generator:
                    if shutdown_flag.is_set():
                        break
                        
                    # Send audio chunk as base64-encoded JSON
                    audio_msg = json.dumps({
                        "type": "audio",
                        "data": base64.b64encode(chunk).decode('utf-8'),
                        "sample_rate": SAMPLE_RATE,
                        "num_channels": 1
                    })
                    await ws.send(audio_msg)
                    chunk_count += 1
                    
                    # Every 10 chunks (~5 seconds), send END signal and wait for response
                    if chunk_count >= 10:
                        # Send end frame to trigger processing
                        end_msg = json.dumps({"type": "end"})
                        await ws.send(end_msg)
                        print("🤖 Processing your speech...")
                        
                        # Receive and play audio response
                        try:
                            response_timeout = 60.0  # 60 second timeout for AI processing (cold start)
                            response_received = False
                            print("⏳ Waiting for AI response (may take up to 60s on cold start)...")
                            
                            while True:
                                try:
                                    response = await asyncio.wait_for(ws.recv(), timeout=response_timeout)
                                    
                                    # Handle different response types
                                    if isinstance(response, str):
                                        try:
                                            msg = json.loads(response)
                                            msg_type = msg.get("type", "")
                                            
                                            if msg_type == "audio":
                                                if not response_received:
                                                    print("🔊 Playing AI response...")
                                                    response_received = True
                                                # Decode and play audio
                                                audio_data = base64.b64decode(msg["data"])
                                                sample_rate = msg.get("sample_rate", SAMPLE_RATE)
                                                play_audio_chunk(audio_data, sample_rate)
                                            elif msg_type == "transcription":
                                                print(f"📝 Transcription: {msg.get('text', '')}")
                                            elif msg_type == "text":
                                                print(f"💬 Message: {msg.get('text', '')}")
                                            elif msg_type == "end":
                                                break
                                        except json.JSONDecodeError:
                                            print(f"📝 Server message: {response}")
                                    elif isinstance(response, bytes):
                                        # Raw audio bytes
                                        if not response_received:
                                            print("🔊 Playing AI response...")
                                            response_received = True
                                        play_audio_chunk(response)
                                        
                                except asyncio.TimeoutError:
                                    if not response_received:
                                        print("⏰ No response from server (timeout)")
                                    break
                                    
                        except Exception as e:
                            print(f"⚠️  Error receiving response: {e}")
                        
                        print("✨ Ready for next input. Continue speaking...")
                        chunk_count = 0
                        
                        # Send start frame for next interaction
                        start_msg = json.dumps({"type": "start"})
                        await ws.send(start_msg)
                        
            except KeyboardInterrupt:
                print("\n🛑 Stopping audio stream...")
            except Exception as e:
                print(f"❌ Error during streaming: {e}")
            finally:
                # Send cancel frame on exit
                cancel_msg = json.dumps({"type": "cancel"})
                await ws.send(cancel_msg)
                
    except websockets.exceptions.WebSocketException as e:
        if "connection refused" in str(e).lower():
            print(f"❌ Cannot connect to {WS_SERVER}")
            print("💡 Make sure your Cerebrium deployment is running!")
            print("   Check your deployment URL and try again.")
        else:
            print(f"❌ WebSocket error: {e}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

def main():
    """Main entry point."""
    print("🎯 Voice Pipeline Local Client (Pipecat Protocol)")
    print("=" * 50)
    print("⚡ Note: First response may take 30-60 seconds due to model warmup")
    print("   Subsequent responses will be much faster (~1-2 seconds)")
    print()
    
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