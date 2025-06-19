# Voice AI Pipeline - Air-Gapped Deployment

A complete voice AI pipeline using **Ultravox** (combined STT + LLM) and **Piper TTS** for fully local, air-gapped deployment on NVIDIA A10 GPUs via Cerebrium.

## 🚀 Quick Start

### 1. Setup Local Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install local client dependencies
pip install -r local_client_requirements.txt
```

### 2. Configure Cerebrium
Edit `cerebrium.toml` and add your Hugging Face token:
```toml
[cerebrium.secrets]
HF_TOKEN = "hf_YOUR_ACTUAL_TOKEN_HERE"
```

### 3. Deploy to Cerebrium
```bash
# Install Cerebrium CLI
pip install cerebrium

# Login
cerebrium login

# Deploy
cerebrium deploy
```

### 4. Connect and Talk
```bash
# Set server URL
export WS_SERVER="wss://your-deployment-id.cerebrium.app/ws"

# Run client
python local_client.py
```

## 🏗️ Architecture

```
Local Machine (CPU)          Cerebrium Cloud (A10 GPU)
┌─────────────────┐         ┌────────────────────────┐
│ 🎙️ Microphone   │   WSS   │ 🤖 Ultravox (STT+LLM)  │
│ 🔊 Speakers     │ ◄─────► │ 🔊 Piper TTS           │
│ 📡 WebSocket    │         │ 🚀 Pipecat Framework   │
└─────────────────┘         └────────────────────────┘
```

## 🎯 Key Features

- **Ultravox**: Single model for both speech recognition and language understanding
- **Piper TTS**: Local neural text-to-speech (no APIs)
- **Air-Gapped**: All AI processing on GPU, no external API calls
- **Real-Time**: Low-latency voice conversations
- **Pipecat**: Production-ready voice pipeline framework

## 📁 Project Structure

```
voice-pipeline/
├── src/
│   ├── main.py                 # Entry point
│   ├── pipecat_pipeline.py     # Main pipeline with Pipecat
│   └── piper_tts_service.py    # Custom Piper TTS service
├── docker/
│   └── Dockerfile              # GPU-enabled container
├── local_client.py             # Audio capture/playback client
├── cerebrium.toml              # Deployment configuration
├── requirements.txt            # Server dependencies (GPU)
└── local_client_requirements.txt  # Client dependencies (lightweight)
```

## 🔧 Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check `WS_SERVER` environment variable
   - Verify deployment is running: `cerebrium list`

2. **No Audio Input/Output**
   - Check audio devices: `python -c "import sounddevice; print(sounddevice.query_devices())"`
   - Ensure microphone/speakers are connected

3. **GPU Memory Issues**
   - The 8B Ultravox model requires ~16GB VRAM
   - A10 has 24GB, should work fine

## 💰 Cost

- **Cerebrium A10**: ~$0.50-1.00/hour when active
- **Auto-scaling**: Scales to zero when idle (no cost)
- **No API fees**: All models run locally on GPU

## 📚 Documentation

See the `docs/` directory for detailed guides:
- [Architecture](docs/architecture.md)
- [Deployment Guide](docs/deployment_guide.md) 
- [API Setup](docs/api_setup.md)
- [Ultravox Setup](docs/ultravox_setup.md)
- [Piper Setup](docs/piper_setup.md)


