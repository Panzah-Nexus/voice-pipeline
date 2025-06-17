# Voice Pipeline Deployment Guide

This guide shows you how to deploy your voice AI pipeline with **Nvidia A10 GPU on Cerebrium** and connect it to your local devices (no local GPU required).

## 🎯 Overview

- **Local Device (CPU-only)**: Captures microphone → WebSocket client → Plays speakers
- **Cerebrium (A10 GPU)**: WebSocket server → Ultravox STT → LLM → TTS → Response

## 📋 Prerequisites

- Python 3.10+ on your local machine
- Cerebrium account
- Hugging Face account (for Ultravox models)
- OpenAI account (for TTS)
- Microphone and speakers on local machine

## 🐍 Virtual Environment Setup

### Why Virtual Environments?

This project uses **two different sets of dependencies**:
- **Server dependencies** (heavy ML libraries for Cerebrium)
- **Client dependencies** (lightweight audio libraries for local use)

Virtual environments prevent conflicts and keep your system clean.

### Phase 0: Virtual Environment Management

#### 0.1 Create Project Virtual Environment
```bash
# Navigate to your project directory
cd /path/to/voice-pipeline

# Create virtual environment
python3 -m venv venv

# Activate virtual environment (Linux/macOS)
source venv/bin/activate

# Activate virtual environment (Windows)
# venv\Scripts\activate

# Verify activation (should show venv path)
which python
```

#### 0.2 When to Use Which Environment

| Task | Virtual Environment | Dependencies | Why |
|------|-------------------|--------------|-----|
| **Local Client** | ✅ `venv` activated | `local_client_requirements.txt` | Lightweight, no ML libraries |
| **Local Testing** | ✅ `venv` activated | `requirements.txt` | Full server dependencies for testing |
| **Cerebrium Deploy** | ❌ No local venv | `requirements.txt` | Cerebrium builds its own container |

#### 0.3 Dependency Management

**For Local Client Only** (recommended for most users):
```bash
# Activate venv
source venv/bin/activate

# Install lightweight client dependencies
pip install -r local_client_requirements.txt

# Verify installation
python -c "import websockets, sounddevice, numpy; print('✅ Client dependencies ready')"
```

**For Full Local Testing** (optional - if you want to test server locally):
```bash
# Activate venv  
source venv/bin/activate

# Install all server dependencies (large download!)
pip install -r requirements.txt

# This includes ML libraries like torch, transformers, etc.
```

#### 0.4 Virtual Environment Best Practices

```bash
# Always activate before working
source venv/bin/activate

# Check what's installed
pip list

# Deactivate when done
deactivate

# Recreate if corrupted
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r local_client_requirements.txt
```

## Phase 1: API Keys Setup

### 1.1 Hugging Face Token
1. Visit: https://huggingface.co/settings/tokens
2. Create a token with "Read" access
3. Copy the token (starts with `hf_`)

### 1.2 OpenAI API Key
1. Visit: https://platform.openai.com/api-keys
2. Create an API key
3. Copy the key (starts with `sk-`)

## Phase 2: Configure Cerebrium Deployment

### 2.1 Update Cerebrium Configuration
Edit `cerebrium.toml` and replace the placeholder tokens:

```toml
[cerebrium.secrets]
HUGGING_FACE_TOKEN = "hf_your_actual_token_here"
OPENAI_API_KEY = "sk_your_actual_key_here"
OPENAI_TTS_VOICE = "nova"
OPENAI_TTS_MODEL = "tts-1"
```

### 2.2 Install Cerebrium CLI
```bash
# Option 1: In your project venv (recommended)
source venv/bin/activate
pip install cerebrium

# Option 2: Global installation
pip install --user cerebrium
```

### 2.3 Login to Cerebrium
```bash
cerebrium login
```

## Phase 3: Deploy to Cerebrium

### 3.1 Deploy the Application
```bash
# Make sure you're in the project directory
cd /path/to/voice-pipeline

# Deploy (no need for venv activation - Cerebrium builds its own container)
cerebrium deploy
```

After deployment, you'll receive a URL like:
```
https://your-deployment-id.cerebrium.app
```

### 3.2 Verify Deployment
Test the health endpoint:
```bash
curl -I https://your-deployment-id.cerebrium.app/health
```

Should return: `200 OK`

## Phase 4: Local Client Setup

### 4.1 Activate Virtual Environment
```bash
# Navigate to project directory
cd /path/to/voice-pipeline

# Activate virtual environment
source venv/bin/activate

# Verify activation
echo "Virtual env: $VIRTUAL_ENV"
```

### 4.2 Install Local Dependencies
```bash
# With venv activated, install client dependencies
pip install -r local_client_requirements.txt
```

The local client only needs:
- `websockets` - For WebSocket communication
- `sounddevice` - For microphone/speaker access
- `numpy` - For audio processing

### 4.3 Configure Server URL
```bash
# Set environment variable (with venv activated)
export WS_SERVER="wss://your-deployment-id.cerebrium.app/ws"

# Verify it's set
echo $WS_SERVER
```

⚠️ **Important**: Replace `your-deployment-id` with your actual deployment ID

### 4.4 Test Audio Devices
```bash
# With venv activated, test audio system
python -c "import sounddevice as sd; print('Audio devices:'); print(sd.query_devices())"
```

## Phase 5: Run the Voice Pipeline

### 5.1 Start Local Client
```bash
# Ensure venv is activated and WS_SERVER is set
source venv/bin/activate
export WS_SERVER="wss://your-deployment-id.cerebrium.app/ws"

# Run the client
python local_client.py
```

Expected output:
```
🎯 Voice Pipeline Local Client
========================================
🔗 Connecting to wss://your-deployment-id.cerebrium.app/ws
✅ Connected to voice pipeline!
🎙️ Speak into your microphone. Press Ctrl+C to stop.
```

### 5.2 Usage Flow
1. **Speak for ~5 seconds** into your microphone
2. System shows: `🤖 Processing your speech...`
3. You hear: `🔊 Playing AI response...`
4. Continue the conversation!

## Phase 6: Monitoring and Logs

### 6.1 View Deployment Logs
```bash
# No venv needed for Cerebrium CLI commands
cerebrium logs voice-pipeline
```

### 6.2 Check Deployment Status
```bash
cerebrium list
```

## 🔧 Virtual Environment Troubleshooting

### Common Issues

#### "Command not found" errors
```bash
# Problem: venv not activated
python local_client.py  # ❌ Error

# Solution: Activate venv first
source venv/bin/activate
python local_client.py  # ✅ Works
```

#### Import errors
```bash
# Problem: Wrong dependencies installed
ModuleNotFoundError: No module named 'websockets'

# Solution: Install correct dependencies
source venv/bin/activate
pip install -r local_client_requirements.txt
```

#### Mixed dependencies
```bash
# Problem: Installed wrong requirements file
# You have torch, transformers, etc. but just want client

# Solution: Recreate venv with correct dependencies
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r local_client_requirements.txt
```

### Verification Commands
```bash
# Check if venv is active
echo $VIRTUAL_ENV  # Should show path to your venv

# Check Python location
which python  # Should show venv/bin/python

# Check installed packages
pip list | grep -E "(websockets|sounddevice|numpy)"

# Test client dependencies
python -c "import websockets, sounddevice, numpy; print('✅ All client deps working')"
```

## 📝 Daily Workflow

### Starting a Session
```bash
# 1. Navigate to project
cd /path/to/voice-pipeline

# 2. Activate virtual environment
source venv/bin/activate

# 3. Set server URL (if not in .bashrc/.zshrc)
export WS_SERVER="wss://your-deployment-id.cerebrium.app/ws"

# 4. Run client
python local_client.py
```

### Ending a Session
```bash
# 1. Stop client (Ctrl+C)
# 2. Deactivate venv
deactivate
```

### Environment Persistence (Optional)
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
# Auto-activate venv when entering project directory
alias voice-pipeline="cd /path/to/voice-pipeline && source venv/bin/activate && export WS_SERVER='wss://your-deployment-id.cerebrium.app/ws'"
```

Then just run: `voice-pipeline` followed by `python local_client.py`

## Configuration Details

### Hardware Configuration (A10 GPU)
```toml
[cerebrium.hardware]
compute = "A10"        # Nvidia A10 GPU
memory = "24Gi"        # 24GB RAM
cpu = "8"              # 8 CPU cores
```

### Scaling Configuration
```toml
[cerebrium.scaling]
min_replicas = 0       # Scale to zero when idle
max_replicas = 2       # Max 2 instances
max_concurrency = 5    # 5 concurrent connections per instance
```

### Runtime Configuration
```toml
[cerebrium.runtime.custom]
port = 8000                        # WebSocket port
healthcheck_endpoint = "/health"   # Health check
readycheck_endpoint = "/ready"     # Readiness check
dockerfile_path = "./docker/Dockerfile"
```

## Cost Optimization

- **Scale to Zero**: Automatically scales down when not in use
- **Pay per Use**: Only charged for active GPU time
- **Efficient Batching**: Multiple conversations can share one instance

## Security Notes

- API keys are stored securely in Cerebrium secrets
- WebSocket connection uses WSS (secure WebSocket)
- No sensitive data stored locally

## Next Steps

- See [Architecture Documentation](architecture.md) for system details
- Check [Troubleshooting Guide](troubleshooting.md) for common issues
- Review [Usage Guide](usage.md) for advanced features 