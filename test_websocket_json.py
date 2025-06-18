#!/usr/bin/env python3
"""Test WebSocket with JSON format that Pipecat expects."""

import asyncio
import websockets
import json
import base64
import numpy as np

WS_URL = "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws"

async def test_json_format():
    """Test with proper JSON format."""
    print("🔍 Testing Pipecat JSON Format")
    print("=" * 50)
    
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Connected!")
            
            # Test 1: Send audio in expected JSON format
            print("\n1️⃣ Sending audio in JSON format")
            audio_data = b'\x00\x00' * 500  # 1000 bytes
            audio_msg = {
                "type": "audio",
                "data": base64.b64encode(audio_data).decode('utf-8'),
                "sample_rate": 16000,
                "num_channels": 1
            }
            await ws.send(json.dumps(audio_msg))
            print("📤 Sent audio message")
            
            # Test 2: Send text message
            print("\n2️⃣ Sending text message")
            text_msg = {
                "type": "text",
                "text": "Hello, echo this!"
            }
            await ws.send(json.dumps(text_msg))
            print("📤 Sent text message")
            
            # Test 3: Send start frame
            print("\n3️⃣ Sending start frame")
            start_msg = {"type": "start"}
            await ws.send(json.dumps(start_msg))
            print("📤 Sent start frame")
            
            # Wait for responses
            print("\n⏳ Waiting for responses...")
            timeout = 10.0
            start_time = asyncio.get_event_loop().time()
            responses = []
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    
                    if isinstance(response, bytes):
                        print(f"📥 Binary response: {len(response)} bytes")
                        responses.append(("binary", len(response)))
                    else:
                        try:
                            msg = json.loads(response)
                            print(f"📥 JSON response: {msg}")
                            responses.append(("json", msg))
                        except:
                            print(f"📥 Text response: {response}")
                            responses.append(("text", response))
                            
                except asyncio.TimeoutError:
                    continue
            
            # Send end frame
            print("\n4️⃣ Sending end frame")
            end_msg = {"type": "end"}
            await ws.send(json.dumps(end_msg))
            
            print(f"\n📊 Total responses: {len(responses)}")
            if len(responses) == 0:
                print("❌ No responses received")
            else:
                print("✅ Received responses!")
                for i, (rtype, content) in enumerate(responses):
                    print(f"   {i+1}. {rtype}: {content}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing Pipecat with proper JSON format\n")
    asyncio.run(test_json_format()) 