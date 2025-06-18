#!/usr/bin/env python3
"""Simple test for Pipecat pipeline - send one chunk and wait."""

import asyncio
import websockets

WS_URL = "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws"

async def test_simple():
    """Send one audio chunk and see what happens."""
    print("🔍 Simple Pipecat Test")
    print("=" * 50)
    
    try:
        print(f"🔗 Connecting to: {WS_URL}")
        async with websockets.connect(WS_URL) as ws:
            print("✅ Connected!")
            
            # Send one small audio chunk
            print("\n📤 Sending 1000 bytes of audio")
            audio = b'\x00\x00' * 500  # 1000 bytes
            await ws.send(audio)
            
            print("⏳ Waiting for response...")
            
            # Wait longer and log everything
            timeout = 20.0
            start = asyncio.get_event_loop().time()
            responses = 0
            
            while asyncio.get_event_loop().time() - start < timeout:
                remaining = timeout - (asyncio.get_event_loop().time() - start)
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=min(2.0, remaining))
                    responses += 1
                    
                    if isinstance(response, bytes):
                        print(f"📥 Response #{responses}: Binary data, {len(response)} bytes")
                    else:
                        print(f"📝 Response #{responses}: {response}")
                        
                except asyncio.TimeoutError:
                    print(f"⏰ No response after {asyncio.get_event_loop().time() - start:.1f} seconds...")
                    
            print(f"\n📊 Total responses: {responses}")
            
            if responses == 0:
                print("❌ No response at all from Pipecat pipeline")
                print("\n💡 This suggests:")
                print("   - Pipeline might not be processing frames")
                print("   - Serializer might not be working")
                print("   - Transport might not be sending data back")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing Pipecat Pipeline\n")
    asyncio.run(test_simple()) 