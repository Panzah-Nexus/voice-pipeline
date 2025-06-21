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
# 7. Pre-download recommended Ollama model for faster startup
###############################################################################
# Start Ollama service and download model during build (optional - speeds up first run)
RUN ollama serve & \
    sleep 5 && \
    ollama pull llama3.2:3b && \
    pkill ollama || true

###############################################################################
# 8. Copy application code
###############################################################################
WORKDIR /app

COPY src/ ./src/
COPY setup_local_pipeline.sh ./
COPY .env* ./

# Create enhanced startup script
RUN cat > /app/start.sh << 'EOF'\
#!/bin/bash\
echo "🚀 Starting Local Voice Pipeline Container..."\
\
# Start SSH daemon\
service ssh start\
echo "✅ SSH daemon started"\
\
# Start Ollama service\
ollama serve &\
OLLAMA_PID=$!\
echo "✅ Ollama service started (PID: $OLLAMA_PID)"\
\
# Wait for Ollama to be ready\
echo "⏳ Waiting for Ollama to be ready..."\
for i in {1..30}; do\
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then\
        echo "✅ Ollama is ready!"\
        break\
    fi\
    sleep 1\
done\
\
# Ensure model is available\
if ! ollama list | grep -q "llama3.2:3b"; then\
    echo "📥 Downloading llama3.2:3b model..."\
    ollama pull llama3.2:3b\
fi\
\
# Set environment variables for the pipeline\
export OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2:3b}"\
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434/v1}"\
export CUDA_AVAILABLE="${CUDA_AVAILABLE:-true}"\
export KOKORO_VOICE_ID="${KOKORO_VOICE_ID:-af_bella}"\
export KOKORO_SAMPLE_RATE="${KOKORO_SAMPLE_RATE:-24000}"\
\
echo "🎙️ Environment configured:"\
echo "   • Ollama Model: $OLLAMA_MODEL"\
echo "   • Ollama URL: $OLLAMA_BASE_URL"\
echo "   • CUDA Available: $CUDA_AVAILABLE"\
echo "   • Kokoro Voice: $KOKORO_VOICE_ID"\
\
# Start the voice pipeline server\
echo "🚀 Starting voice pipeline server..."\
exec python src/main.py\
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

# Start SSH, Ollama, and the pipeline
CMD ["/app/start.sh"]



