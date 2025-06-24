# 1. Base image: CUDA 12.6.1 + cuDNN on Ubuntu 22.04 for NVIDIA L4
FROM nvidia/cuda:12.6.1-cudnn-runtime-ubuntu22.04

# 2. System packages (including default Python 3.10 on 22.04)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-dev python3-pip \
    gcc g++ build-essential openssh-server espeak-ng libespeak-ng1 \
    curl wget ffmpeg libsndfile1 git \
 && rm -rf /var/lib/apt/lists/*

# 3. SSH setup
RUN mkdir -p /var/run/sshd \
 && echo 'root:runpod' | chpasswd \
 && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
 && sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd

# 4. Make python3.10 the default python and pip
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 \
 && update-alternatives --install /usr/bin/pip    pip    /usr/bin/pip3    1

# 5. Upgrade pip and install uv for isolated Python environments
RUN pip install --upgrade pip setuptools wheel uv

# 6. Install Ollama via official script and pull your model
ARG MODEL=llama3:8b
RUN curl -fsSL https://ollama.com/install.sh | sh \
 && export OLLAMA_HOST=0.0.0.0 \
 && bash -c '\
      OLLAMA_HOST=0.0.0.0 ollama serve &                                \
      until curl -s http://localhost:11434/api/tags >/dev/null; do sleep 1; done \
      && ollama pull $MODEL                                              \
      && pkill ollama'

# 7. Python dependencies: ONNX Runtime GPU (CUDA 12.x)
RUN pip install --no-cache-dir onnxruntime-gpu

# 8. Install Kokoro-ONNX with GPU extra
RUN pip install --no-cache-dir kokoro-onnx[gpu]

# 9. Install Moonshine-ONNX from GitHub
RUN pip install --no-cache-dir git+https://github.com/usefulsensors/moonshine.git#subdirectory=moonshine-onnx

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

ENV ONNX_PROVIDER=CUDAExecutionProvider

# 10. Copy application code and assets
WORKDIR /app
COPY src/ ./src/
COPY assets/ ./assets/

# 11. Entrypoint script to launch SSH, Ollama, then your app
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
service ssh start
echo "Starting Ollama…"
ollama serve &
echo "Waiting for Ollama to be ready…"
timeout 60 bash -c 'until curl -s http://localhost:11434/api/tags >/dev/null; do sleep 1; done'
echo "Launching application…"
exec python src/main.py
EOF
RUN chmod +x /app/start.sh

# 12. Expose ports and default command
EXPOSE 22 8000 11434
CMD ["/app/start.sh"]
