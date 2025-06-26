# 1. Base image: CUDA 12.6.1 + cuDNN on Ubuntu 22.04 for NVIDIA L4
FROM nvidia/cuda:12.6.1-cudnn-runtime-ubuntu22.04

# Set the working directory to /workspace to align with RunPod's persistent volume.
WORKDIR /workspace

# 2. System packages (including default Python 3.10 on 22.04)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-dev python3-pip python3-venv \
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

# 7. Create **isolated** virtual-env for Kokoro TTS to avoid dependency clashes
#    This venv is created at an absolute path, so it's not affected by WORKDIR.
RUN python3 -m venv /venv/tts \
 && /venv/tts/bin/pip install --upgrade pip wheel \
 && /venv/tts/bin/pip install --no-cache-dir 'kokoro-onnx[gpu]' \
 && /venv/tts/bin/pip uninstall -y onnxruntime-gpu onnxruntime \
 && /venv/tts/bin/pip install 'onnxruntime-gpu' \
 && /venv/tts/bin/pip install pipecat-ai

# 8. Install main application dependencies for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

# 9. Copy the rest of the application code
COPY . .

# 10. Entrypoint script to launch SSH, Ollama, then your app
RUN cat > /workspace/start.sh <<EOF
#!/bin/bash
service ssh start
echo "Starting Ollama…"
ollama serve &
echo "Waiting for Ollama to be ready…"
timeout 60 bash -c 'until curl -s http://localhost:11434/api/tags >/dev/null; do sleep 1; done'
echo "Launching application…"
exec python src/main.py
EOF
RUN chmod +x /workspace/start.sh

# 11. Expose ports and default command
EXPOSE 22 8000 11434
CMD ["/workspace/start.sh"]
