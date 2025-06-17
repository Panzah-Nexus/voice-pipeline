# Voice Pipeline Architecture

This document describes the architecture of the voice AI pipeline system.

## System Overview

The voice pipeline consists of two main components:
- **Local Client**: Handles audio input/output on your local machine
- **Remote Server**: Processes AI on Cerebrium's A10 GPU

## Architecture Diagram

```
┌─────────────────┐    WebSocket/WSS     ┌─────────────────────────────────────┐
│   LOCAL CLIENT  │ ◄────────────────── ► │           CEREBRIUM A10             │
│   (CPU Only)    │                      │          AIR-GAPPED                 │
│                 │                      │                                     │
│ ┌─────────────┐ │                      │  ┌─────────────────────────────┐   │
│ │ Microphone  │ │                      │  │        VOICE PIPELINE       │   │
│ │   Input     │ │                      │  │                             │   │
│ └─────────────┘ │                      │  │  ┌───────────────────────┐  │   │
│                 │                      │  │  │    Ultravox STT       │  │   │
│ ┌─────────────┐ │                      │  │  │   (Speech-to-Text)    │  │   │
│ │  Speaker    │ │                      │  │  └───────────────────────┘  │   │
│ │  Output     │ │                      │  │           │                 │   │
│ └─────────────┘ │                      │  │           ▼                 │   │
│                 │                      │  │  ┌───────────────────────┐  │   │
│ ┌─────────────┐ │                      │  │  │   Ultravox LLM        │  │   │
│ │ WebSocket   │ │                      │  │  │ (Language Generation) │  │   │
│ │   Client    │ │                      │  │  └───────────────────────┘  │   │
│ └─────────────┘ │                      │  │           │                 │   │
└─────────────────┘                      │  │           ▼                 │   │
                                         │  │  ┌───────────────────────┐  │   │
                                         │  │  │    LOCAL Piper TTS    │  │   │
                                         │  │  │   (Text-to-Speech)    │  │   │
                                         │  │  │     GPU Accelerated   │  │   │
                                         │  │  └───────────────────────┘  │   │
                                         │  └─────────────────────────────┘   │
                                         └─────────────────────────────────────┘
```

## Data Flow

### 1. Audio Capture (Local → Remote)
1. Microphone captures audio at 16kHz, 16-bit, mono
2. Audio chunked into 0.5-second segments (8KB each)
3. Chunks sent via WebSocket to Cerebrium
4. Server accumulates ~5 seconds of audio

### 2. AI Processing (Remote)
1. **Ultravox STT**: Converts audio to text
2. **Ultravox LLM**: Generates conversational response
3. **OpenAI TTS**: Converts response text to speech
4. Audio streamed back to client

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
- **Ultravox Service**: Speech-to-text and language generation
- **Local Piper TTS**: GPU-accelerated text-to-speech (air-gapped)
- **FastAPI Server**: WebSocket endpoint and health checks

### Infrastructure (Cerebrium)
- **Hardware**: Nvidia A10 GPU, 24GB RAM, 8 CPU cores
- **Scaling**: 0-2 instances, auto-scaling based on demand
- **Container**: Docker with CUDA support

## Performance

### Latency Breakdown
- Audio capture: 5 seconds (buffering)
- Network upload: 50-200ms
- STT processing: 500-1000ms
- LLM generation: 500-1500ms
- TTS processing: 800-1200ms
- Network download: 100-300ms
- Total round-trip: ~2-5 seconds

### Resource Usage
- GPU memory: ~8-12GB for models
- CPU usage: 20-40% during processing
- RAM usage: ~4-8GB for buffering
- Network: ~50KB/second sustained

## Security

- **Encryption**: WSS (secure WebSocket) for all communication
- **API Keys**: Stored securely in Cerebrium secrets
- **Data Privacy**: Audio processed in memory only, not stored
- **Access Control**: Restricted to authorized tokens

## Configuration

### Required Environment Variables
```bash
HUGGING_FACE_TOKEN=hf_xxx    # For Ultravox model access
```

### Optional Configuration
```bash
PIPER_MODEL=en_US-lessac-medium  # Piper TTS model selection
PIPER_SAMPLE_RATE=22050          # Audio sample rate
WS_SERVER=wss://...              # Server URL for local client
```

## Scaling Strategy

- **Horizontal**: Auto-scaling up to 2 A10 instances
- **Vertical**: A10 GPU optimal for current models
- **Cold Start**: ~30-60 seconds for first request
- **Warm Instances**: <1 second response time
- **Concurrency**: 5 connections per instance 