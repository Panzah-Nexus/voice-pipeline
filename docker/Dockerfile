FROM nvidia/cuda:12.3.1-runtime-ubuntu22.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.11 python3.11-venv python3-pip ffmpeg libsndfile1 && \
    ln -sf /usr/bin/python3.11 /usr/local/bin/python && \
    pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/
WORKDIR /app
EXPOSE 8000
CMD ["python", "-m", "src.pipecat_pipeline"]
