###############################################################################
# Base: CUDA 11.8 runtime (matches L4 driver + PyTorch cu118 wheels)
###############################################################################
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

###############################################################################
# 1. System packages
###############################################################################
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-dev python3-pip \
        git git-lfs curl wget ffmpeg libsndfile1 \
        gcc g++ build-essential openssh-server espeak-ng libespeak-ng1 && \
    git lfs install && \
    rm -rf /var/lib/apt/lists/*

###############################################################################
# 2. SSH (unchanged)
###############################################################################
RUN mkdir -p /var/run/sshd && \
    echo 'root:runpod' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's@session\\s*required\\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd

###############################################################################
# 3. Python tooling
###############################################################################
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

###############################################################################
# 4. Clone Kokoro model & voices with Git-LFS
###############################################################################
RUN mkdir -p /models && \
    git clone https://huggingface.co/hexgrad/Kokoro-82M /models/kokoro   # downloads ~600 MB via LFS

# Expose the path to Kokoro so the Python package finds it automatically
ENV KOKORO_HOME=/models/kokoro

###############################################################################
# 5. Python dependencies
###############################################################################
# * cu118 wheels for torch/torchvision/torchaudio 2.3.0               ─┐
# * Pipecat with Ultravox + Silero + WebSocket extras                 │
# * bitsandbytes  — optional INT8 quant                               │
# * kokoro         — PyTorch inference wrapper                        │

# Copy requirements.txt right before installation to break cache when it changes
COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir \
        torch==2.3.0+cu118 torchvision==0.18.0+cu118 torchaudio==2.3.0+cu118 \
            --index-url https://download.pytorch.org/whl/cu118 && \
    pip install --no-cache-dir -r /tmp/requirements.txt

###############################################################################
# 6. Piper (kept as-is — comment if unused)
###############################################################################
ARG PIPER_VERSION=latest
RUN set -eux; \
    mkdir -p /usr/local/bin /usr/local/lib && cd /tmp; \
    if [ "$PIPER_VERSION" = "latest" ]; then \
        PIPER_URL=$(curl -s https://api.github.com/repos/rhasspy/piper/releases/latest | \
                    grep browser_download_url | grep linux_x86_64 | cut -d '"' -f 4); \
    else \
        PIPER_URL="https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/piper_linux_x86_64.tar.gz"; \
    fi; \
    echo "Downloading Piper from: $PIPER_URL"; \
    wget -q "$PIPER_URL" -O piper.tar.gz; \
    tar -xzf piper.tar.gz; \
    cp piper/piper /usr/local/bin/; \
    find piper -maxdepth 2 -name '*.so*' -exec cp {} /usr/local/lib/ \;; \
    ldconfig; rm -rf /tmp/piper*

RUN mkdir -p /models/piper && \
    cd /models/piper && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

###############################################################################
# 7. Copy your application code
###############################################################################
WORKDIR /app
# (requirements already copied in layer above)
COPY src/ ./src/

###############################################################################
# 8. Start script (SSH + app)
###############################################################################
RUN printf '%s\n' \
  '#!/bin/bash' \
  'service ssh start' \
  'exec python -m src.main' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 22 8000
CMD ["/app/start.sh"]
