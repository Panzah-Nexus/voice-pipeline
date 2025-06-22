# Source Code Structure

This directory contains the core server-side Python code for the voice pipeline.

## Core Files

### `main.py`
The FastAPI entry point for the voice pipeline server. It handles server startup, WebSocket routing, and basic management endpoints like `/connect`.

### `pipecat_pipeline.py`
This is the heart of the application. It uses the `pipecat-ai` framework to wire together all the necessary AI services:
-   Integrates `UltravoxWithContextService` for unified, low-latency STT and LLM processing.
-   Uses the custom `KokoroTTSService` for fully offline, air-gapped text-to-speech.
-   Manages the WebSocket transport layer and client connections.

### `ultravox_with_context.py`
A custom Pipecat service that extends the base `UltravoxSTTService` to include conversation memory. This allows the AI to maintain context across multiple turns, leading to more natural conversations.

### `kokoro_tts_service.py`
A custom Pipecat-compatible TTS service for the Kokoro engine. It receives text from the pipeline and streams synthesized audio back in real-time.

## Architecture Notes

1.  **Air-Gapped Design**: All AI processing (STT, LLM, TTS) happens on the deployed GPU without external API calls during operation.
2.  **Unified STT/LLM**: The use of `UltravoxWithContextService` is a key design choice to minimize latency by avoiding a separate transcription step.
3.  **Dockerized Deployment**: The models are downloaded when the Docker container is first initialized on RunPod, ensuring they are cached in the pod's volume for fast subsequent startups.

