#!/usr/bin/env python3
"""Test echo functionality on deployed server."""

import asyncio
import websockets
import numpy as np
import aiohttp
import json

WS_URL = "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws"
BASE_URL = "https://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped"

async def test_echo_endpoints():
    """Test the echo server endpoints."""
    print("1️⃣ Testing Echo Endpoints")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test debug endpoint
        try:
            async with session.get(f"{BASE_URL}/debug") as resp:
                if resp.status == 200:
                    debug_info = await resp.json()
                    print("✅ Debug endpoint working!")
                    print(json.dumps(debug_info, indent=2))
                else:
                    print(f"❌ Debug endpoint: {resp.status}")
        except Exception as e:
            print(f"❌ Debug endpoint failed: {e}")


async def test_echo_websocket():
    """Test echo functionality over WebSocket."""
    print("\n2️⃣ Testing Echo WebSocket")
    print("=" * 50)
    
    try:
        print(f"🔗 Connecting to: {WS_URL}")
        async with websockets.connect(WS_URL) as ws:
            print("✅ Connected!")
            
            # Send a few small audio chunks
            print("\n📤 Sending audio chunks...")
            
            received_count = 0
            sent_count = 0
            
            # Create a task to receive responses
            async def receive_responses():
                nonlocal received_count
                try:
                    while True:
                        response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                        received_count += 1
                        if isinstance(response, bytes):
                            print(f"📥 Received echo #{received_count}: {len(response)} bytes")
                        else:
                            print(f"📝 Received text: {response}")
                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    print(f"Receive error: {e}")
            
            # Start receiver
            receive_task = asyncio.create_task(receive_responses())
            
            # Send 3 audio chunks
            for i in range(3):
                # Create 0.5 seconds of audio (8000 samples at 16kHz)
                audio = np.zeros(8000, dtype=np.int16)
                # Add a beep in the middle of each chunk for identification
                audio[4000:4100] = np.int16(1000 * np.sin(2 * np.pi * 440 * np.arange(100) / 16000))
                
                await ws.send(audio.tobytes())
                sent_count += 1
                print(f"📤 Sent audio chunk #{sent_count}: {len(audio.tobytes())} bytes")
                await asyncio.sleep(0.5)
            
            # Wait for responses
            await asyncio.sleep(2)
            receive_task.cancel()
            
            print(f"\n📊 Results:")
            print(f"   Sent: {sent_count} chunks")
            print(f"   Received: {received_count} chunks")
            
            if received_count > 0:
                print("✅ Echo is working!")
            else:
                print("❌ No echo received")
                
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_simple_audio():
    """Test with the simplest possible audio."""
    print("\n3️⃣ Testing Simple Audio Echo")
    print("=" * 50)
    
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Connected")
            
            # Send one tiny audio chunk
            audio = b'\x00\x00' * 100  # 200 bytes of silence
            print(f"📤 Sending {len(audio)} bytes...")
            await ws.send(audio)
            
            # Wait for echo
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                if isinstance(response, bytes):
                    print(f"✅ Received echo: {len(response)} bytes")
                else:
                    print(f"📝 Received: {response}")
            except asyncio.TimeoutError:
                print("❌ No echo received (timeout)")
                
    except Exception as e:
        print(f"❌ Simple test failed: {e}")


async def main():
    """Run all echo tests."""
    print("🔊 Echo Deployment Test")
    print("Testing if audio is echoed back\n")
    
    await test_echo_endpoints()
    await test_echo_websocket()
    await test_simple_audio()
    
    print("\n💡 Next Steps:")
    print("1. If echo works → Pipeline is processing frames correctly")
    print("2. If echo fails → Issue with WebSocket/frame processing")
    print("3. Check logs: cerebrium logs voice-pipeline-airgapped")


if __name__ == "__main__":
    asyncio.run(main()) 