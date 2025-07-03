# Voice Pipeline for Real-Time Coaching Avatars

This project is a real-time, interruptible voice AI pipeline designed to find the optimal hardware and software configuration for **real-time coaching avatars**. It's built to run entirely air-gapped on local, consumer-grade hardware (like an NVIDIA L4 GPU) and deliver low-latency, conversational experiences for training simulations.

The system is architected for realistic role-playing scenarios to help train sales and customer service teams.

## Key Technical Features

*   **Cascading Architecture:** A flexible pipeline (ASR → LLM → TTS) that allows for independent component optimization and robust feature support.
*   **Low Latency (~1.1s):** Built with `pipecat-ai` and optimized for real-time, interruptible conversations.
*   **VRAM Efficient (~12GB):** The pipeline is designed to run on accessible hardware, using significantly less VRAM than alternative end-to-end models.
*   **GPU-Accelerated ASR/TTS:** Uses `faster-whisper` for speech-to-text and `kokoro-onnx` for text-to-speech, with full GPU acceleration.
*   **Isolated TTS Subprocess:** Manages conflicting `onnxruntime-gpu` dependencies by running Kokoro TTS in a separate, isolated Python process—a key solution to achieve full GPU utilization.
*   **Local LLM Integration:** Connects to a local, quantized `Llama-3.1-8B` model served via Ollama.
*   **Reproducible Docker Deployment:** A `CUDA 12` based Dockerfile manages all complex dependencies to ensure a consistent and stable environment.

## Documentation

For detailed information on architecture, setup, and model decisions, please see the full documentation in the [`docs/`](./docs/README.md) directory.


