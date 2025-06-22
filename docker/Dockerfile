###############################################################################
# Base: CUDA 11.8 runtime (matches L4 driver + PyTorch cu118 wheels)
###############################################################################
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

###############################################################################
# 1. System packages
###############################################################################


RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-dev python3-pip \
    gcc g++ build-essential openssh-server espeak-ng libespeak-ng1 \
    curl wget ffmpeg libsndfile1 git \
 && rm -rf /var/lib/apt/lists/*




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
# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel uv

###############################################################################
# 4. Install Moonshine ASR
###############################################################################
RUN uv pip install useful-moonshine-onnx@git+https://git@github.com/usefulsensors/moonshine.git#subdirectory=moonshine-onnx

###############################################################################
# 5. Install Ollama and pull model
###############################################################################
RUN curl -fsSL https://ollama.com/install.sh | sh
RUN ollama pull llama3.1

###############################################################################
# 6. Python dependencies from requirements.txt
###############################################################################
# * cu118 wheels for torch/torchvision/torchaudio 2.3.0               ─┐
# * Pipecat with WebSocket + Silero extras                            │
# * bitsandbytes  — optional INT8 quant                               │
# * kokoro-onnx    — ONNX inference wrapper                           │
# * ollama         — Ollama client library                            │

# Copy requirements.txt right before installation to break cache when it changes
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

###############################################################################
# 7. Copy your application code and models
###############################################################################
WORKDIR /app

COPY src/ ./src/
COPY assets/ /app/assets/

# Create startup script that starts SSH, Ollama, and the app
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
# Start SSH daemon
service ssh start
# Start Ollama server in the background
ollama serve &
# Give it a moment to initialize
sleep 3
# Start the voice pipeline server
exec python src/main.py
EOF

RUN chmod +x /app/start.sh

# Expose ports
EXPOSE 22 8000 11434

# Start all services
CMD ["/app/start.sh"]



