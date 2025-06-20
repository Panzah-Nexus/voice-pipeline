# Use NVIDIA CUDA base image for A10 GPU
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Install system dependencies including SSH server
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-dev python3-pip \
    gcc g++ build-essential \
    curl wget \
    ffmpeg \
    libsndfile1 \
    openssh-server \
    git \
    && rm -rf /var/lib/apt/lists/*

# Configure SSH
RUN mkdir /var/run/sshd
RUN echo 'root:runpod' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd

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
ENV PYTHONUNBUFFERED=1

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

# Create startup script that starts SSH and the app
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
# Start SSH daemon
service ssh start
# Start the voice pipeline server
exec python src/main.py
EOF

RUN chmod +x /app/start.sh

# Expose ports
EXPOSE 22 8000

# Start both SSH and the app
CMD ["/app/start.sh"]
