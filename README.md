# Local Voice AI Pipeline on RunPod

A complete, low-latency, and self-hosted voice AI pipeline using **Moonshine** (STT), **Ollama** (LLM), and **Kokoro** (TTS). This project is designed for deployment on **RunPod (NVIDIA L4 GPU)**, providing a powerful, private voice interface without external API dependencies.

## 🚀 Quick Start

### 1. Deploy on RunPod
- Follow the [**Deployment Guide**](docs/deployment_guide.md) to set up a RunPod template using the custom Docker image you build from this repository.
- Ensure you have an `assets` folder in the project root containing your Kokoro models (`kokoro-v1.0.onnx`, `voices-v1.0.bin`).

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

The entire pipeline runs inside a single Docker container on a RunPod GPU instance.

```
Local Machine (CPU)                RunPod Cloud (NVIDIA L4 GPU)
┌─────────────────┐         ┌──────────────────────────────────────────┐
│ 🌐 Web Browser  │   WSS   │   Moonshine (STT) -> Ollama (LLM) -> Kokoro (TTS) │
│ 🔊 Speakers     │ ◄─────► │   (Running as background service)       │
│ 📡 WebSocket    │         │   🚀 Pipecat Framework                  │
└─────────────────┘         └──────────────────────────────────────────┘
```

The startup script inside the container automatically launches the `ollama` server before starting the Pipecat pipeline.

## 🎯 Key Features

- **Cascaded Local Pipeline**: Best-in-class local models for each task: Moonshine (STT), Ollama (LLM), and Kokoro (TTS).
- **Ollama with Llama 3.1 Pre-packaged**: The Docker image comes with the Ollama server and the `llama3.1` model pre-installed for fast startups.
- **RunPod Optimized**: Designed to leverage powerful NVIDIA L4 GPUs on RunPod for minimal latency.
- **Real-Time & Low-Latency**: Engineered for natural, real-time voice conversations with interruption handling.
- **Pipecat Framework**: Built on a robust, production-ready framework for voice AI.
- **Self-Hosted & Private**: All AI processing occurs within your private RunPod instance.

## 📁 Project Structure

```
voice-pipeline/
├── src/
│   ├── main.py                     # FastAPI server entry point
│   ├── pipecat_pipeline.py         # Core pipeline logic with Pipecat
│   └── ...
├── docker/
│   └── Dockerfile                  # Container definition for RunPod
├── assets/
│   ├── kokoro-v1.0.onnx            # Kokoro TTS Model
│   └── voices-v1.0.bin             # Kokoro TTS Voices
├── docs/                           # All project documentation
├── requirements.txt                # Server dependencies
└── client/                         # Local WebSocket client code
```

## 🔧 Troubleshooting

Refer to the complete [**Troubleshooting Guide**](docs/troubleshooting.md) for detailed solutions to common issues related to RunPod deployment and client setup.

## 💰 Cost

- **RunPod L4**: Approx. $0.43 per hour (check current pricing)
- **No API fees**: The self-hosted design means no extra costs for STT, LLM, or TTS APIs.

## 📚 Documentation

See the `docs/` directory for detailed guides on every aspect of this project. The main [**Documentation Hub**](docs/README.md) provides a complete overview.


