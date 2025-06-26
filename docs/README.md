# Documentation

Welcome to the technical documentation for the Voice Pipeline project.

This documentation is for developers and infrastructure engineers responsible for building, deploying, and maintaining the system.

## Table of Contents

1.  **[Quick Start](./1_quick_start.md)**
    *   Learn how to build and run the pipeline locally with Docker or on a cloud GPU instance.

2.  **[Architecture](./2_architecture.md)**
    *   Get a high-level overview of the system's components and data flow, from audio input to audio output.

3.  **[TTS Service](./3_tts_service.md)**
    *   A deep dive into the isolated Text-to-Speech (TTS) subprocess, explaining its design and communication protocol.

4.  **[STT Service](./4_stt_service.md)**
    *   Details on the Speech-to-Text (STT) model, configuration, and performance expectations.

5.  **[Observability](./5_observability.md)**
    *   Instructions for enabling and configuring metrics (Pipecat) and tracing (OpenTelemetry).

6.  **[Configuration](./6_configuration.md)**
    *   A reference guide for all environment variables and command-line arguments.

7.  **[Troubleshooting](./7_troubleshooting.md)**
    *   Solutions for common errors and issues.

8.  **[Contributing](./8_contributing.md)**
    *   Guidelines for contributing to the project, including code style and testing procedures.

## 🚀 Getting Started

If this is your first time using the project, the **[Deployment Guide](deployment_guide.md)** is the best place to start. It provides a complete, step-by-step walkthrough of setting up the pipeline on RunPod.

## 📚 Complete Documentation

This documentation is structured to help you based on your goals, whether you want to use the system, understand its inner workings, or troubleshoot problems.

| Guide | Description | Key Topics |
| :------------------------------------------ | :----------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------- |
| [**🚀 Deployment Guide**](deployment_guide.md) | **Step-by-step instructions** for deploying the pipeline on RunPod.      | RunPod template setup, environment variables (`HF_TOKEN`), start commands, and local client configuration. |
| [**🎯 Usage Guide**](usage.md) | **How to use the pipeline** for daily operation and interaction.         | Starting a session, speaking tips, conversation examples, and configuration options.                  |
| [**🔧 Troubleshooting Guide**](troubleshooting.md) | **Solutions to common problems** you might encounter in a RunPod environment. | Checking pod logs, SSHing into the pod, connection errors, and AI service failures.                 |
| [**🏗️ Architecture**](architecture.md) | A **high-level overview** of the system's design and data flow.        | The roles of the local client and the RunPod server, `UltravoxWithContextService`, and `KokoroTTSService`. |
| [**🔑 API & Model Setup**](api_setup.md) | **Details on the models** and the Hugging Face token setup.              | How the `HF_TOKEN` is used, model names, and security best practices.                                 |
| [**🤖 Ultravox Setup**](ultravox_setup.md) | An in-depth look at the **combined STT+LLM service**.                  | Benefits of a single model, context management, and performance tuning.                               |
| [**🔊 Kokoro TTS Setup**](kokoro_setup.md) | An in-depth look at the **offline TTS service**.                       | Benefits of local TTS, configuration, and troubleshooting.                                            |
| [**🔌 Hardware Guide**](hardware_guide.md) | A **comparison of suitable GPUs** for deploying the pipeline.            | Comparison of NVIDIA L4, A10, and L40 GPUs for different deployment scenarios.                        |
| [**ንድ Pipeline Design**](pipeline_design.md) | The **strategic goals** of the project and its deployment path.          | Using RunPod for development and targeting an on-premises GPU for final production.                   |

### Where to Start Based on Your Goal

#### 🎯 "I want to use this system."
1.  **[Deployment Guide](deployment_guide.md)**: For your initial one-time setup.
2.  **[Usage Guide](usage.md)**: For your day-to-day workflow.
3.  **[Troubleshooting Guide](troubleshooting.md)**: When you encounter any issues.

#### 🏗️ "I want to understand how it works."
1.  **[Architecture](architecture.md)**: For the system's overall structure.
2.  **[Pipeline Design](pipeline_design.md)**: For the project's strategic vision.
3.  **[Hardware Guide](hardware_guide.md)**: To understand the hardware requirements.

#### 🔧 "I'm having problems."
1.  **[Troubleshooting Guide](troubleshooting.md)**: The first place to look for solutions.
2.  **[Usage Guide](usage.md)**: To double-check that you are following the correct operational steps.
3.  **[Deployment Guide](deployment_guide.md)**: To verify that your RunPod setup is configured correctly.

## 🏗️ System Architecture Overview

```
LOCAL MACHINE (Web Browser)          RUNPOD CLOUD (NVIDIA L4 GPU)
┌─────────────────────────┐ WSS    ┌───────────────────────────────────┐
│  🕸️ Web Client          │◄─────►│     🐳 Docker Container           │
│  ┌─────────────────────┐│        │  ┌───────────────────────────────┐ │
│  │   JavaScript        ││        │  │      AI Services:             │ │
│  │   • Pipecat SDK     ││        │  │   • UltravoxWithContext       │ │
│  │   • Web Audio API   ││        │  │   • KokoroTTSService          │ │
│  └─────────────────────┘│        │  └───────────────────────────────┘ │
│                         │        │                                    │
│  🎙️ Microphone Input    │        │   🚀 Pipecat Orchestration      │
│  🔊 Speaker Output      │        └───────────────────────────────────┘
└─────────────────────────┘
```

**Key Principle**: Your local machine runs a lightweight web client, while all the intensive AI processing happens in your private, secure RunPod container.

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