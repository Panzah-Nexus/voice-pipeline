"""Simple binary serializer for AudioRawFrame in air-gapped voice pipeline."""

import struct
from typing import Optional

from pipecat.frames.frames import AudioRawFrame, Frame
from pipecat.serializers.base_serializer import FrameSerializer, FrameSerializerType


class AudioFrameSerializer(FrameSerializer):
    """Simple binary serializer for AudioRawFrame.
    
    This serializer is designed for direct WebSocket communication
    in air-gapped environments. It only handles AudioRawFrame types
    for bidirectional audio streaming.
    
    Format:
    - 4 bytes: Frame type ID (1 = AudioRawFrame)
    - 4 bytes: Sample rate (uint32)
    - 4 bytes: Number of channels (uint32) 
    - 4 bytes: Audio data length (uint32)
    - N bytes: Raw audio data
    """
    
    AUDIO_RAW_FRAME_ID = 1
    
    @property
    def type(self) -> FrameSerializerType:
        return FrameSerializerType.BINARY
    
    async def serialize(self, frame: Frame) -> Optional[bytes]:
        """Serialize frame to binary format."""
        if not isinstance(frame, AudioRawFrame):
            # Only handle AudioRawFrame for air-gapped voice pipeline
            return None
            
        try:
            # Pack frame data: type_id, sample_rate, channels, data_length, audio_data
            header = struct.pack(
                '>IIII',  # Big-endian, 4 unsigned ints
                self.AUDIO_RAW_FRAME_ID,
                frame.sample_rate,
                frame.num_channels,
                len(frame.audio)
            )
            
            return header + frame.audio
            
        except Exception as e:
            print(f"Serialization error: {e}")
            return None
    
    async def deserialize(self, data: bytes) -> Optional[Frame]:
        """Deserialize binary data to AudioRawFrame."""
        if len(data) < 16:  # Minimum header size
            return None
            
        try:
            # Unpack header
            frame_type, sample_rate, num_channels, audio_length = struct.unpack('>IIII', data[:16])
            
            if frame_type != self.AUDIO_RAW_FRAME_ID:
                return None
                
            if len(data) < 16 + audio_length:
                return None
                
            # Extract audio data
            audio_data = data[16:16 + audio_length]
            
            return AudioRawFrame(
                audio=audio_data,
                sample_rate=sample_rate,
                num_channels=num_channels
            )
            
        except Exception as e:
            print(f"Deserialization error: {e}")
            return None 