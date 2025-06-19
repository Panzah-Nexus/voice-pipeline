# 📖 Voice Pipeline Documentation

Welcome to the complete documentation for the **Air-Gapped Voice AI Pipeline** running on **Nvidia A10 GPU** via Cerebrium. This system enables natural voice conversations with AI using your local microphone and speakers, with all AI processing happening on dedicated GPU infrastructure without external API dependencies.

## 🚀 Quick Start Guide

### Step 1: Virtual Environment Setup ⚡
```bash
# Navigate to your project directory
cd /path/to/voice-pipeline

# Create and activate virtual environment (ESSENTIAL!)
python3 -m venv venv
source venv/bin/activate

# Install client dependencies (lightweight)
pip install -r local_client_requirements.txt

# Verify setup
python -c "import websockets, sounddevice, numpy; print('✅ Ready for voice pipeline')"
```

### Step 2: Get Required Tokens 🔑
- [**Hugging Face Token**](https://huggingface.co/settings/tokens) - For downloading Ultravox models

### Step 3: Deploy & Connect 🚀
```bash
# Configure and deploy
nano cerebrium.toml  # Add your HF token
cerebrium deploy

# Start voice session (with venv active)
source venv/bin/activate
export WS_SERVER="wss://your-deployment-id.cerebrium.app/ws"
python local_client.py
```

## 🐍 Virtual Environment Management

### ⚠️ Critical: Why Virtual Environments Matter

This project uses **two different dependency sets**:

| Component | Environment | Dependencies | Purpose |
|-----------|-------------|--------------|---------|
| **Local Client** | `venv` activated | `local_client_requirements.txt` | Lightweight audio & WebSocket |
| **Remote Server** | Cerebrium container | `requirements.txt` | Heavy ML libraries (GPU) |

**Not using virtual environments** leads to:
- Dependency conflicts 
- Bloated local installations
- Import errors
- Performance issues

### Virtual Environment Quick Reference

```bash
# ✅ Correct Workflow
cd voice-pipeline
source venv/bin/activate          # ALWAYS do this first
python local_client.py            # Works perfectly

# ❌ Common Mistakes  
python local_client.py            # Error: venv not activated
pip install requirements.txt      # Wrong file (too heavy)
pip install -g websockets         # Global install (conflicts)
```

```

## 📚 Complete Documentation

| Guide | Essential For | Virtual Env Notes |
|-------|---------------|-------------------|
| [**🚀 Deployment Guide**](deployment_guide.md) | **First-time setup** | Full venv setup with troubleshooting |
| [**🎯 Usage Guide**](usage.md) | **Daily operation** | Daily workflow with venv activation |
| [**🔧 Troubleshooting**](troubleshooting.md) | **Problem solving** | Venv issues are #1 most common problem |
| [**🏗️ Architecture**](architecture.md) | **Understanding system** | Why local vs remote dependencies differ |
| [**🔑 API Setup**](api_setup.md) | **Configuration** | Only HF token needed for model access |
| [**🤖 Ultravox Setup**](ultravox_setup.md) | **STT+LLM Model** | Combined speech and language processing |
| [**🔊 Piper Setup**](piper_setup.md) | **TTS System** | Local neural text-to-speech |

### Start Here Based on Your Goal

#### 🎯 "I want to use this system"
1. **[Deployment Guide](deployment_guide.md)** - Complete setup including venv
2. **[Usage Guide](usage.md)** - Daily operation with venv workflow
3. **[Troubleshooting](troubleshooting.md)** - When things go wrong

#### 🏗️ "I want to understand how it works" 
1. **[Architecture](architecture.md)** - System design and data flow
2. **[API Setup](api_setup.md)** - Configuration and tokens
3. **[Deployment Guide](deployment_guide.md)** - Technical implementation

#### 🔧 "I'm having problems"
1. **[Troubleshooting](troubleshooting.md)** - Start here for all issues
2. **[Usage Guide](usage.md)** - Verify correct operation
3. **[Deployment Guide](deployment_guide.md)** - Reconfigure if needed

## 🏗️ System Architecture

```
LOCAL MACHINE (CPU Only)           CEREBRIUM CLOUD (A10 GPU)
┌─────────────────────────┐       ┌─────────────────────────────────────┐
│  🐍 Virtual Environment │       │     🐳 Docker Container             │
│  ┌─────────────────────┐│       │  ┌─────────────────────────────────┐│
│  │   Dependencies:     ││  WSS  │  │      Dependencies:              ││
│  │   • websockets      ││◄─────►│  │   • pipecat-ai[ultravox]        ││
│  │   • sounddevice     ││       │  │   • torch                       ││
│  │   • numpy           ││       │  │   • transformers                ││
│  └─────────────────────┘│       │  │   • piper-tts                   ││
│                         │       │  │                                 ││
│  🎙️ Microphone Input    │       │  └─────────────────────────────────┘│
│  🔊 Speaker Output      │       │                                     │
│  📡 WebSocket Client    │       │  🤖 Ultravox (STT+LLM Combined)     │
└─────────────────────────┘       │  🔊 Piper TTS                       │
                                  └─────────────────────────────────────┘
```

**Key Point**: Local environment stays lightweight, all AI processing happens on GPU with no external API calls.

## ⚡ Most Common Issues (All Virtual Environment Related!)

### 1. `ModuleNotFoundError: No module named 'websockets'`
```bash
# Problem: venv not activated
echo $VIRTUAL_ENV  # Shows nothing

# Solution:
source venv/bin/activate
echo $VIRTUAL_ENV  # Shows path to venv
```

### 2. `python: command not found`
```bash
# Problem: Using system python instead of venv
which python  # Shows /usr/bin/python

# Solution:
source venv/bin/activate
which python  # Shows venv/bin/python
```

### 3. Heavy Dependencies Installed Locally
```bash
# Problem: Installed server requirements on local machine
pip list | grep torch  # Shows torch, transformers, etc.

# Solution: Recreate venv with correct dependencies
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r local_client_requirements.txt
```

## 🎯 Success Indicators

### ✅ Virtual Environment Working Correctly
```bash
source venv/bin/activate
echo "Virtual env: $VIRTUAL_ENV"          # Shows path
which python                              # Shows venv/bin/python
pip list | wc -l                         # Shows ~10-15 packages (lightweight)
python local_client.py                   # Runs without import errors
```

### ✅ System Working End-to-End
```
🎯 Voice Pipeline Local Client
========================================
🔗 Connecting to wss://your-deployment.cerebrium.app/ws
✅ Connected to voice pipeline!
🎙️ Speak into your microphone. Press Ctrl+C to stop.

🤖 Processing your speech...
🔊 Playing AI response...
```

## 💰 Cost Optimization

| Component | Cost | Notes |
|-----------|------|-------|
| **Local Client** | $0 | Just uses your computer |
| **Cerebrium A10** | ~$0.50-1.00/hour | Only when processing |
| **Hugging Face** | $0 | Free tier sufficient for model downloads |

**Total**: ~$0.50-1.00 per hour of usage with auto-scaling to zero cost when idle.

## 🎓 Advanced Topics

### Multiple Environment Management
```bash
# For development (optional)
python3 -m venv venv-dev
source venv-dev/bin/activate
pip install -r requirements.txt  # Full server dependencies for local testing

# For production client (recommended)
python3 -m venv venv
source venv/bin/activate  
pip install -r local_client_requirements.txt  # Lightweight client only
```

### Environment Automation
```bash
# Add to ~/.bashrc or ~/.zshrc
export VOICE_PIPELINE_DIR="/path/to/voice-pipeline"
export VOICE_PIPELINE_URL="wss://your-deployment-id.cerebrium.app/ws"

alias voice-start="cd $VOICE_PIPELINE_DIR && source venv/bin/activate && export WS_SERVER=$VOICE_PIPELINE_URL"
alias voice-test="cd $VOICE_PIPELINE_DIR && source venv/bin/activate && python -c 'import websockets, sounddevice, numpy; print(\"✅ All dependencies OK\")'"
```

## 🆘 Getting Help

### Before Reporting Issues
1. **Check virtual environment**: `echo $VIRTUAL_ENV`
2. **Verify dependencies**: `pip list | grep -E "(websockets|sounddevice|numpy)"`
3. **Test audio devices**: `python -c "import sounddevice as sd; print(sd.query_devices())"`
4. **Check server health**: `curl -I https://your-deployment-id.cerebrium.app/health`

### Include in Bug Reports
```bash
# System info
echo "Virtual env: $VIRTUAL_ENV"
echo "Python: $(which python)"
echo "Platform: $(python -c 'import platform; print(platform.platform())')"

# Dependencies
pip list > pip_packages.txt

# Error logs
python local_client.py 2>&1 | tee error.log
```

## 🔄 Updates & Maintenance

### Keeping Virtual Environment Healthy
```bash
# Weekly check
source venv/bin/activate
pip check  # Look for dependency conflicts

# Monthly refresh (if needed)
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r local_client_requirements.txt --upgrade
```


## 🎯 Ready to Start?

1. **[🚀 Deployment Guide](deployment_guide.md)** - Step-by-step setup including virtual environment
2. **[🎯 Usage Guide](usage.md)** - Daily operation with proper environment management  
3. **[🔧 Troubleshooting](troubleshooting.md)** - Virtual environment troubleshooting and more

**Remember**: Virtual environment activation is required for **every session**! This is the #1 success factor. 