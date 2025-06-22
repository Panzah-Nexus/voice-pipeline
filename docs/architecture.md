# Voice Pipeline Architecture

This document describes the architecture of the air-gapped voice AI pipeline, designed for low-latency performance on RunPod.

## System Overview

The system is split into two primary components:

-   **Local Client**: A lightweight application running on your local machine that handles audio input (microphone) and output (speakers).
-   **Remote Server on RunPod**: A powerful AI pipeline running in a Docker container on an **NVIDIA L4 GPU**. It performs all the heavy lifting: speech-to-text, language understanding, and text-to-speech, without relying on external APIs.

## Architecture Diagram

```
┌─────────────────┐      Secure WebSocket      ┌────────────────────────────────────┐
│   LOCAL CLIENT  │     (WSS Protocol)       │        RUNPOD CONTAINER (NVIDIA L4 GPU)    │
│   (Your Computer) │ ◄──────────────────────► │          (Air-Gapped)              │
│                 │                          │                                    │
│ ┌─────────────┐ │                          │  ┌─────────────────────────────┐   │
│ │ Microphone  │ │                          │  │      PIPECAT FRAMEWORK      │   │
│ │ (Audio In)  │ │                          │  │                             │   │
│ └─────────────┘ │                          │  │  ┌───────────────────────┐  │   │
│        ▲        │                          │  │  │ UltravoxWithContext   │  │   │
│        │        │                          │  │  │ - Combined STT + LLM  │  │   │
│ ┌─────────────┐ │                          │  │  │ - Conversation Memory │  │   │
│ │   Speaker   │ │                          │  │  └───────────────────────┘  │   │
│ │ (Audio Out) │ │                          │  │              │              │   │
│ └─────────────┘ │                          │  │              ▼              │   │
│                 │                          │  │  ┌───────────────────────┐  │   │
│ ┌─────────────┐ │                          │  │  │    KokoroTTSService   │  │   │
│ │ WebSocket   │ │                          │  │  │  - Offline Neural TTS │  │   │
│ │   Client    │ │                          │  │  └───────────────────────┘  │   │
│ └─────────────┘ │                          │  └─────────────────────────────┘   │
└─────────────────┘                          └────────────────────────────────────┘
```

## Data Flow

1.  **Audio Capture (Local → Remote)**: The local client captures microphone audio and streams it in real-time over a secure WebSocket (WSS) connection to the RunPod server.
2.  **AI Processing (Remote & Air-Gapped on RunPod)**:
    -   **`UltravoxWithContextService`**: Receives the raw audio stream, processes it directly into language (bypassing a separate text transcription step), and generates a text response based on the current context and conversation history.
    -   **`KokoroTTSService`**: The generated text is streamed to this offline TTS engine, which synthesizes speech in real-time and streams audio chunks back into the pipeline.
3.  **Audio Playback (Remote → Local)**: The synthesized audio chunks are streamed back to the local client and played through the speakers as they arrive.

## Component Details

-   **Local Client**: Handles audio I/O and WebSocket communication. Can be a simple Python script or a web-based client.
-   **Remote Server (`src/pipecat_pipeline.py`)**: Orchestrated by `pipecat-ai`, it runs the `UltravoxWithContextService`, `KokoroTTSService`, and the FastAPI web server.
-   **Infrastructure (RunPod)**: The server runs in a Docker container on an **NVIDIA L4 GPU**. Models are downloaded on first launch and cached in the pod's volume.

## Performance
For detailed performance metrics and comparisons between different GPUs (like the NVIDIA L4 and A10), see the [**Hardware Guide**](hardware_guide.md).

## Air-Gapped & Security Benefits

-   **No External API Calls**: All AI processing happens inside your private RunPod container.
-   **Data Privacy**: Your voice data is streamed only between your local machine and your private RunPod instance.
-   **Secure Communication**: Communication is encrypted using the standard WSS protocol.
-   **Model Security**: The `HF_TOKEN` is only used for the initial model download.

## Configuration

### Required Environment Variables
```bash
HF_TOKEN=hf_xxx    # Only for initial model download
```
