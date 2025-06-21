from pipecat.processors.frame_processor import FrameProcessor
from pipecat.frames import frames as _f     # import module once

# ---- Resolve class names that exist in your wheel (0.0.71) -------------
def _cls(*candidates):
    for name in candidates:
        if hasattr(_f, name):
            return getattr(_f, name)
    raise ImportError(f"None of {candidates} found in pipecat.frames.frames")

LLMStart  = _cls("LLMFullResponseStartFrame",  "LLMResponseStartFrame")
LLMChunk  = _cls("LLMFullResponseContentFrame","LLMResponseContentFrame")
LLMEnd    = _cls("LLMFullResponseEndFrame",    "LLMResponseEndFrame")

from pipecat.frames.frames import TTSTextFrame, Frame

class LLMToTTSBridge(FrameProcessor):
    """Convert Ultravox LLM frames → TTSTextFrame (works on 0.0.70–0.0.71)."""
    def __init__(self, *, send_partial=True):
        super().__init__()
        self._buf, self._partial = [], send_partial

    async def process_frame(self, frame: Frame, direction):
        if isinstance(frame, LLMStart):
            self._buf.clear()
        elif isinstance(frame, LLMChunk):
            self._buf.append(frame.content)
            if self._partial:
                await self.propagate(TTSTextFrame(text=frame.content), direction)
        elif isinstance(frame, LLMEnd):
            text = "".join(self._buf).strip()
            if text:
                await self.propagate(TTSTextFrame(text=text), direction)
        await self.propagate(frame, direction)  # always forward original
