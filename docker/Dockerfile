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
#ARG PIPER_VERSION=latest
#RUN set -eux; \
#    mkdir -p /usr/local/bin /usr/local/lib && cd /tmp; \
#    if [ "$PIPER_VERSION" = "latest" ]; then \
#        PIPER_URL=$(curl -s https://api.github.com/repos/rhasspy/piper/releases/latest | \
#                    grep browser_download_url | grep linux_x86_64 | cut -d '"' -f 4); \
#    else \
#        PIPER_URL="https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/piper_linux_x86_64.tar.gz"; \
#    fi; \
#    echo "Downloading Piper from: $PIPER_URL"; \
#    wget -q "$PIPER_URL" -O piper.tar.gz; \
#    tar -xzf piper.tar.gz; \
#    cp piper/piper /usr/local/bin/; \
#    find piper -maxdepth 2 -name '*.so*' -exec cp {} /usr/local/lib/ \;; \
#    ldconfig; rm -rf /tmp/piper*

#RUN mkdir -p /models/piper && \
#    cd /models/piper && \
#    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx && \
#    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

###############################################################################
# 8. Copy application code
###############################################################################
WORKDIR /app

COPY src/ ./src/

# Create startup script that starts SSH and the app
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
# Start SSH daemon
service ssh start
# Start the voice pipeline server
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



