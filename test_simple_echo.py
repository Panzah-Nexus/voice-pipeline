#!/usr/bin/env python3
"""
Simple echo test for WebSocket - tests the most basic functionality.
"""

import asyncio
import websockets
import json

WS_URL = "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws"

async def test_echo():
    """Test basic echo functionality."""
    print("🔍 Simple WebSocket Echo Test")
    print("=" * 50)
    
    try:
        print(f"🔗 Connecting to: {WS_URL}")
        async with websockets.connect(WS_URL) as ws:
            print("✅ Connected!")
            
            # Test 1: Send text
            print("\n📤 Sending text: 'Hello'")
            await ws.send("Hello")
            
            # Wait briefly
            await asyncio.sleep(1)
            
            # Try to receive
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                print(f"📨 Received: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response to text message")
            
            # Test 2: Send END signal
            print("\n📤 Sending: 'END'")
            await ws.send("END")
            
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                print(f"📨 Received: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response to END signal")
            
            # Test 3: Send minimal audio
            print("\n📤 Sending 1KB of audio data")
            audio = b'\x00\x00' * 500  # 1KB of silence
            await ws.send(audio)
            
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                if isinstance(response, bytes):
                    print(f"📨 Received audio: {len(response)} bytes")
                else:
                    print(f"📨 Received text: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response to audio data")
                
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_echo()) 