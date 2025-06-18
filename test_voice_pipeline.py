#!/usr/bin/env python3
"""Test the deployed voice pipeline with proper Pipecat protocol."""

import asyncio
import websockets
import json
import numpy as np
import sounddevice as sd
import base64
import struct
import time

async def test_pipeline():
    """Test the voice pipeline with proper Pipecat frames."""
    
    # Get the WebSocket URL
    ws_url = "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws"
    
    print(f"🔗 Connecting to: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected to voice pipeline!")
            
            # Send a start frame
            start_frame = {
                "type": "start",
                "timestamp": time.time()
            }
            await websocket.send(json.dumps(start_frame))
            print("📤 Sent start frame")
            
            # Create test audio (5 seconds of sine wave)
            sample_rate = 16000
            duration = 5.0
            frequency = 440  # A4 note
            
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio = (0.3 * np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
            
            print("🎵 Sending test audio (5 seconds of 440Hz tone)...")
            
            # Send audio in chunks
            chunk_size = int(sample_rate * 0.1)  # 100ms chunks
            for i in range(0, len(audio), chunk_size):
                chunk = audio[i:i + chunk_size]
                
                # Create audio frame following Pipecat protocol
                audio_frame = {
                    "type": "audio",
                    "data": base64.b64encode(chunk.tobytes()).decode('utf-8'),
                    "sample_rate": sample_rate,
                    "channels": 1,
                    "timestamp": time.time()
                }
                
                await websocket.send(json.dumps(audio_frame))
                await asyncio.sleep(0.1)  # Simulate real-time streaming
            
            print("✅ Audio sent, waiting for response...")
            
            # Listen for responses
            response_count = 0
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    
                    if isinstance(response, str):
                        # Parse JSON response
                        frame = json.loads(response)
                        print(f"📥 Received frame type: {frame.get('type', 'unknown')}")
                        
                        if frame.get('type') == 'audio':
                            # Decode and play audio
                            audio_data = base64.b64decode(frame['data'])
                            audio_array = np.frombuffer(audio_data, dtype=np.int16)
                            print(f"🔊 Playing audio response ({len(audio_array)} samples)...")
                            sd.play(audio_array, samplerate=frame.get('sample_rate', 16000))
                            response_count += 1
                        
                        elif frame.get('type') == 'transcript':
                            print(f"📝 Transcript: {frame.get('text', '')}")
                        
                        elif frame.get('type') == 'error':
                            print(f"❌ Error: {frame.get('message', 'Unknown error')}")
                            break
                    
                    else:
                        # Binary data (might be raw audio)
                        print(f"📦 Received binary data: {len(response)} bytes")
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for response")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break
            
            print(f"✅ Test complete! Received {response_count} audio responses")
            
            # Send end frame
            end_frame = {
                "type": "end",
                "timestamp": time.time()
            }
            await websocket.send(json.dumps(end_frame))
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🧪 Voice Pipeline Test")
    print("=" * 40)
    asyncio.run(test_pipeline()) 