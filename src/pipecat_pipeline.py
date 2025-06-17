"""Pipecat pipeline setup.

This module configures Pipecat with STT, LM, and TTS components.
Replace the placeholders with actual model initialization code.
"""
from __future__ import annotations

from pipecat import Pipeline

# TODO: import STT, LM, and TTS classes


def create_pipeline() -> Pipeline:
    """Create and return a Pipecat pipeline."""
    # TODO: load the smallest Ultravox model from Hugging Face
    # TODO: configure STT and language model
    pipeline = Pipeline()
    # pipeline.add_component(...)
    return pipeline


if __name__ == "__main__":
    p = create_pipeline()
    # TODO: run WebSocket server that processes audio through `p`
    pass
