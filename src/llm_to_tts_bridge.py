"""
LLM-to-TTS bridge for pipecat-ai 0.0.71
--------------------------------------

Collects the assistant’s text fragments coming from Ultravox
(LLMFullResponse* frames) and emits `TTSTextFrame` so any TTS
service downstream can speak.

• Works on 0.0.70-0.0.71 where pipecat did NOT yet ship
  `pipecat.processors.tts.llm_to_tts`.
• Sends partial text as soon as it arrives for low latency, then
  one final full sentence when the LLM signals end.
"""

from pipecat.processors.frame_processor import FrameProcessor
from pipecat.frames.frames import (
    LLMFullResponseStartFrame,
    LLMFullResponseContentFrame,
    LLMFullResponseEndFrame,
    TTSTextFrame,
    Frame,
)

class LLMToTTSBridge(FrameProcessor):
    """
    Turn Ultravox response frames into TTSTextFrame.

    Parameters
    ----------
    send_partial : bool, default True
        If True, each `LLMFullResponseContentFrame` is forwarded
        immediately as its own `TTSTextFrame`, so the TTS can
        start talking before the whole sentence is finished.
        If False, only one final frame is sent.
    """
    def __init__(self, *, send_partial: bool = True):
        super().__init__()
        self._buf: list[str] = []
        self._send_partial = send_partial

    async def process_frame(self, frame: Frame, direction):
        if isinstance(frame, LLMFullResponseStartFrame):
            self._buf.clear()

        elif isinstance(frame, LLMFullResponseContentFrame):
            self._buf.append(frame.content)
            if self._send_partial:
                await self.propagate(
                    TTSTextFrame(text=frame.content),
                    direction,
                )

        elif isinstance(frame, LLMFullResponseEndFrame):
            text = "".join(self._buf).strip()
            if text:
                await self.propagate(TTSTextFrame(text=text), direction)

        # Always forward the original frame too
        await self.propagate(frame, direction)
