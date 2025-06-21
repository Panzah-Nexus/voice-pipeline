# 🎙️ Local Voice Pipeline

**Fully local, air-gapped voice AI pipeline** using open-source components with no external dependencies.

## 🏗️ Architecture

### **Cascaded Pipeline:**
```
Audio Input → Whisper STT → Ollama LLM → Kokoro TTS → Audio Output
```

### **Components:**
- **🎙️ STT**: WhisperSTTService (local, CUDA-accelerated)
- **🧠 LLM**: OLLamaLLMService (local models with conversation memory) 
- **🗣️ TTS**: KokoroTTSService (PyTorch-based, already working)
- **🔧 Framework**: Pipecat (handles audio, interruptions, real-time streaming)

## 🚀 Quick Start

### 1. Install Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a fast model for conversation
ollama pull llama3.2:3b

# Or for better quality (if you have enough GPU memory):
ollama pull llama3.1:8b
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables
```bash
# Ollama Configuration
export OLLAMA_MODEL="llama3.2:3b"  # Or your preferred model
export OLLAMA_BASE_URL="http://localhost:11434/v1"

# Optional: CUDA for Whisper (auto-detected)
export CUDA_AVAILABLE="true"

# TTS Settings (existing)
export KOKORO_VOICE_ID="af_bella"
```

### 4. Run the Pipeline
```bash
python src/main.py
```

## ✨ Key Features

### **🔒 Fully Local & Private**
- ✅ No external API calls
- ✅ No data leaves your machine
- ✅ Complete conversation privacy

### **💬 Perfect Conversation Memory**
- ✅ OpenAI-compatible context management
- ✅ Maintains conversation history
- ✅ System prompt enforcement (English-only)

### **⚡ Optimized Performance**
- ✅ CUDA acceleration for Whisper STT
- ✅ Fast interruption detection (150ms VAD)
- ✅ Streaming responses
- ✅ Minimal latency

### **🔧 Ready for Function Calling**
- ✅ Built-in tool/function support via OpenAI format
- ✅ Easy to add custom functions
- ✅ Extensible for future features

### **🛠️ Easy Debugging**
- ✅ Separate components = easier troubleshooting
- ✅ Individual component metrics
- ✅ Clear conversation flow logging

## 📊 Expected Performance

### **Latency Breakdown:**
- **STT (Whisper)**: ~200-400ms
- **LLM (Ollama 3B)**: ~300-800ms (depends on hardware)  
- **TTS (Kokoro)**: ~100-300ms
- **Total**: ~600ms-1.5s (much better than previous 1.8s+)

### **Interruption Response**: ~150ms (fast VAD)

## 🎯 Model Recommendations

### **For Development/Testing:**
```bash
ollama pull llama3.2:1b    # Fastest (~200-400ms inference)
ollama pull llama3.2:3b    # Good balance (recommended)
```

### **For Production Quality:**
```bash
ollama pull llama3.1:8b    # Best quality, slower (~4.9GB)
ollama pull mistral:7b     # Alternative high-quality option
```

### **Whisper Models (auto-selected):**
- `DISTIL_MEDIUM_EN`: Fast English-only (~400MB, recommended)
- `MEDIUM`: Multilingual support (~769MB)  
- `LARGE`: Best accuracy (~1.5GB, slower)

## 🔧 Configuration

### **System Prompt (Anti-Chinese Switching):**
The system prompt includes multiple safeguards against language switching:
```
1. ALWAYS respond in English only
2. If user speaks another language, understand but respond in English
3. Keep responses conversational and under 2 sentences
4. Remember conversation context
5. Immediately switch to English if non-English generation starts
```

### **Environment Variables:**
```bash
# Ollama LLM
OLLAMA_MODEL="llama3.2:3b"
OLLAMA_BASE_URL="http://localhost:11434/v1"

# Whisper STT  
CUDA_AVAILABLE="true"  # Enable CUDA acceleration

# Kokoro TTS (existing)
KOKORO_MODEL_PATH="/models/kokoro/model_fp16.onnx"
KOKORO_VOICES_PATH="/models/kokoro/voices-v1.0.bin"  
KOKORO_VOICE_ID="af_bella"
KOKORO_SAMPLE_RATE="24000"
```

## 🆚 Why Cascaded > Ultravox

| Feature | Ultravox (Pipecat) | Cascaded (New) |
|---------|--------------------|----|
| **Conversation Memory** | ❌ Broken/Limited | ✅ Full OpenAI Context |
| **Function Calling** | ❌ Not supported | ✅ Built-in support |
| **Debugging** | ❌ Black box | ✅ Component-level |
| **Performance Control** | ❌ Limited | ✅ Fine-tunable |
| **System Prompts** | ❌ Unreliable | ✅ Fully working |
| **Stability** | ❌ Experimental | ✅ Production-ready |

## 🛠️ Future Extensions

This architecture makes it easy to add:
- **🔧 Function calling**: Weather, databases, APIs
- **📊 Analytics**: Conversation insights
- **🎯 Custom models**: Local fine-tuned models
- **🔄 Model switching**: Dynamic model selection
- **📱 Multi-modal**: Vision, images (already supported by Ollama)

## 📝 Deployment

Same Docker deployment process - just updated dependencies and models!

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


