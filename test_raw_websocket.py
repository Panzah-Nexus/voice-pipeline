#!/usr/bin/env python3
"""Test raw WebSocket communication without Pipecat framework."""

import asyncio
import websockets
import struct

WS_URL = "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws"

async def test_raw_websocket():
    """Test raw WebSocket communication."""
    print("🔍 Raw WebSocket Test (No Pipecat)")
    print("=" * 50)
    
    try:
        print(f"🔗 Connecting to: {WS_URL}")
        async with websockets.connect(WS_URL) as ws:
            print("✅ Connected!")
            
            # Send different types of data to see what happens
            
            # Test 1: Send text
            print("\n1️⃣ Sending text 'Hello'")
            await ws.send("Hello")
            await asyncio.sleep(0.5)
            
            # Test 2: Send small binary data
            print("\n2️⃣ Sending 100 bytes of binary data")
            data = b'\x00' * 100
            await ws.send(data)
            await asyncio.sleep(0.5)
            
            # Test 3: Send audio-sized binary data (16000 bytes = 1 second at 16kHz)
            print("\n3️⃣ Sending 16000 bytes (1 second of audio)")
            audio = b'\x00' * 16000
            await ws.send(audio)
            await asyncio.sleep(0.5)
            
            # Test 4: Send "END" signal
            print("\n4️⃣ Sending 'END' signal")
            await ws.send("END")
            
            # Now try to receive ANY response
            print("\n⏳ Waiting for ANY response...")
            received_anything = False
            
            try:
                # Set a longer timeout
                timeout = 10.0
                start_time = asyncio.get_event_loop().time()
                
                while True:
                    remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                    if remaining <= 0:
                        break
                        
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=remaining)
                        received_anything = True
                        
                        if isinstance(response, bytes):
                            print(f"📥 Received binary: {len(response)} bytes")
                            # Check if it might be audio
                            if len(response) > 1000:
                                print("   (Might be audio data)")
                        else:
                            print(f"📝 Received text: {response}")
                            
                    except asyncio.TimeoutError:
                        break
                        
            except Exception as e:
                print(f"❌ Error receiving: {e}")
                
            if not received_anything:
                print("❌ No response received at all")
            else:
                print("✅ Received some response!")
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()


async def test_continuous_audio():
    """Test sending continuous audio chunks."""
    print("\n\n🔍 Continuous Audio Test")
    print("=" * 50)
    
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Connected!")
            
            # Send 5 chunks of audio
            print("📤 Sending 5 audio chunks...")
            for i in range(5):
                # 8000 samples = 0.5 seconds at 16kHz
                audio = b'\x00' * 16000  # 16-bit samples
                await ws.send(audio)
                print(f"   Sent chunk {i+1}")
                await asyncio.sleep(0.1)
            
            # Send END
            print("📤 Sending END signal")
            await ws.send("END")
            
            # Wait for response
            print("⏳ Waiting for response...")
            
            timeout = 15.0
            responses = 0
            
            try:
                start = asyncio.get_event_loop().time()
                while asyncio.get_event_loop().time() - start < timeout:
                    remaining = timeout - (asyncio.get_event_loop().time() - start)
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=min(2.0, remaining))
                        responses += 1
                        if isinstance(response, bytes):
                            print(f"📥 Response #{responses}: {len(response)} bytes")
                        else:
                            print(f"📝 Response #{responses}: {response}")
                    except asyncio.TimeoutError:
                        if responses == 0:
                            print("⏰ Still no response...")
                        else:
                            break
                            
            except Exception as e:
                print(f"Error: {e}")
                
            print(f"\n📊 Total responses: {responses}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    print("🧪 Testing Raw WebSocket Communication")
    print("This bypasses Pipecat to test the server directly\n")
    
    asyncio.run(test_raw_websocket())
    asyncio.run(test_continuous_audio()) 