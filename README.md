# Voice Pipeline

This repository contains a voice AI pipeline with [Pipecat](https://github.com/pipecat-ai/pipecat) that runs on **Nvidia A10 GPU** via Cerebrium. The system enables natural voice conversations with AI - speak into your local microphone and hear AI responses through your speakers, with all processing happening on remote GPU infrastructure.

## 🎯 **Quick Start** (Air-Gapped Deployment)

1. **Setup Virtual Environment**: `python3 -m venv venv && source venv/bin/activate`
2. **Get Hugging Face Token**: [Hugging Face](https://huggingface.co/settings/tokens) (No OpenAI needed!)
3. **Configure**: Edit `cerebrium.toml` with your Hugging Face token
4. **Deploy**: `cerebrium deploy`
5. **Connect**: `pip install -r local_client_requirements.txt && python local_client.py`
6. **Talk**: Speak naturally and hear AI responses - all processing stays local!

## 🏗️ **Architecture**

```
┌─────────────────┐    WebSocket/WSS     ┌─────────────────────────────────────┐
│   LOCAL CLIENT  │ ◄────────────────── ► │           CEREBRIUM A10             │
│   (CPU Only)    │                      │                                     │
│                 │                      │  ┌─────────────────────────────┐   │
│ ┌─────────────┐ │                      │  │        VOICE PIPELINE       │   │
│ │ Microphone  │ │                      │  │                             │   │
│ │   Input     │ │                      │  │  ┌───────────────────────┐  │   │
│ └─────────────┘ │                      │  │  │    Ultravox STT       │  │   │
│                 │                      │  │  │   (Speech-to-Text)    │  │   │
│ ┌─────────────┐ │                      │  │  └───────────────────────┘  │   │
│ │  Speaker    │ │                      │  │           │                 │   │
│ │  Output     │ │                      │  │           ▼                 │   │
│ └─────────────┘ │                      │  │  ┌───────────────────────┐  │   │
│                 │                      │  │  │   Ultravox LLM        │  │   │
│ ┌─────────────┐ │                      │  │  │ (Language Generation) │  │   │
│ │ WebSocket   │ │                      │  │  └───────────────────────┘  │   │
│ │   Client    │ │                      │  │           │                 │   │
│ └─────────────┘ │                      │  │           ▼                 │   │
└─────────────────┘                      │  │  ┌───────────────────────┐  │   │
                                         │  │  │     OpenAI TTS        │  │   │
                                         │  │  │  (Text-to-Speech)     │  │   │
                                         │  │  └───────────────────────┘  │   │
                                         │  └─────────────────────────────┘   │
                                         └─────────────────────────────────────┘
```

## 📖 **Documentation**

Comprehensive documentation is available in the [`docs/`](docs/) directory:

| Guide | Purpose | 
|-------|---------|
| [**📋 Deployment Guide**](docs/deployment_guide.md) | Complete setup with A10 GPU on Cerebrium |
| [**🏗️ Architecture**](docs/architecture.md) | System design and technical details |
| [**🔑 API Setup**](docs/api_setup.md) | Getting API keys and configuration |
| [**🎯 Usage Guide**](docs/usage.md) | How to use the system effectively |
| [**🔧 Troubleshooting**](docs/troubleshooting.md) | Common issues and solutions |

**Start here**: [**📖 Documentation Index**](docs/README.md)

## ✨ **Features**

- **🎙️ Real-time voice conversations** with AI
- **☁️ No local GPU required** - all AI runs on Cerebrium A10
- **🔄 Auto-scaling** - scales to zero when not in use
- **💰 Cost-effective** - pay only for GPU time used
- **🔒 Secure** - API keys managed via Cerebrium secrets
- **⚡ Fast** - 2-5 second response times
- **🎛️ Configurable** - Multiple TTS voices and models

## 🛠️ **Technology Stack** (Air-Gapped)

- **AI Models**: [Ultravox](https://github.com/fixie-ai/ultravox) (STT + LLM) + [Piper TTS](https://github.com/rhasspy/piper) (Local)
- **Framework**: [Pipecat](https://github.com/pipecat-ai/pipecat) for AI pipeline orchestration
- **GPU Platform**: [Cerebrium](https://www.cerebrium.ai) with Nvidia A10
- **Local Audio**: Python + sounddevice for microphone/speaker access
- **Communication**: WebSocket for real-time audio streaming
- **Security**: No external API calls - everything runs locally

## 📁 **Directory Structure**

```
voice-pipeline/
├── src/                              # Server code (runs on Cerebrium)
│   ├── main.py                       # Entry point with fallback handling
│   ├── pipecat_pipeline.py          # AI pipeline with Ultravox + TTS
│   ├── simple_test_server.py        # Test server for audio echo
│   ├── websocket_client.py          # WebSocket client (legacy)
│   └── audio_utils.py               # Audio helper functions
├── local_client.py                  # Standalone local client
├── cerebrium.toml                   # Cerebrium deployment config
├── requirements.txt                 # Server dependencies
├── local_client_requirements.txt    # Client-only dependencies
├── docker/
│   └── Dockerfile                   # Container for Cerebrium deployment
└── docs/                           # Comprehensive documentation
    ├── README.md                   # Documentation index
    ├── deployment_guide.md         # Complete setup guide
    ├── architecture.md             # System design details
    ├── api_setup.md               # API keys and configuration
    ├── usage.md                   # How to use the system
    ├── troubleshooting.md          # Common issues and solutions
    ├── pipeline_design.md          # Original design document
    ├── cerebrium_setup.md          # Platform-specific setup
    └── ultravox_setup.md          # Model-specific configuration
```

## 🚀 **Requirements** (Air-Gapped)

### For Deployment (Cerebrium)
- Cerebrium account
- [Hugging Face token](https://huggingface.co/settings/tokens) (for Ultravox)
- No external API keys needed - fully air-gapped!

### For Local Client
- Python 3.10+
- Microphone and speakers
- Internet connection

### Hardware (Provided by Cerebrium)
- Nvidia A10 GPU (24GB VRAM)
- 24GB RAM, 8 CPU cores
- Auto-scaling infrastructure

## 💡 **Use Cases**

- **🤖 Voice Assistant**: Ask questions and get spoken answers
- **🗣️ Language Practice**: Conversation practice and pronunciation
- **♿ Accessibility**: Voice interface for hands-free computing
- **✍️ Creative Collaboration**: Voice brainstorming and content creation
- **📚 Learning**: Educational conversations and explanations

## 💰 **Cost Estimation** (Air-Gapped)

- **Cerebrium A10**: ~$0.50-1.00/hour (only when active)
- **Local Piper TTS**: $0 (runs locally on GPU)
- **Hugging Face**: Free tier sufficient for most use
- **Total**: ~$0.50-1.00/hour GPU time only - no per-conversation fees!

*Costs scale to zero when not in use thanks to Cerebrium auto-scaling.*

## 🔒 **Security & Privacy** (Air-Gapped)

- **🔐 Single API key** - only Hugging Face token needed
- **🛡️ WSS encryption** for all communication
- **🗑️ No data storage** - audio processed in memory only
- **🚫 No external API calls** - everything runs locally on GPU
- **🌐 Air-gapped deployment** - perfect for UAE compliance requirements

## 🆘 **Need Help?**

1. **Getting Started**: See [Deployment Guide](docs/deployment_guide.md)
2. **Issues**: Check [Troubleshooting](docs/troubleshooting.md)
3. **API Problems**: Review [API Setup](docs/api_setup.md)
4. **Usage Questions**: Read [Usage Guide](docs/usage.md)
5. **Technical Details**: Study [Architecture](docs/architecture.md)

## 📜 **License**

This project is open source. See individual dependencies for their respective licenses.

---

**Ready to start?** 👉 [**Get Started with Documentation**](docs/README.md)

