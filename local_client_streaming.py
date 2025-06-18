#!/usr/bin/env python3
"""
Continuous streaming client for Pipecat voice pipeline.
Sends continuous audio and lets VAD handle speech detection.
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
import threading
import queue

# Configuration
WS_SERVER = os.environ.get("WS_SERVER", "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws")
SAMPLE_RATE = 16000
CHUNK_DURATION_SEC = 0.02  # 20ms chunks for smoother streaming
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_SEC)

# Global flag for graceful shutdown
shutdown_flag = threading.Event()
audio_queue = queue.Queue()

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\n🛑 Stopping audio stream...")
    shutdown_flag.set()

def audio_callback(indata, frames, time_info, status):
    """Callback for continuous audio capture."""
    if status:
        print(f"⚠️  Audio status: {status}")
    if not shutdown_flag.is_set():
        # Put audio data in queue
        audio_queue.put(indata.copy())

async def audio_sender(ws):
    """Continuously send audio from the queue to WebSocket."""
    print("🎤 Starting audio streaming...")
    
    # Send initial start frame
    start_msg = json.dumps({"type": "start"})
    await ws.send(start_msg)
    
    while not shutdown_flag.is_set():
        try:
            # Get audio from queue (non-blocking with timeout)
            audio_data = audio_queue.get(timeout=0.1)
            
            # Convert to bytes and send
            audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
            
            # Send as Pipecat audio frame
            audio_msg = json.dumps({
                "type": "audio",
                "data": base64.b64encode(audio_bytes).decode('utf-8'),
                "sample_rate": SAMPLE_RATE,
                "num_channels": 1
            })
            await ws.send(audio_msg)
            
        except queue.Empty:
            # No audio available, continue
            await asyncio.sleep(0.01)
        except Exception as e:
            if not shutdown_flag.is_set():
                print(f"⚠️  Error sending audio: {e}")
            break

async def response_receiver(ws):
    """Receive and handle responses from the server."""
    print("👂 Listening for responses...")
    
    while not shutdown_flag.is_set():
        try:
            response = await ws.recv()
            
            # Handle different response types
            if isinstance(response, str):
                try:
                    msg = json.loads(response)
                    msg_type = msg.get("type", "")
                    
                    if msg_type == "audio":
                        # Decode and play audio
                        audio_data = base64.b64decode(msg["data"])
                        audio_array = np.frombuffer(audio_data, dtype=np.int16)
                        sample_rate = msg.get("sample_rate", SAMPLE_RATE)
                        
                        # Play audio
                        sd.play(audio_array, samplerate=sample_rate)
                        print("🔊 Playing AI response...")
                        
                    elif msg_type == "transcription":
                        print(f"📝 Transcription: {msg.get('text', '')}")
                        
                    elif msg_type == "text":
                        print(f"💬 Message: {msg.get('text', '')}")
                        
                    elif msg_type in ["bot_started_speaking", "BotStartedSpeakingFrame"]:
                        print("🤖 AI is speaking...")
                        
                    elif msg_type in ["bot_stopped_speaking", "BotStoppedSpeakingFrame"]:
                        print("✨ AI finished speaking")
                        
                except json.JSONDecodeError:
                    print(f"📝 Server message: {response}")
                    
            elif isinstance(response, bytes):
                # Raw audio bytes
                audio_array = np.frombuffer(response, dtype=np.int16)
                sd.play(audio_array, samplerate=SAMPLE_RATE)
                
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed")
            break
        except Exception as e:
            if not shutdown_flag.is_set():
                print(f"⚠️  Error receiving response: {e}")
            break

async def stream_audio():
    """Main streaming function."""
    print(f"🔗 Connecting to {WS_SERVER}")
    
    try:
        async with websockets.connect(
            WS_SERVER,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10
        ) as ws:
            print("✅ Connected to voice pipeline!")
            print("🎙️  Speak naturally - the AI will detect when you stop talking")
            print("     Press Ctrl+C to stop.")
            print()
            
            # Start audio capture with callback
            stream = sd.InputStream(
                callback=audio_callback,
                channels=1,
                samplerate=SAMPLE_RATE,
                blocksize=CHUNK_SIZE,
                dtype='float32'
            )
            
            with stream:
                # Create tasks for sending and receiving
                sender_task = asyncio.create_task(audio_sender(ws))
                receiver_task = asyncio.create_task(response_receiver(ws))
                
                # Wait for either task to complete or shutdown
                done, pending = await asyncio.wait(
                    [sender_task, receiver_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cancel remaining tasks
                for task in pending:
                    task.cancel()
                    
            # Send cancel frame on exit
            if not ws.closed:
                cancel_msg = json.dumps({"type": "cancel"})
                await ws.send(cancel_msg)
                
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

def main():
    """Main entry point."""
    print("🎯 Voice Pipeline Streaming Client")
    print("=" * 50)
    print("⚡ Continuous audio streaming with VAD detection")
    print("   The AI will automatically detect when you stop speaking")
    print()
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        asyncio.run(stream_audio())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    finally:
        shutdown_flag.set()

if __name__ == "__main__":
    main() 