#!/usr/bin/env python3
"""
Comprehensive diagnostic script for voice pipeline issues.
Tests various aspects of the deployment to identify problems.
"""

import asyncio
import aiohttp
import json
import os
import sys
import websockets
import time
from datetime import datetime

# Configuration
BASE_URL = "https://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped"
WS_URL = "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws"

async def test_health_endpoints():
    """Test basic health and ready endpoints."""
    print("\n1️⃣ Testing Health Endpoints")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        try:
            async with session.get(f"{BASE_URL}/health") as resp:
                print(f"✅ /health: {resp.status} - {await resp.text()}")
        except Exception as e:
            print(f"❌ /health failed: {e}")
            
        # Test ready endpoint
        try:
            async with session.get(f"{BASE_URL}/ready") as resp:
                print(f"✅ /ready: {resp.status} - {await resp.text()}")
        except Exception as e:
            print(f"❌ /ready failed: {e}")
            
        # Test debug endpoint (most important!)
        try:
            async with session.get(f"{BASE_URL}/debug") as resp:
                if resp.status == 200:
                    debug_info = await resp.json()
                    print(f"\n📊 Debug Status:")
                    print(json.dumps(debug_info, indent=2))
                else:
                    print(f"❌ /debug: {resp.status} - {await resp.text()}")
        except Exception as e:
            print(f"❌ /debug failed: {e}")

async def test_websocket_connection():
    """Test basic WebSocket connectivity."""
    print("\n\n2️⃣ Testing WebSocket Connection")
    print("=" * 50)
    
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ WebSocket connected successfully")
            
            # Test sending a simple message
            await ws.send("test")
            print("✅ Sent test message")
            
            # Try to receive with timeout
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"📨 Received: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response within 5 seconds (might be normal)")
                
            await ws.close()
            print("✅ WebSocket closed cleanly")
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")

async def test_audio_pipeline():
    """Test sending actual audio data."""
    print("\n\n3️⃣ Testing Audio Pipeline")
    print("=" * 50)
    
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Connected to WebSocket")
            
            # Create silent audio (16kHz, 16-bit, mono)
            sample_rate = 16000
            duration = 2  # 2 seconds
            silence = b'\x00\x00' * (sample_rate * duration)
            
            print(f"📤 Sending {len(silence)} bytes of silent audio...")
            
            # Send audio in chunks
            chunk_size = 8000  # 0.5 seconds
            chunks_sent = 0
            
            for i in range(0, len(silence), chunk_size):
                chunk = silence[i:i+chunk_size]
                await ws.send(chunk)
                chunks_sent += 1
                await asyncio.sleep(0.1)  # Small delay between chunks
                
            print(f"✅ Sent {chunks_sent} audio chunks")
            
            # Send END signal
            await ws.send("END")
            print("📤 Sent END signal")
            
            # Wait for response
            print("⏳ Waiting for response...")
            start_time = time.time()
            response_count = 0
            
            try:
                while True:
                    response = await asyncio.wait_for(ws.recv(), timeout=15.0)
                    response_count += 1
                    
                    if isinstance(response, bytes):
                        print(f"🔊 Received audio chunk #{response_count}: {len(response)} bytes")
                    else:
                        print(f"📝 Received text: {response}")
                        if response == "" or response is None:
                            break
                            
            except asyncio.TimeoutError:
                elapsed = time.time() - start_time
                print(f"⏰ Timeout after {elapsed:.1f} seconds")
                
            if response_count == 0:
                print("❌ No response received from server")
            else:
                print(f"✅ Received {response_count} responses")
                
    except Exception as e:
        print(f"❌ Audio pipeline test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_model_loading():
    """Check if models are loading by monitoring logs."""
    print("\n\n4️⃣ Checking Model Status")
    print("=" * 50)
    
    print("💡 To check model loading status, run:")
    print("   cerebrium logs voice-pipeline-airgapped | grep -E '(model|Model|Loading|Downloading|GPU|CUDA)'")
    print("\n💡 Common issues to look for:")
    print("   - 'HF_TOKEN not found' - Token not set in secrets")
    print("   - 'CUDA out of memory' - Model too large for GPU")
    print("   - 'Failed to initialize' - Service initialization errors")

async def test_json_protocol():
    """Test JSON-based communication protocol."""
    print("\n\n5️⃣ Testing JSON Protocol")
    print("=" * 50)
    
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Connected to WebSocket")
            
            # Send JSON start message
            start_msg = json.dumps({"type": "start"})
            await ws.send(start_msg)
            print("📤 Sent JSON start message")
            
            # Send JSON audio message (with base64 encoded audio)
            import base64
            audio_data = b'\x00\x00' * 1000  # Small audio sample
            audio_msg = json.dumps({
                "type": "audio",
                "data": base64.b64encode(audio_data).decode('utf-8'),
                "sample_rate": 16000,
                "num_channels": 1
            })
            await ws.send(audio_msg)
            print("📤 Sent JSON audio message")
            
            # Send JSON end message
            end_msg = json.dumps({"type": "end"})
            await ws.send(end_msg)
            print("📤 Sent JSON end message")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=10.0)
                print(f"📨 Received: {response[:100]}..." if len(str(response)) > 100 else f"📨 Received: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response to JSON messages")
                
    except Exception as e:
        print(f"❌ JSON protocol test failed: {e}")

async def main():
    """Run all diagnostic tests."""
    print("🔍 Voice Pipeline Diagnostics")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Testing deployment at: {BASE_URL}")
    
    # Run tests in sequence
    await test_health_endpoints()
    await test_websocket_connection()
    await test_audio_pipeline()
    await test_json_protocol()
    await test_model_loading()
    
    print("\n\n📋 Diagnostic Summary")
    print("=" * 50)
    print("✅ Check the /debug endpoint output above - it shows service status")
    print("✅ If stt_available or tts_available is false, check model initialization")
    print("✅ Run 'cerebrium logs' command shown above to see detailed errors")
    print("\n💡 Most common issues:")
    print("   1. HF_TOKEN not set correctly in cerebrium.toml")
    print("   2. Model download failures during deployment")
    print("   3. GPU memory issues with large models")
    print("   4. Missing Piper binary in Docker image")

if __name__ == "__main__":
    asyncio.run(main()) 