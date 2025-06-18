#!/usr/bin/env python3
"""Comprehensive audio test client with detailed logging and diagnostics."""

import asyncio
import websockets
import numpy as np
import time
from datetime import datetime

# Test configuration
WS_URL = "wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws"
SAMPLE_RATE = 16000
DURATION_SEC = 1.0

class AudioTestClient:
    def __init__(self):
        self.sent_count = 0
        self.received_count = 0
        self.sent_bytes = 0
        self.received_bytes = 0
        self.start_time = None
        
    def generate_test_tone(self, frequency=440, duration=1.0):
        """Generate a test tone at given frequency."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
        audio = np.sin(2 * np.pi * frequency * t)
        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)
        return audio_int16.tobytes()
    
    def generate_silence(self, duration=1.0):
        """Generate silence."""
        samples = int(SAMPLE_RATE * duration)
        return np.zeros(samples, dtype=np.int16).tobytes()
    
    async def test_connection(self):
        """Test the WebSocket connection with various audio patterns."""
        print("🔍 Audio Echo Test Client")
        print("=" * 60)
        print(f"📡 Connecting to: {WS_URL}")
        print(f"🎵 Sample rate: {SAMPLE_RATE} Hz")
        print("=" * 60)
        
        try:
            async with websockets.connect(WS_URL) as ws:
                print("✅ Connected successfully!")
                self.start_time = time.time()
                
                # Create tasks for sending and receiving
                send_task = asyncio.create_task(self.send_audio(ws))
                receive_task = asyncio.create_task(self.receive_audio(ws))
                
                # Wait for both tasks
                await asyncio.gather(send_task, receive_task)
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            import traceback
            traceback.print_exc()
    
    async def send_audio(self, ws):
        """Send various audio patterns."""
        try:
            # Test 1: Send 440Hz tone (A4 note)
            print("\n📤 Test 1: Sending 440Hz tone (1 second)")
            audio = self.generate_test_tone(440, 1.0)
            await ws.send(audio)
            self.sent_count += 1
            self.sent_bytes += len(audio)
            print(f"   Sent {len(audio)} bytes")
            await asyncio.sleep(1.5)
            
            # Test 2: Send 880Hz tone (A5 note)
            print("\n📤 Test 2: Sending 880Hz tone (0.5 seconds)")
            audio = self.generate_test_tone(880, 0.5)
            await ws.send(audio)
            self.sent_count += 1
            self.sent_bytes += len(audio)
            print(f"   Sent {len(audio)} bytes")
            await asyncio.sleep(1.0)
            
            # Test 3: Send silence
            print("\n📤 Test 3: Sending silence (1 second)")
            audio = self.generate_silence(1.0)
            await ws.send(audio)
            self.sent_count += 1
            self.sent_bytes += len(audio)
            print(f"   Sent {len(audio)} bytes")
            await asyncio.sleep(1.0)
            
            # Test 4: Send multiple small chunks rapidly
            print("\n📤 Test 4: Sending 10 small chunks (100ms each)")
            for i in range(10):
                audio = self.generate_test_tone(440 + i*50, 0.1)
                await ws.send(audio)
                self.sent_count += 1
                self.sent_bytes += len(audio)
                print(f"   Chunk {i+1}: {len(audio)} bytes")
                await asyncio.sleep(0.1)
            
            # Test 5: Send END signal
            print("\n📤 Test 5: Sending END signal")
            await ws.send("END")
            
            # Wait a bit for responses
            await asyncio.sleep(3.0)
            
        except Exception as e:
            print(f"❌ Send error: {e}")
    
    async def receive_audio(self, ws):
        """Receive and analyze responses."""
        print("\n📥 Listening for responses...")
        print("-" * 40)
        
        try:
            while True:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    self.received_count += 1
                    
                    if isinstance(response, bytes):
                        self.received_bytes += len(response)
                        
                        # Analyze the audio
                        audio_array = np.frombuffer(response, dtype=np.int16)
                        
                        # Calculate basic statistics
                        rms = np.sqrt(np.mean(audio_array**2))
                        peak = np.max(np.abs(audio_array))
                        is_silence = peak < 100  # Threshold for silence
                        
                        print(f"\n📊 Response #{self.received_count}:")
                        print(f"   Type: Binary audio")
                        print(f"   Size: {len(response)} bytes ({len(audio_array)} samples)")
                        print(f"   Duration: {len(audio_array)/SAMPLE_RATE:.3f} seconds")
                        print(f"   RMS: {rms:.1f}")
                        print(f"   Peak: {peak}")
                        print(f"   Silent: {'Yes' if is_silence else 'No'}")
                        
                        # Check if it matches what we sent
                        latency = time.time() - self.start_time
                        print(f"   Latency: ~{latency:.3f} seconds")
                        
                    else:
                        print(f"\n📝 Response #{self.received_count}:")
                        print(f"   Type: Text")
                        print(f"   Message: {response}")
                        
                        if response == "Echo: END":
                            print("\n🔚 Received END echo, closing...")
                            break
                            
                except asyncio.TimeoutError:
                    # No response within timeout
                    pass
                    
        except websockets.exceptions.ConnectionClosed:
            print("\n🔌 Connection closed by server")
        except Exception as e:
            print(f"\n❌ Receive error: {e}")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        duration = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"⏱️  Total duration: {duration:.2f} seconds")
        print(f"📤 Sent: {self.sent_count} messages, {self.sent_bytes:,} bytes")
        print(f"📥 Received: {self.received_count} messages, {self.received_bytes:,} bytes")
        
        if self.sent_bytes > 0:
            echo_rate = (self.received_bytes / self.sent_bytes) * 100
            print(f"📈 Echo rate: {echo_rate:.1f}%")
        
        if self.sent_count > 0 and self.received_count > 0:
            print(f"✅ Audio echo is working!")
        else:
            print(f"❌ No audio echo detected")
        
        print("=" * 60)


async def main():
    """Run the test client."""
    client = AudioTestClient()
    await client.test_connection()


if __name__ == "__main__":
    print(f"🕐 Starting test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    asyncio.run(main()) 