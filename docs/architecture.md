# Voice Pipeline Architecture

This document describes the architecture of the air-gapped voice AI pipeline system using Pipecat framework.

## System Overview

The voice pipeline consists of two main components:
- **Local Client**: Handles audio input/output on your local machine
- **Remote Server**: Processes AI on Cerebrium's A10 GPU with no external API dependencies

## Architecture Diagram

```
┌─────────────────┐    WebSocket/WSS     ┌────────────────────────────────────┐
│   LOCAL CLIENT  │ ◄────────────────── ►│           CEREBRIUM A10            │
│   (CPU Only)    │                      │          AIR-GAPPED                │
│                 │                      │                                    │
│ ┌─────────────┐ │                      │  ┌─────────────────────────────┐   │
│ │ Microphone  │ │                      │  │    PIPECAT FRAMEWORK        │   │
│ │   Input     │ │                      │  │                             │   │
│ └─────────────┘ │                      │  │  ┌───────────────────────┐  │   │
│                 │                      │  │  │  Ultravox Model       │  │   │
│ ┌─────────────┐ │                      │  │  │  - Speech-to-Text     │  │   │
│ │  Speaker    │ │                      │  │  │  - Language Model     │  │   │
│ │  Output     │ │                      │  │  │  (Combined in One)    │  │   │
│ └─────────────┘ │                      │  │  └───────────────────────┘  │   │
│                 │                      │  │           │                 │   │
│ ┌─────────────┐ │                      │  │           ▼                 │   │
│ │ WebSocket   │ │                      │  │  ┌───────────────────────┐  │   │
│ │   Client    │ │                      │  │  │    Piper TTS          │  │   │
│ └─────────────┘ │                      │  │  │  - Local Neural TTS   │  │   │
└─────────────────┘                      │  │  │  - GPU Accelerated    │  │   │
                                         │  │  │  - 50+ Languages      │  │   │
                                         │  │  └───────────────────────┘  │   │
                                         │  └─────────────────────────────┘   │
                                         └────────────────────────────────────┘
```

## Data Flow

### 1. Audio Capture (Local → Remote)
1. Microphone captures audio at 16kHz, 16-bit, mono
2. Audio chunked into 0.5-second segments (8KB each)
3. Chunks sent via WebSocket to Cerebrium
4. Server accumulates ~5 seconds of audio

### 2. AI Processing (Remote - Fully Air-Gapped)
1. **Ultravox**: Single model processes audio directly to generate text response
   - No separate STT step - audio is directly encoded into LLM space
   - ~150ms time-to-first-token on A10 GPU
   - Generates 50-100 tokens per second
2. **Piper TTS**: Converts response text to speech locally on GPU
   - Real-time synthesis with <200ms latency
   - High-quality neural voices
   - No internet connection required

### 3. Audio Playback (Remote → Local)
1. Audio chunks received via WebSocket
2. Audio played through local speakers
3. Process repeats for continuous conversation

## Component Details

### Local Client (`local_client.py`)
- **Audio I/O**: Microphone capture and speaker output
- **WebSocket Client**: Secure connection to Cerebrium
- **Dependencies**: websockets, sounddevice, numpy

### Remote Server (`src/pipecat_pipeline.py`)
- **Pipecat Framework**: Orchestrates the voice pipeline
- **Ultravox Service**: Combined STT+LLM for faster processing
- **Piper TTS Service**: Local neural text-to-speech
- **FastAPI Server**: WebSocket endpoint and health checks

### Infrastructure (Cerebrium)
- **Hardware**: Nvidia A10 GPU, 24GB RAM, 8 CPU cores
- **Scaling**: 0-2 instances, auto-scaling based on demand
- **Container**: Docker with CUDA support
- **Models**: Pre-loaded on deployment for instant availability

## Performance

### Latency Breakdown
- Audio capture: 5 seconds (buffering)
- Network upload: 50-200ms
- Ultravox processing: 150-600ms (combined STT+LLM)
- Piper TTS processing: 100-200ms
- Network download: 100-300ms
- Total round-trip: ~1-2 seconds (60% faster than cascaded approach)

### Resource Usage
- GPU memory: ~12-16GB for models
- CPU usage: 20-40% during processing
- RAM usage: ~8-12GB for model loading
- Network: ~50KB/second sustained

## Security & Air-Gap Benefits

- **No External APIs**: All processing happens on-device
- **Data Privacy**: Audio never leaves your infrastructure
- **Encryption**: WSS (secure WebSocket) for communication
- **Model Security**: Models loaded from local storage
- **Token Usage**: HF token only for initial model download

## Configuration

### Required Environment Variables
```bash
HF_TOKEN=hf_xxx    # Only for initial model download
```

### Optional Configuration
```bash
PIPER_MODEL=en_US-lessac-medium  # Piper voice selection
PIPER_SAMPLE_RATE=22050          # Audio sample rate
WS_SERVER=wss://...              # Server URL for local client
```

## Why Ultravox + Piper?

### Ultravox Advantages
- **Single Model**: Combines STT and LLM, reducing latency by ~50%
- **Direct Audio Processing**: No transcription errors or information loss
- **Context Aware**: Better understanding of tone, emotion, and context
- **Efficient**: Less GPU memory than running separate models

### Piper Advantages
- **Fully Offline**: No API calls or internet dependency
- **Fast**: Real-time synthesis on GPU
- **Quality**: Neural voices comparable to cloud services
- **Multilingual**: 50+ languages with multiple voices each
- **Open Source**: Complete control over the TTS pipeline

## Scaling Strategy

- **Horizontal**: Auto-scaling up to 2 A10 instances
- **Vertical**: A10 GPU optimal for 8B Ultravox model
- **Cold Start**: ~30-60 seconds for first request
- **Warm Instances**: <1 second response time
- **Concurrency**: 3-5 connections per instance depending on model 