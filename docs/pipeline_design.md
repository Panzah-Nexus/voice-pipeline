# Pipeline Design

This document outlines the design goals for the voice pipeline. The main idea is to develop and test using cloud GPU resources and then deploy locally on an NVIDIA A10 with no code changes.

## Components

1. **WebSocket Client/Server**
   - Client runs on your local machine, capturing microphone audio and sending it to a remote GPU server.
   - Server is inside the Docker container, running the inference pipeline and streaming audio responses back.
2. **Pipecat**
   - Orchestrates the components in the pipeline.
   - We rely on the **UltravoxSTTService** for both speech-to-text and LLM capabilities.
   - `CartesiaTTSService` produces the spoken response.
3. **Docker**
   - The Docker image includes Python, PyTorch with CUDA, pipecat, and Ultravox dependencies.
   - Build once for the remote GPU, then reuse the same image locally.
4. **Cerebrium Cloud**
   - Optional environment for remote testing if you don't have direct access to the GPU.
   - Start the container and expose the websocket port to the public internet (use TLS/SSH tunnel for security).
5. **Local Deployment**
   - On the A10 GPU, run the same Docker image. No code changes should be required.

## File Overview

- `src/pipecat_pipeline.py` – Set up pipecat with STT, LM, and Ultravox TTS components.
- `src/websocket_client.py` – Capture microphone audio and stream to the remote server.
- `src/audio_utils.py` – Helper functions for audio capture/playback.
- `docker/Dockerfile` – Build environment with Pipecat and Ultravox.

## Environment

Set the following variables when running the container:

- `HF_TOKEN` – Hugging Face token used by UltravoxSTTService
- `CARTESIA_API_KEY` – API key for the Cartesia TTS service

## References

- Pipecat documentation: <https://github.com/spidercat/pipecat>
- Ultravox: <https://github.com/rhasspy/ultravox>
- Cerebrium: <https://www.cerebrium.ai>

