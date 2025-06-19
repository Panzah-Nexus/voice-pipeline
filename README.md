# Voice AI Pipeline - Air-Gapped Deployment

A complete voice AI pipeline using **Ultravox** (STT + LLM) and **Piper TTS** for fully local, air-gapped deployment on NVIDIA A10 GPUs.

## ✅ **Architecture Overview**

This implementation uses the **correct** approach for air-gapped voice AI:

```
Audio Input → Ultravox (STT + LLM) → Piper TTS → Audio Output
```

### **Key Components:**
- **Ultravox**: Multimodal LLM that handles both speech recognition AND language generation in one model
- **Piper TTS**: Local text-to-speech engine (no external APIs)
- **Pipecat**: Framework for real-time voice pipeline orchestration
- **FastAPI + WebSocket**: Real-time audio streaming

## 🚀 **Quick Start**

### **1. Install Dependencies**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install requirements
pip install -r requirements.txt
```

### **2. Setup Environment**

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Hugging Face token
HF_TOKEN=hf_your_token_here
```

### **3. Setup Piper TTS Server**

```bash
# Run the setup script (tries Docker first, falls back to local install)
python setup_piper_server.py
```

### **4. Test the Setup**

> **Note on Piper TTS**: The pipeline uses a custom Piper TTS service that runs Piper directly via subprocess (no HTTP server needed). If you prefer the official Pipecat Piper service, you'll need to run a Piper HTTP server and modify the import in `src/pipecat_pipeline.py`.

```bash
# Run all tests
python run_tests.py

# Or run specific tests
python run_tests.py piper   # Test Piper TTS
python run_tests.py docker  # Test Docker build

# Start the voice pipeline server
python src/main.py

# In another terminal, run the client
python local_client.py          # Raw audio streaming client

# Note: By default, the server uses protobuf serialization. To use the raw audio client:
# Set USE_PROTOBUF=false in your .env file or export USE_PROTOBUF=false
```

## 🔧 **Enhanced Pipeline Features**

### **✅ Off-the-Shelf Pipecat Components:**

The pipeline now uses many built-in Pipecat components for better performance and reduced errors:

1. **Context Aggregators**: Proper conversation state management
2. **ProtobufFrameSerializer**: Efficient frame serialization
3. **SileroVADAnalyzer**: Voice Activity Detection (optional)
4. **FrameLogger**: Debug frame flow (optional)
5. **FrameProcessorMetrics**: Performance metrics collection
6. **NoiseReduceFilter**: Audio noise reduction (optional)

### **🎚️ Configurable Options:**

Enable features via environment variables:

```bash
# Enable Voice Activity Detection
ENABLE_VAD=true

# Enable noise reduction
ENABLE_NOISE_REDUCTION=true

# Enable debug frame logging
DEBUG_FRAMES=true

# Enable performance metrics
ENABLE_METRICS=true
ENABLE_USAGE_METRICS=true

# Debug mode
DEBUG=true

# Protocol selection (set to false for raw audio clients)
USE_PROTOBUF=true
```

### **📦 Pipeline Structure:**


## 📊 **Performance Expectations**

- **Ultravox 8B on A10**: ~150ms time-to-first-token
- **End-to-end latency**: 600-800ms (comparable to OpenAI Realtime API)
- **Memory usage**: ~16GB VRAM for Ultravox 8B
- **Throughput**: 50-100 tokens/second

## 🌐 **Deployment Options**

### **Local Testing**
```bash
python src/pipecat_pipeline.py
```

### **Cerebrium Deployment**
Your existing `cerebrium.toml` should work with the fixed implementation:

```bash
cerebrium deploy
```

### **Docker Deployment**
```bash
# Build image
docker build -t voice-pipeline .

# Run with GPU support
docker run --gpus all -p 8000:8000 voice-pipeline
```

## 🔍 **Debugging**

### **Check Service Status**
```bash
curl http://localhost:8000/debug
```

### **Check Piper TTS**
```bash
curl http://localhost:5000/health
```

### **View Logs**
The pipeline provides detailed logging for each component:
- ✅ Service initialization
- 🎵 Audio processing
- 🤖 Ultravox inference
- 🔊 TTS generation

## 📁 **Project Structure**

```
voice-pipeline/
├── src/                         # Core deployment code
│   ├── pipecat_pipeline.py      # Main pipeline with Ultravox + Piper
│   ├── piper_tts_service.py     # Consolidated Piper TTS service
│   ├── main.py                  # FastAPI entry point
│   └── README.md                # Source code documentation
├── utils/                       # Development utilities (not deployed)
│   ├── websocket_client.py      # Test client for audio streaming
│   ├── audio_utils.py           # Audio helper functions
│   ├── simple_test_server.py    # Echo test server
│   └── README.md                # Utilities documentation
├── tests/                       # Test suite
│   ├── test_piper_local.py      # Piper TTS tests
│   ├── test_docker_build.py     # Docker build tests
│   └── README.md                # Test documentation
├── docs/                        # Comprehensive documentation
├── docker/
│   └── Dockerfile               # Container configuration
├── setup_piper_server.py        # Piper TTS setup script
├── local_client.py              # Voice pipeline client
├── run_tests.py                 # Test runner
├── requirements.txt             # Python dependencies
├── cerebrium.toml              # Cerebrium deployment config
└── README.md                   # This file
```

## 🐛 **Troubleshooting**

### **"UltravoxSTTService unavailable"**
- Check your HF_TOKEN in `.env`
- Ensure you have access to `fixie-ai/ultravox-v0_4_1-llama-3_1-8b`

### **"Piper TTS server not found"**
- Run `python setup_piper_server.py`
- Or manually start: `docker run -p 5000:5000 rhasspy/piper:latest`

### **GPU Memory Issues**
- Use Ultravox 8B instead of 70B for A10
- Check CUDA memory: `nvidia-smi`

### **WebSocket Connection Failed**
- Ensure server is running on port 8000
- Check firewall settings
- Test with: `python local_client.py`

## 🎯 **Next Steps for Production**

1. **Optimize Model Loading**: Cache models in memory
2. **Implement Authentication**: Add API keys/tokens
3. **Add Monitoring**: Metrics and health checks
4. **Scale Horizontally**: Load balancer + multiple instances
5. **Fine-tune Ultravox**: Custom training data for your use case

## 📚 **References**

- [Ultravox Documentation](https://github.com/fixie-ai/ultravox)
- [Pipecat Documentation](https://docs.pipecat.ai/)
- [Piper TTS](https://github.com/rhasspy/piper)
- [Cerebrium Ultravox Tutorial](https://www.cerebrium.ai/blog/deploying-ultravox-on-cerebrium)

---

**✅ Your architecture is correct! This implementation fixes the service usage while maintaining your air-gapped, local deployment approach.**

