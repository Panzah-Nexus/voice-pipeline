"""Raw audio serializer for Pipecat that handles direct binary audio."""

import logging
from typing import Any
from pipecat.serializers.base_serializer import FrameSerializer
from pipecat.frames.frames import (
    AudioRawFrame,
    Frame,
    StartFrame,
    EndFrame,
    CancelFrame,
    TextFrame
)

logger = logging.getLogger(__name__)

class RawAudioSerializer(FrameSerializer):
    """Serializer that handles raw binary audio directly."""
    
    @property
    def type(self) -> str:
        """Return the type of this serializer."""
        return "raw_audio"
    
    async def serialize(self, frame: Frame) -> Any:
        """Serialize frame to raw format."""
        if isinstance(frame, AudioRawFrame):
            # Return raw audio bytes directly
            return frame.audio
        elif isinstance(frame, TextFrame):
            # Return text as string
            return frame.text
        elif isinstance(frame, StartFrame):
            return "START"
        elif isinstance(frame, EndFrame):
            return "END"
        elif isinstance(frame, CancelFrame):
            return "CANCEL"
        else:
            # For other frames, return their type name
            return frame.__class__.__name__
    
    async def deserialize(self, data: Any) -> Frame | None:
        """Deserialize data to frame."""
        # FastAPI WebSocket wraps data in a dict
        if isinstance(data, dict):
            if "bytes" in data:
                # Raw audio bytes
                audio_data = data["bytes"]
                logger.debug(f"Deserializing raw audio: {len(audio_data)} bytes")
                return AudioRawFrame(
                    audio=audio_data,
                    sample_rate=16000,
                    num_channels=1
                )
            elif "text" in data:
                # Text message
                text = data["text"]
                logger.debug(f"Deserializing text: {text}")
                
                if text == "START":
                    return StartFrame()
                elif text == "END":
                    return EndFrame()
                elif text == "CANCEL":
                    return CancelFrame()
                else:
                    return TextFrame(text=text)
        
        # If data is already bytes (shouldn't happen with FastAPI)
        elif isinstance(data, bytes):
            logger.debug(f"Deserializing direct bytes: {len(data)} bytes")
            return AudioRawFrame(
                audio=data,
                sample_rate=16000,
                num_channels=1
            )
        
        # If data is a string
        elif isinstance(data, str):
            if data == "START":
                return StartFrame()
            elif data == "END":
                return EndFrame()
            elif data == "CANCEL":
                return CancelFrame()
            else:
                return TextFrame(text=data)
        
        logger.warning(f"Unable to deserialize data of type: {type(data)}")
        return None 