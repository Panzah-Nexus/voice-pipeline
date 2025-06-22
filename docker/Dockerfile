###############################################################################
# Base: CUDA 11.8 runtime (for PyTorch + Whisper CUDA acceleration)
###############################################################################
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

###############################################################################
# 1. System packages + Ollama dependencies
###############################################################################
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-dev python3-pip \
    gcc g++ build-essential openssh-server espeak-ng libespeak-ng1 \
    curl wget ffmpeg libsndfile1 git \
    # Ollama dependencies
    ca-certificates gnupg lsb-release \
 && rm -rf /var/lib/apt/lists/*

###############################################################################
# 2. Install Ollama
###############################################################################
RUN curl -fsSL https://ollama.com/install.sh | sh

###############################################################################
# 3. SSH (unchanged)
###############################################################################
RUN mkdir -p /var/run/sshd && \
    echo 'root:runpod' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's@session\\s*required\\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd

###############################################################################
# 4. Python tooling
###############################################################################
# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

###############################################################################
# 5. Clone Kokoro model & voices with Git-LFS (TTS component)
###############################################################################
RUN mkdir -p /models && \
    git clone https://huggingface.co/hexgrad/Kokoro-82M /models/kokoro   # downloads ~600 MB via LFS

# Expose the path to Kokoro so the Python package finds it automatically
ENV KOKORO_HOME=/models/kokoro

###############################################################################
# 6. Python dependencies (updated for cascaded pipeline)
###############################################################################
# Copy requirements.txt right before installation to break cache when it changes
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

###############################################################################
# 7. Pre-download Ollama model for faster startup
###############################################################################
# Start Ollama in background, download model, then stop
RUN ollama serve & \
    sleep 10 && \
    ollama pull llama3.2:3b && \
    pkill ollama

###############################################################################
# 8. Copy application code
###############################################################################
WORKDIR /app

COPY src/ ./src/

# Create startup script that starts SSH, Ollama, and the app
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
set -e

echo "Starting SSH daemon..."
service ssh start

echo "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

echo "Waiting for Ollama to be ready..."
# Wait for Ollama to be ready
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    echo "Waiting for Ollama... ($i/30)"
    sleep 2
done

# Verify model is available
echo "Verifying model is available..."
ollama list

echo "Starting voice pipeline server..."
exec python src/main.py
EOF

RUN chmod +x /app/start.sh

# Set environment variables with defaults
ENV OLLAMA_MODEL="llama3.2:3b"
ENV OLLAMA_BASE_URL="http://localhost:11434/v1"
ENV CUDA_AVAILABLE="true"
ENV KOKORO_VOICE_ID="af_bella"
ENV KOKORO_SAMPLE_RATE="24000"

# Expose ports
EXPOSE 22 8000 11434

# Start both SSH and the app
CMD ["/app/start.sh"]



