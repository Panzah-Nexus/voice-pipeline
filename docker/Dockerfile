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

# Upgrade pip and install uv
RUN pip install --upgrade pip setuptools wheel uv

###############################################################################
# 4. Install Ollama and pull model
###############################################################################
ARG MODEL=llama3:8b
RUN curl -fsSL https://ollama.com/install.sh | sh
ENV OLLAMA_HOST=0.0.0.0
# Start Ollama, wait for it to be ready, pull the model, then stop it.
# This is done in a single RUN command to ensure the server is available for the pull.
RUN bash -c '\
  OLLAMA_HOST=0.0.0.0 ollama serve &                                                   \
  until curl -s http://localhost:11434/api/tags >/dev/null; do sleep 1; done && \
  ollama pull $MODEL &&                                            \
  pkill ollama'

###############################################################################
# 5. Python dependencies (Installed in specific order)
###############################################################################

# First, install libraries that need to be present before others
RUN pip install --no-cache-dir ollama
RUN pip install --no-cache-dir kokoro-onnx

# Second, install Moonshine from Git
RUN uv pip install --system useful-moonshine-onnx@git+https://git@github.com/usefulsensors/moonshine.git#subdirectory=moonshine-onnx

# Finally, install the rest of the requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

###############################################################################
# 6. Copy your application code and models
###############################################################################
WORKDIR /app

COPY src/ ./src/
# This line assumes you have an `assets` directory with the Kokoro models
# in the root of your project.
COPY assets/ /app/assets/

# Create a robust startup script with a health check
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash

# Start SSH daemon
service ssh start

# Start Ollama server in the background
echo "Starting Ollama server..."
ollama serve &

# Wait for the Ollama server to be ready
echo "Waiting for Ollama to be ready..."
timeout 60 bash -c 'until curl -s http://localhost:11434/api/tags > /dev/null; do echo -n "."; sleep 1; done'

echo
echo "Ollama server is ready."

# Start the voice pipeline server
echo "Starting Pipecat voice pipeline..."
exec python src/main.py
EOF

RUN chmod +x /app/start.sh

# Expose ports
EXPOSE 22 8000 11434

# Start all services
CMD ["/app/start.sh"]