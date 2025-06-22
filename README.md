# Air-Gapped Voice AI Pipeline on RunPod

A complete, low-latency, and air-gapped voice AI pipeline using **Ultravox** (combined STT + LLM) and **Kokoro TTS**. This project is designed for deployment on **RunPod (NVIDIA L4 GPU)**, providing a powerful, private voice interface without external API dependencies.

## 🚀 Quick Start

### 1. Configure RunPod
- Select a RunPod template with PyTorch and CUDA support.
- Set the required environment variables in the template settings:
  - `HF_TOKEN`: Your Hugging Face token for model downloads.
  - `KOKORO_VOICE_ID`: The specific TTS voice to use (e.g., `af_bella`).
- Set the container's start command to: `python src/main.py`

### 2. Deploy and Connect
- Deploy your pod on RunPod.
- Once running, find your pod's WebSocket endpoint. The application provides a `/connect` endpoint to help discover this URL.
- Use a local WebSocket client to connect to the endpoint and start talking.

### 3. Setup Local Client
The recommended client is the web client located in `client/websocket-client/`.

```bash
# Navigate to the web client directory
cd client/websocket-client

# Install dependencies
npm install
```

Before running, you must update the `VITE_WS_URL` in the `.env` file (or create one from `.env.example`) to point to your RunPod's WebSocket URL.

### 4. Run Local Client
```bash
# Run the development server
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
- **Air-Gapped by Design**: All AI processing occurs within your private RunPod instance. No data is sent to third-party APIs.

## 📁 Project Structure

```
voice-pipeline/
├── src/
│   ├── main.py                     # FastAPI server entry point
│   ├── pipecat_pipeline.py         # Core pipeline logic with Pipecat
│   ├── ultravox_with_context.py    # Custom Ultravox service with memory
│   └── kokoro_tts_service.py       # Custom Kokoro TTS service
├── docker/
│   └── Dockerfile                  # Container definition for RunPod
├── docs/                           # All project documentation
├── requirements.txt                # Server dependencies for RunPod
└── client/                         # Local WebSocket client code
```

## 🔧 Troubleshooting

Common issues often relate to incorrect environment variables on RunPod, network connectivity, or audio device configuration on your local machine.

Refer to the complete [**Troubleshooting Guide**](docs/troubleshooting.md) for detailed solutions.

## 💰 Cost

- **RunPod L4**: Billed by the hour. Check RunPod's pricing for the most current rates.
- **No API fees**: The air-gapped design means no extra costs for STT, LLM, or TTS APIs.
Cost me $0.43 per hour

## 📚 Documentation

See the `docs/` directory for detailed guides on every aspect of this project. The main [**Documentation Hub**](docs/README.md) provides a complete overview.


