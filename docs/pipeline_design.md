# Pipeline Design

This document outlines the design goals and architecture for the air-gapped voice pipeline. The primary objective is to develop a high-performance, low-latency voice AI system that can be tested in a cloud environment (RunPod) and then deployed to a local, on-premises NVIDIA GPU with minimal code changes.

This approach allows for rapid development and iteration using powerful cloud GPUs like the NVIDIA L4, while ensuring the final product meets the client's requirement for a fully air-gapped solution on a local NVIDIA A10 or similar GPU.

## Core Components

1.  **WebSocket Client/Server**
    -   The **client** is a lightweight application that runs on a user's local machine. It captures microphone audio and streams it to the remote server. It also receives and plays the synthesized audio response.
    -   The **server** runs inside the main Docker container on the GPU instance (RunPod for development, local A10 for production). It manages the WebSocket connection and orchestrates the AI services.

2.  **Pipecat Framework**
    -   Pipecat serves as the central orchestration framework, managing the flow of audio and data between the various components of the pipeline. It handles interruptions, manages the real-time stream, and connects the STT, LLM, and TTS services.

3.  **AI Services**
    -   **`UltravoxWithContextService`**: This custom service combines STT and LLM functionality into one. It uses the `fixie-ai/ultravox-v0_5-llama-3_1-8b` model from Hugging Face for fast, context-aware processing.
    -   **`KokoroTTSService`**: This service provides offline, high-quality text-to-speech synthesis, ensuring the pipeline remains fully air-gapped during operation.

4.  **Docker**
    -   The entire server-side application is encapsulated in a single Docker image. This image includes Python, PyTorch with CUDA support, all Pipecat and model dependencies, and the application source code.
    -   The same Docker image built for RunPod testing can be used for the final on-premises deployment, ensuring consistency between environments.

## Deployment Strategy

1.  **Development & Testing (RunPod on an NVIDIA L4)**
    -   Primary development and testing occur on **RunPod** to leverage easy access to high-end hardware.
    -   The RunPod pod exposes the WebSocket port to the internet for testing with a local client.

2.  **Production (On-Premises on an NVIDIA A10/L4)**
    -   The ultimate goal is to deploy the same Docker container on a local, air-gapped server.
    -   The target hardware for this is a server equipped with an **NVIDIA A10** or **NVIDIA L4** GPU.
    -   No code changes should be necessary for this transition, other than changing the WebSocket URL the client connects to.

## Key References

-   **Pipecat Framework**: [github.com/pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat)
-   **Ultravox Model**: [huggingface.co/fixie-ai/ultravox-v0_5-llama-3_1-8b](https://huggingface.co/fixie-ai/ultravox-v0_5-llama-3_1-8b)
-   **RunPod**: [www.runpod.io](https://www.runpod.io)
-   **Hardware Options**: [Hardware Guide](hardware_guide.md)

