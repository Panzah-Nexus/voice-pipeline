#!/usr/bin/env python3
"""Test pipeline components locally to verify they work."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.frames.frames import AudioRawFrame, Frame, TextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
import numpy as np

# Simple echo processor for testing
class EchoProcessor(FrameProcessor):
    """Simple processor that echoes audio frames."""
    
    def __init__(self):
        super().__init__()
        self.frame_count = 0
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        if isinstance(frame, AudioRawFrame):
            self.frame_count += 1
            print(f"🎵 Echo processor received audio frame #{self.frame_count}: {len(frame.audio)} bytes")
            # Echo it back
            await self.push_frame(frame, direction)
        else:
            print(f"📦 Echo processor received frame type: {type(frame).__name__}")
            await self.push_frame(frame, direction)


# Test transport that generates and receives frames
class TestTransport(FrameProcessor):
    """Test transport that generates audio and receives responses."""
    
    def __init__(self):
        super().__init__()
        self.received_frames = []
        
    async def start_test(self):
        """Generate test audio frames."""
        print("🚀 Starting test pipeline...")
        
        # Generate 3 test audio frames (silence)
        for i in range(3):
            audio_data = np.zeros(8000, dtype=np.int16)  # 0.5 seconds of silence
            frame = AudioRawFrame(
                audio=audio_data.tobytes(),
                sample_rate=16000,
                num_channels=1
            )
            print(f"📤 Sending test audio frame #{i+1}")
            await self.push_frame(frame)
            await asyncio.sleep(0.1)
            
        print("✅ Test frames sent")
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        if isinstance(frame, AudioRawFrame):
            self.received_frames.append(frame)
            print(f"📥 Received audio response: {len(frame.audio)} bytes")
        else:
            print(f"📦 Received frame type: {type(frame).__name__}")


async def test_echo_pipeline():
    """Test a simple echo pipeline locally."""
    print("🧪 Testing Local Echo Pipeline")
    print("=" * 50)
    
    # Create components
    transport = TestTransport()
    echo = EchoProcessor()
    
    # Build pipeline
    pipeline = Pipeline([
        transport,      # Input
        echo,          # Process (echo)
        transport      # Output (back to transport)
    ])
    
    # Create task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
        ),
    )
    
    # Run pipeline
    runner = PipelineRunner()
    
    # Start test in background
    async def run_test():
        await transport.start_test()
        await asyncio.sleep(1)  # Let frames process
        await runner.stop()
    
    # Run both
    await asyncio.gather(
        runner.run(task),
        run_test()
    )
    
    # Check results
    print(f"\n📊 Results: Received {len(transport.received_frames)} frames")
    if transport.received_frames:
        print("✅ Echo pipeline working locally!")
    else:
        print("❌ No frames received - pipeline not working")


async def test_with_pipecat_services():
    """Test with actual Pipecat services."""
    print("\n\n🧪 Testing with Pipecat Services")
    print("=" * 50)
    
    try:
        # Try to import services
        from src.piper_tts_service import PiperTTSService
        
        # Test TTS
        print("Testing Piper TTS...")
        tts = PiperTTSService(model_name="en_US-lessac-medium", sample_rate=16000)
        
        # Generate simple TTS
        frames = []
        async for frame in tts.run_tts("Hello, this is a test"):
            frames.append(frame)
            if isinstance(frame, AudioRawFrame):
                print(f"✅ TTS generated audio: {len(frame.audio)} bytes")
                
        if frames:
            print(f"✅ TTS working! Generated {len(frames)} frames")
        else:
            print("❌ TTS not generating frames")
            
    except Exception as e:
        print(f"❌ Failed to test services: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🔍 Local Pipeline Component Test")
    print("This tests if the pipeline components work locally\n")
    
    # Run tests
    asyncio.run(test_echo_pipeline())
    asyncio.run(test_with_pipecat_services()) 