"""Simple protobuf serializer for Pipecat WebSocket communication."""

import base64
import json
import logging
from typing import Any
from pipecat.serializers.base_serializer import FrameSerializer

logger = logging.getLogger(__name__)
from pipecat.frames.frames import (
    AudioRawFrame,
    Frame,
    StartFrame,
    EndFrame,
    CancelFrame,
    TranscriptionFrame,
    TextFrame
)

class SimpleProtobufSerializer(FrameSerializer):
    """Simple serializer for WebSocket communication."""
    
    @property
    def type(self) -> str:
        """Return the type of this serializer."""
        return "simple_protobuf"
    
    async def serialize(self, frame: Frame) -> Any:
        """Serialize frame to JSON-compatible format."""
        if isinstance(frame, AudioRawFrame):
            return {
                "type": "audio",
                "data": base64.b64encode(frame.audio).decode('utf-8'),
                "sample_rate": frame.sample_rate,
                "num_channels": frame.num_channels
            }
        elif isinstance(frame, TranscriptionFrame):
            return {
                "type": "transcription",
                "text": frame.text,
                "user_id": frame.user_id,
                "timestamp": frame.timestamp
            }
        elif isinstance(frame, TextFrame):
            return {
                "type": "text",
                "text": frame.text
            }
        elif isinstance(frame, StartFrame):
            return {"type": "start"}
        elif isinstance(frame, EndFrame):
            return {"type": "end"}
        elif isinstance(frame, CancelFrame):
            return {"type": "cancel"}
        else:
            # Default serialization
            return {"type": frame.__class__.__name__}
    
    async def deserialize(self, data: Any) -> Frame | None:
        """Deserialize data to frame."""
        if isinstance(data, bytes):
            # Raw audio bytes - create audio frame
            logger.debug(f"Deserializing raw audio bytes: {len(data)} bytes")
            return AudioRawFrame(
                audio=data,
                sample_rate=16000,
                num_channels=1
            )
        elif isinstance(data, str):
            try:
                # Try to parse as JSON
                msg = json.loads(data)
                msg_type = msg.get("type", "")
                
                if msg_type == "audio":
                    # Decode base64 audio data
                    audio_data = base64.b64decode(msg["data"])
                    logger.debug(f"Deserializing audio frame: {len(audio_data)} bytes")
                    return AudioRawFrame(
                        audio=audio_data,
                        sample_rate=msg.get("sample_rate", 16000),
                        num_channels=msg.get("num_channels", 1)
                    )
                elif msg_type == "start":
                    logger.debug("Deserializing start frame")
                    return StartFrame()
                elif msg_type == "end":
                    logger.debug("Deserializing end frame")
                    return EndFrame()
                elif msg_type == "cancel":
                    return CancelFrame()
                elif msg_type == "text":
                    return TextFrame(text=msg.get("text", ""))
            except json.JSONDecodeError:
                # If not JSON, treat as raw text
                if data == "END":
                    return EndFrame()
                else:
                    return TextFrame(text=data)
        
        return None 