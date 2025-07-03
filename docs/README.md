# Voice Pipeline Documentation

## 📚 Documentation Structure

### Reading Order
1. **[Quick Start](./1_quick_start.md)** - Get running in 5 minutes
2. **[Architecture](./2_architecture.md)** - System design and data flow
3. **[Model Decisions](./3_model_decisions.md)** - Framework choices and alternatives
4. **[Performance](./4_performance.md)** - Latency analysis and benchmarks
5. **[Improvements](./5_improvements.md)** - Future enhancements and optimizations

### Reference Files
- **[Configuration](./6_configuration.md)** - Environment variables and settings
- **[Troubleshooting](./7_troubleshooting.md)** - Common issues and solutions
- **[Contributing](./8_contributing.md)** - Development guidelines

## 🎯 Quick Overview

**Current Pipeline**: Faster Whisper ASR → Ollama LLM → Kokoro TTS
- **Framework**: Pipecat + RTVI
- **Deployment**: Docker container with GPU support
- **Latency**: [TO BE ADDED] - What's your current end-to-end latency?
- **Interruptibility**: Yes - users can speak over AI responses

## 🚀 Getting Started

```bash
# Clone and setup
git clone [YOUR_REPO_URL]
cd voice-pipeline
docker build -t voice-pipeline .
docker run -p 8000:8000 --gpus all voice-pipeline
```

**Prerequisites**: [TO BE ADDED]
- What GPU requirements do you have?
- What models need to be downloaded?
- Any specific environment variables?

## 📊 Current Performance

**Latency Breakdown**: [TO BE ADDED]
- VAD detection: ___ ms
- STT processing: ___ ms  
- LLM inference: ___ ms
- TTS generation: ___ ms
- Total end-to-end: ___ ms

**Resource Usage**: [TO BE ADDED]
- GPU memory: ___ GB
- CPU usage: ___ %
- Memory usage: ___ GB

## 🔧 Key Components

1. **Faster Whisper ASR** - Speech-to-text with [TO BE ADDED] accuracy
2. **Ollama LLM** - Local Llama 3.1 8B model
3. **Kokoro TTS** - Offline text-to-speech
4. **Pipecat Framework** - Pipeline orchestration
5. **RTVI** - Real-time voice interaction

## 📈 Success Metrics

- **Response Time**: [TO BE ADDED] - What's your target latency?
- **Accuracy**: [TO BE ADDED] - How accurate is the STT/LLM?
- **Uptime**: [TO BE ADDED] - What's your deployment reliability?
- **Cost**: [TO BE ADDED] - What's your current deployment cost?

---

**Next**: Read [Quick Start](./1_quick_start.md) to get running, then [Architecture](./2_architecture.md) to understand the system. 