"""Audio helper functions."""

from __future__ import annotations

from typing import Iterable
import queue
import sounddevice as sd

SAMPLE_RATE = 16000
CHUNK_SIZE = 1024


def microphone_chunks() -> Iterable[bytes]:
    """Yield raw microphone audio chunks from the default microphone."""
    q: queue.Queue[bytes] = queue.Queue()

    def callback(indata, frames, time, status):  # type: ignore[call-arg]
        if status:
            print(status)
        q.put(indata.tobytes())

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, blocksize=CHUNK_SIZE, callback=callback):
        while True:
            yield q.get()


def play_audio_chunk(chunk: bytes) -> None:
    """Play a chunk of audio through speakers."""
    sd.play(chunk, samplerate=SAMPLE_RATE)
    sd.wait()
