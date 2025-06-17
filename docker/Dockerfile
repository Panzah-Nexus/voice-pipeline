# Use Python 3.10 with CUDA support for A10 GPU air-gapped deployment
FROM python:3.10-slim

# Install system dependencies including CUDA toolkit essentials and audio libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    dumb-init \
    ffmpeg \
    ca-certificates \
    wget \
    gnupg \
    software-properties-common \
    alsa-utils \
    libasound2-dev \
    portaudio19-dev \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Update CA certificates
RUN update-ca-certificates

# Set working directory
WORKDIR /app

# Set environment variables for GPU and air-gapped deployment
ENV CUDA_VISIBLE_DEVICES=0
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV PYTHONPATH=/app
ENV PIPER_MODEL=en_US-lessac-medium
ENV PIPER_SAMPLE_RATE=22050

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional ONNX runtime for GPU acceleration
RUN pip install --no-cache-dir onnxruntime-gpu

# Create directory for Piper models
RUN mkdir -p /root/.local/share/piper/models

# Copy source code
COPY src/ ./src/

# Expose port (required by Cerebrium)
EXPOSE 8000

# Use dumb-init for proper signal handling
CMD ["dumb-init", "--", "python", "-m", "src.main"]
