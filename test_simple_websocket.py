#!/usr/bin/env python3
"""Simple test to verify WebSocket connectivity."""

import asyncio
import websockets
import json
import time

WS_SERVER = "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws"

async def test_connection():
    """Test basic WebSocket connection and frame exchange."""
    print(f"🔗 Testing connection to: {WS_SERVER}")
    
    try:
        async with websockets.connect(
            WS_SERVER,
            ping_interval=20,
            ping_timeout=10
        ) as ws:
            print("✅ Connected!")
            
            # Send a start frame
            start_msg = json.dumps({"type": "start"})
            await ws.send(start_msg)
            print("📤 Sent start frame")
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Send an end frame
            end_msg = json.dumps({"type": "end"})
            await ws.send(end_msg)
            print("📤 Sent end frame")
            
            # Wait for any response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"📥 Received: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response received (timeout)")
            
            # Send cancel frame
            cancel_msg = json.dumps({"type": "cancel"})
            await ws.send(cancel_msg)
            print("📤 Sent cancel frame")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection()) 