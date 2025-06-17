"""Pipecat pipeline setup.

This module configures Pipecat with STT, LM, and TTS components.
Replace the placeholders with actual model initialization code.
"""
from __future__ import annotations

import os
from pipecat import Pipeline
from pipecat.services.ultravox.stt import UltravoxSTTService
from pipecat.services.cartesia.tts import CartesiaTTSService


def create_pipeline() -> Pipeline:
    """Create and return a Pipecat pipeline configured with Ultravox."""
    stt = UltravoxSTTService(
        model_size="fixie-ai/ultravox-v0_5-llama-3_1-8b",
        hf_token=os.environ.get("HF_TOKEN"),
        temperature=0.5,
        max_tokens=150,
    )

    tts = CartesiaTTSService(api_key=os.environ.get("CARTESIA_API_KEY"))

    pipeline = Pipeline([stt, tts])
    return pipeline


if __name__ == "__main__":
    from .websocket_server import main as ws_main

    ws_main()
