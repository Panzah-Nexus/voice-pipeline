# Air-Gapped Voice AI Pipeline on RunPod

A complete, low-latency, and air-gapped voice AI pipeline using **Ultravox** (combined STT + LLM) and **Kokoro TTS**. This project is designed for deployment on **RunPod (NVIDIA L4 GPU)**, providing a powerful, private voice interface without external API dependencies.

## 🚀 Quick Start

### 1. Deploy on RunPod
- Follow the [**Deployment Guide**](docs/deployment_guide.md) to set up a RunPod template using the custom Docker image (`mlbra2006/voice-pipeline-airgapped:uvfix`) and launch a pod.
- Configure the necessary environment variables like `HF_TOKEN`.

### 2. Configure the Client
- Once the pod is running, find its public URL for port 8000.
- Navigate to the `client/websocket-client` directory.
- Create a `.env` file from the `.env.example`.
- Paste the pod's WebSocket URL (obtained from the `/connect` endpoint) into the `VITE_WS_URL` variable in your `.env` file.

### 3. Run the Client
```bash
# Navigate to the web client directory
cd client/websocket-client

# Install dependencies and run
npm install
npm run dev
```
Then, visit `http://localhost:5173` in your browser to use the client.

## 🏗️ Architecture

```
Local Machine (CPU)                RunPod Cloud (NVIDIA L4 GPU)
┌─────────────────┐         ┌──────────────────────────────────┐
│ 🌐 Web Browser  │   WSS   │   🤖 UltravoxWithContext (STT+LLM) │
│ 🔊 Speakers     │ ◄─────► │   🔊 KokoroTTS (Offline TTS)       │
│ 📡 WebSocket    │         │   🚀 Pipecat Framework             │
└─────────────────┘         └──────────────────────────────────┘
```

## 🎯 Key Features

- **Ultravox with Context**: A single, powerful model for speech recognition and language understanding that maintains conversation history.
- **Kokoro TTS**: High-quality, offline text-to-speech, ensuring the entire pipeline remains air-gapped.
- **RunPod Optimized**: Designed to leverage powerful NVIDIA L4 GPUs on RunPod for minimal latency.
- **Real-Time & Low-Latency**: Engineered for natural, real-time voice conversations.
- **Pipecat Framework**: Built on a robust, production-ready framework for voice AI.
- **Air-Gapped by Design**: All AI processing occurs within your private RunPod instance.

## 📁 Project Structure

```
voice-pipeline/
├── src/
│   ├── main.py                     # FastAPI server entry point
│   ├── pipecat_pipeline.py         # Core pipeline logic with Pipecat
│   └── ...                         # AI services
├── docker/
│   └── Dockerfile                  # Container definitions for RunPod
├── docs/                           # All project documentation
├── requirements.txt                # Server dependencies
└── client/                         # Local WebSocket client code
```

## 🔧 Troubleshooting

Refer to the complete [**Troubleshooting Guide**](docs/troubleshooting.md) for detailed solutions to common issues related to RunPod deployment and client setup.

## 💰 Cost

- **RunPod L4**: Cost me $0.43 per hour
- **No API fees**: The air-gapped design means no extra costs for STT, LLM, or TTS APIs.

## 📚 Documentation

See the `docs/` directory for detailed guides on every aspect of this project. The main [**Documentation Hub**](docs/README.md) provides a complete overview.


