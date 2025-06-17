FROM python:3.10-slim

# Install system deps (for audio processing etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install python deps
RUN pip install --no-cache-dir \
    pipecat-ai[ultravox] \
    websockets \
    sounddevice

WORKDIR /app
COPY ../src /app/src

CMD ["python", "-m", "src.main"]
