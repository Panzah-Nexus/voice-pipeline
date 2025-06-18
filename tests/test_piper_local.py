#!/usr/bin/env python3
"""Test the local Piper TTS setup."""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from piper_tts_service import PiperTTSService

async def test_piper():
    print("🧪 Testing Piper TTS Service...")
    
    try:
        # Initialize Piper TTS Service
        tts = PiperTTSService(model_name="en_US-lessac-medium")
        print(f"✅ Piper initialized with model: {tts.model_name}")
        
        # Test synthesis
        text = "Hello! This is a test of the Piper text-to-speech system."
        print(f"📝 Text: {text}")
        
        # Collect audio frames
        audio_chunks = []
        async for frame in tts.run_tts(text):
            if hasattr(frame, 'audio') and frame.audio:
                audio_chunks.append(frame.audio)
                print(f"📦 Received frame: {len(frame.audio)} bytes")
        
        if audio_chunks:
            # Combine chunks
            audio_data = b''.join(audio_chunks)
            print(f"✅ Generated {len(audio_data)} bytes of audio")
            
            # Create WAV file
            import wave
            with wave.open("test_output.wav", "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)  # Service sample rate
                wav_file.writeframes(audio_data)
            print("✅ Saved to test_output.wav")
        else:
            print("❌ No audio frames generated")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_piper()) 