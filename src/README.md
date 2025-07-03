# Source Code Structure

This directory contains the core server-side Python code for the voice pipeline. The architecture is a cascading pipeline (ASR -> LLM -> TTS) orchestrated by the `pipecat-ai` framework.

## Core Files

### `main.py`
The FastAPI entry point for the voice pipeline server. It handles:
- Server startup and shutdown.
- The `/ws` endpoint for WebSocket connections.
- A `/connect` endpoint for clients to retrieve the correct WebSocket URL.

### `pipecat_pipeline.py`
This is the heart of the application. It defines the `pipecat` pipeline and wires together all the necessary AI services:
-   `WhisperSTTService`: Transcribes user audio to text using a local, GPU-accelerated Faster Whisper model.
-   `OLLamaLLMService`: Manages conversation history and sends prompts to the local Llama 3.1 model.
-   `KokoroSubprocessTTSService`: A custom service that sends text to the Kokoro TTS engine and receives synthesized audio back. See below for why this runs in a subprocess.

### `kokoro/`
This directory contains the implementation for our custom Kokoro TTS service.
-   **`tts_subprocess_wrapper.py`**: The `pipecat` service that is directly used in the main pipeline. It manages communication with the TTS subprocess.
-   **`tts_subprocess_server.py`**: The server that runs inside the isolated subprocess. It loads the Kokoro ONNX model and performs the text-to-speech inference.
-   **`tts.py`**: A direct Python wrapper around the Kokoro ONNX model logic.

## Key Architecture Note: Subprocess Isolation

A major technical challenge was resolving the `onnxruntime-gpu` dependency conflicts between the ASR and TTS models. The solution was to run the entire Kokoro TTS engine in an **isolated subprocess** with its own Python environment. This allows both the main pipeline and the TTS service to have conflicting dependencies while still achieving full GPU acceleration for all models, which was critical for meeting the low-latency requirements of the project.

