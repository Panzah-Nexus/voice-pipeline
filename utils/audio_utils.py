"""Audio helper functions."""

from __future__ import annotations

import sounddevice as sd
import numpy as np
from typing import Iterator

SAMPLE_RATE = 16000
CHUNK_DURATION_SEC = 0.5
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_SEC)


def microphone_chunks() -> Iterator[bytes]:
    """Yield raw microphone audio chunks using sounddevice."""
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=CHUNK_SIZE) as stream:
        while True:
            audio, _ = stream.read(CHUNK_SIZE)
            yield audio.tobytes()


def play_audio_chunk(chunk: bytes) -> None:
    """Play a chunk of audio through speakers using sounddevice."""
    audio = np.frombuffer(chunk, dtype=np.int16)
    sd.play(audio, samplerate=SAMPLE_RATE)
    sd.wait()
