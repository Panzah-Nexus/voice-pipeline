# Use NVIDIA CUDA base image for A10 GPU
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-dev python3-pip \
    gcc g++ build-essential \
    curl wget \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Set working directory
WORKDIR /app

# Set environment variables
ENV CUDA_VISIBLE_DEVICES=0
ENV PYTHONPATH=/app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download and install Piper binary
RUN mkdir -p /usr/local/bin && \
    cd /tmp && \
    wget https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz && \
    tar -xzf piper_linux_x86_64.tar.gz && \
    # The tar file extracts to a 'piper' directory with the binary inside
    cp piper/piper /usr/local/bin/piper && \
    chmod +x /usr/local/bin/piper && \
    rm -rf /tmp/piper*

# Create directory for Piper models
RUN mkdir -p /models

# Download default Piper voice model
RUN cd /models && \
    wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx && \
    wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Run the main pipecat pipeline with raw audio support
CMD ["python", "-m", "uvicorn", "src.pipecat_pipeline:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["python", "-m", "uvicorn", "src.echo_pipeline:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["python", "-m", "uvicorn", "src.debug_echo_pipeline:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]
# CMD ["python", "-m", "uvicorn", "src.simple_audio_echo:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["python", "-m", "uvicorn", "src.raw_echo_server:app", "--host", "0.0.0.0", "--port", "8000"]
