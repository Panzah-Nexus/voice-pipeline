# Voice Pipeline

This project provides a real-time, interruptible voice AI testing pipeline designed to find the optimal hardware and software configuration for real-time coaching avatars. It's built to run locally on constrained hardware (like an NVIDIA L4 GPU) and deliver low-latency, conversational experiences.

The system is designed for realistic role-playing scenarios to help train sales and customer service teams.

## Key Features

*   **Real-time & Interruptible:** Built with `pipecat-ai`, the pipeline supports fluid, natural-sounding conversations.
*   **High-Performance STT/TTS:** Uses `faster-whisper` for speech-to-text and `kokoro-onnx` for text-to-speech, both optimized for GPU execution.
*   **Isolated TTS Environment:** Manages heavy TTS dependencies in a separate Python virtual environment, keeping the main application lightweight.
*   **LLM Integration:** Connects to a local Llama3-8B model served via Ollama.
*   **Deployable with Docker:** Includes Dockerfiles for consistent builds and deployment.
*   **Built-in Observability:** Comes with optional support for metrics and tracing through OpenTelemetry.

## Documentation

For detailed information on architecture, setup, configuration, and troubleshooting, please see the full documentation in the [`docs/`](./docs/README.md) directory.


