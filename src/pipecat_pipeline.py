"""Pipecat pipeline setup.

This module configures Pipecat with STT, LM, and TTS components.
Replace the placeholders with actual model initialization code.
"""
from __future__ import annotations

import os
from pipecat import Pipeline

try:
    from pipecat.services.ultravox import UltravoxSTTService
except Exception as exc:  # pragma: no cover - optional dependency
    UltravoxSTTService = None
    print("UltravoxSTTService unavailable:", exc)

# TODO: import LM and TTS classes


def create_pipeline() -> Pipeline:
    """Create and return a Pipecat pipeline."""
    hf_token = os.environ.get("HUGGING_FACE_TOKEN")
    pipeline = Pipeline()

    if UltravoxSTTService:
        stt = UltravoxSTTService(
            model_size="1b",
            hf_token=hf_token,
            temperature=0.5,
            max_tokens=150,
        )
        pipeline.add_component(stt)

    # TODO: configure language model and TTS components
    return pipeline


if __name__ == "__main__":
    p = create_pipeline()
    # TODO: run WebSocket server that processes audio through `p`
    pass
