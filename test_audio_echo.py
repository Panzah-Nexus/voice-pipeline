#!/usr/bin/env python3
"""Test audio echo with real audio patterns."""

import asyncio
import websockets
import numpy as np

WS_URL = "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws"

def generate_test_audio(duration_sec=1.0, frequency=440, sample_rate=16000):
    """Generate a test tone (A4 note)."""
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec))
    # Generate sine wave
    audio = np.sin(2 * np.pi * frequency * t)
    # Convert to 16-bit PCM
    audio_int16 = (audio * 32767).astype(np.int16)
    return audio_int16.tobytes()

async def test_audio_echo():
    """Test audio echo with identifiable patterns."""
    print("🔊 Audio Echo Test")
    print("=" * 50)
    
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Connected!")
            
            # Test 1: Send a beep pattern
            print("\n1️⃣ Sending 440Hz tone (A4 note)")
            tone = generate_test_audio(duration_sec=0.5, frequency=440)
            await ws.send(tone)
            
            # Test 2: Send different frequency
            print("2️⃣ Sending 880Hz tone (A5 note)")
            tone2 = generate_test_audio(duration_sec=0.5, frequency=880)
            await ws.send(tone2)
            
            # Test 3: Send silence
            print("3️⃣ Sending silence")
            silence = b'\x00\x00' * 8000  # 0.5 seconds of silence
            await ws.send(silence)
            
            # Send END
            print("4️⃣ Sending END signal")
            await ws.send("END")
            
            # Receive responses
            print("\n⏳ Waiting for echoed audio...")
            responses = []
            
            timeout = 10.0
            start = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start < timeout:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    
                    if isinstance(response, bytes):
                        responses.append(response)
                        print(f"📥 Received audio #{len(responses)}: {len(response)} bytes")
                        
                        # Check if it's silence or has signal
                        audio_array = np.frombuffer(response[:1000], dtype=np.int16)
                        max_val = np.max(np.abs(audio_array))
                        if max_val < 100:
                            print("   → Sounds like silence")
                        else:
                            print(f"   → Has audio signal (max amplitude: {max_val})")
                    else:
                        print(f"📝 Received text: {response}")
                        
                except asyncio.TimeoutError:
                    if len(responses) > 0:
                        break
                        
            print(f"\n📊 Summary:")
            print(f"   Total audio responses: {len(responses)}")
            
            # Verify we got our audio back
            if len(responses) >= 3:
                print("✅ All audio chunks echoed back!")
                
                # Check if audio matches what we sent
                if len(responses[0]) == len(tone):
                    print("✅ First echo matches sent tone size")
                if len(responses[2]) == len(silence):
                    print("✅ Silence echo matches sent size")
            else:
                print("❌ Not all audio was echoed back")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_voice_simulation():
    """Simulate a more realistic voice interaction."""
    print("\n\n🎤 Voice Simulation Test")
    print("=" * 50)
    
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Connected!")
            
            print("📤 Simulating 5 seconds of 'speech'...")
            
            # Send 10 chunks of 0.5 seconds each
            for i in range(10):
                # Create varying amplitude to simulate speech
                t = np.linspace(0, 0.5, 8000)
                # Mix of frequencies to simulate voice
                voice = (
                    0.3 * np.sin(2 * np.pi * 200 * t) +  # Low frequency
                    0.2 * np.sin(2 * np.pi * 400 * t) +  # Mid frequency
                    0.1 * np.sin(2 * np.pi * 800 * t)    # High frequency
                )
                # Add envelope to simulate speech patterns
                envelope = np.sin(np.pi * i / 10)
                voice = voice * envelope
                
                # Convert to 16-bit
                voice_int16 = (voice * 16383).astype(np.int16)
                
                await ws.send(voice_int16.tobytes())
                print(f"   Sent chunk {i+1}/10")
                await asyncio.sleep(0.05)  # Small delay between chunks
                
            # Send END
            print("📤 Sending END")
            await ws.send("END")
            
            # Count responses
            print("\n⏳ Receiving echo...")
            audio_count = 0
            text_count = 0
            
            timeout = 15.0
            start = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start < timeout:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    
                    if isinstance(response, bytes):
                        audio_count += 1
                        if audio_count <= 3 or audio_count > 8:
                            print(f"📥 Audio chunk #{audio_count}: {len(response)} bytes")
                        elif audio_count == 4:
                            print("   ... (showing first/last few)")
                    else:
                        text_count += 1
                        print(f"📝 Text: {response}")
                        
                except asyncio.TimeoutError:
                    break
                    
            print(f"\n📊 Results:")
            print(f"   Audio chunks echoed: {audio_count}")
            print(f"   Text messages: {text_count}")
            
            if audio_count == 10:
                print("✅ Perfect! All 10 audio chunks echoed back")
            else:
                print(f"⚠️  Expected 10 chunks, got {audio_count}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    print("🧪 Testing Audio Echo Functionality")
    print("This tests echo with real audio patterns\n")
    
    asyncio.run(test_audio_echo())
    asyncio.run(test_voice_simulation()) 