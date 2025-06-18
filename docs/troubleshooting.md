# Troubleshooting Guide

This guide helps you diagnose and fix common issues with the air-gapped voice pipeline.

## 🔍 Quick Diagnostics

### Check System Status
```bash
# 1. Test deployment health
curl -I https://your-deployment-id.cerebrium.app/health

# 2. Check virtual environment (IMPORTANT!)
echo $VIRTUAL_ENV  # Should show your venv path
which python       # Should show venv/bin/python

# 3. Check local audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# 4. Test WebSocket connection
python -c "import websockets; print('WebSocket library available')"

# 5. Verify environment variables
echo $WS_SERVER

# 6. Check service status (NEW)
curl https://your-deployment-id.cerebrium.app/debug
```

## 🐍 Virtual Environment Issues

### 1. Virtual Environment Not Activated
```
python: command not found
ModuleNotFoundError: No module named 'websockets'
```

**Cause**: Most common issue - virtual environment not activated

**Solutions**:
```bash
# Check if venv is activated
echo $VIRTUAL_ENV  # Should show path, not empty

# If empty, activate it
cd /path/to/voice-pipeline
source venv/bin/activate

# Verify activation
which python  # Should show venv/bin/python, not /usr/bin/python
```

### 2. Wrong Dependencies Installed
```
ModuleNotFoundError: No module named 'websockets'
# OR
ImportError: No module named 'torch'  # (when you only need client)
```

**Solutions**:

#### A. For Client-Only Users (Recommended)
```bash
# Activate venv
source venv/bin/activate

# Install lightweight client dependencies
pip install -r local_client_requirements.txt

# Verify
python -c "import websockets, sounddevice, numpy; print('✅ Client ready')"
```

#### B. Mixed Dependencies Issue
```bash
# If you have wrong mix of dependencies, recreate venv
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r local_client_requirements.txt
```

### 3. Virtual Environment Corrupted
```
Error: Python executable not found
```

**Solution**: Recreate virtual environment
```bash
# Remove corrupted venv
rm -rf venv

# Create fresh venv
python3 -m venv venv
source venv/bin/activate

# Install correct dependencies
pip install -r local_client_requirements.txt

# Test
python local_client.py
```

### 4. Path Issues
```
python: No such file or directory
```

**Solutions**:
```bash
# Check Python version
python3 --version  # Should be 3.10+

# Create venv with explicit Python version
python3.10 -m venv venv  # or python3.11, etc.
source venv/bin/activate

# Verify correct Python
which python
python --version
```

## 🚨 Common Issues

### 5. Connection Refused Error
```
❌ Cannot connect to wss://your-deployment-id.cerebrium.app/ws
ConnectionRefusedError: [Errno 111] Connect call failed
```

**Causes & Solutions:**

#### A. Wrong Server URL
```bash
# Check your environment variable
echo $WS_SERVER

# Should be: wss://your-deployment-id.cerebrium.app/ws
# Fix with:
export WS_SERVER="wss://your-actual-deployment-id.cerebrium.app/ws"
```

#### B. Deployment Not Running
```bash
# Check deployment status
cerebrium list

# If not deployed, deploy:
cerebrium deploy

# Check logs for deployment issues:
cerebrium logs voice-pipeline-airgapped
```

#### C. Network/Firewall Issues
```bash
# Test with curl
curl -I https://your-deployment-id.cerebrium.app/health

# If this fails, check:
# - Internet connection
# - Corporate firewall blocking WSS
# - VPN interference
```

### 6. Audio Device Issues
```
OSError: [Errno -9996] Invalid device
PortAudioError: Device unavailable
```

**Solutions:**

#### A. List Available Devices
```python
# With venv activated:
import sounddevice as sd
print("Available audio devices:")
for i, device in enumerate(sd.query_devices()):
    print(f"{i}: {device['name']} - {device['max_input_channels']} in, {device['max_output_channels']} out")
```

#### B. Set Specific Device
```python
# In local_client.py, modify:
sd.default.device = [input_device_id, output_device_id]
```

#### C. Install Audio Drivers
```bash
# Linux (with venv activated)
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio

# macOS
brew install portaudio
pip install pyaudio

# Windows
# Download PyAudio wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
```

### 7. Permission Denied (Microphone)
```
PermissionError: Microphone access denied
```

**Solutions:**
- **macOS**: System Preferences → Security & Privacy → Microphone → Allow Terminal/Python
- **Windows**: Settings → Privacy → Microphone → Allow apps to access microphone
- **Linux**: Check PulseAudio/ALSA permissions

### 8. AI Service Errors (Air-Gapped Specific)
```
❌ Failed to initialize Ultravox STT service: Failed to infer device type
❌ STT service not available - check HF_TOKEN
❌ Piper TTS service not available
```

**Solutions:**

#### A. Verify Hugging Face Token (Model Downloads Only)
```bash
# Check Hugging Face token
curl -H "Authorization: Bearer $HF_TOKEN" \
     https://huggingface.co/api/whoami

# Check model access
curl -H "Authorization: Bearer $HF_TOKEN" \
     https://huggingface.co/api/models/fixie-ai/ultravox-v0_4_1-llama-3_1-8b
```

#### B. Update Cerebrium Secrets (Air-Gapped)
```toml
# Edit cerebrium.toml
[cerebrium.secrets]
HF_TOKEN = "hf_your_real_token_here"
# NO external API keys needed!
PIPER_MODEL = "en_US-lessac-medium"
PIPER_SAMPLE_RATE = "22050"
```

#### C. Redeploy with New Secrets
```bash
cerebrium deploy
```

#### D. Check Piper TTS Status
```bash
# Check if Piper models are loaded
curl https://your-deployment-id.cerebrium.app/debug

# Should show:
# "tts_available": true,
# "tts_type": "PiperTTSService"
```

### 9. GPU/Memory Issues
```
RuntimeError: CUDA out of memory
RuntimeError: Failed to infer device type
torch.cuda.OutOfMemoryError: CUDA out of memory
```

**Solutions:**

#### A. Check GPU Configuration
```bash
# View deployment logs
cerebrium logs voice-pipeline-airgapped

# Look for GPU initialization messages
# Should see: "🖥️  GPU detected - configuring for CUDA"
```

#### B. Use Appropriate Model Size
```python
# In src/pipecat_pipeline.py, using 8B model (recommended for A10):
stt_service = UltravoxSTTService(
    model_size="fixie-ai/ultravox-v0_4_1-llama-3_1-8b",  # 8B model
    # ... other params
)
```

#### C. Scale Down Concurrency
```toml
# In cerebrium.toml
[cerebrium.scaling]
max_concurrency = 3  # Reduce from 5 for 8B model
```

### 10. WebSocket Disconnection Issues
```
ERROR: Exception in ASGI application
RuntimeError: Cannot call "receive" once a disconnect message has been received
```

**Solutions:**

#### A. Client-Side Fix
```bash
# Restart local client (with venv activated)
source venv/bin/activate
python local_client.py
```

#### B. Server-Side Fix
```bash
# Restart deployment
cerebrium deploy

# Or check logs for specific errors
cerebrium logs voice-pipeline-airgapped
```

### 11. Slow Response Times
```
⏰ No response from server (timeout)
```

**Causes & Solutions:**

#### A. Cold Start Delay
- **First request**: 30-60 seconds normal (model loading)
- **Solution**: Wait patiently or send test request to warm up

#### B. Model Loading Time
- **Ultravox 8B**: Takes 20-40 seconds to load
- **Piper TTS**: Takes 5-10 seconds to initialize
- **Solution**: Increase timeout in client or use warm instances

#### C. Network Latency
```bash
# Test network speed to deployment
ping your-deployment-id.cerebrium.app
curl -w "@curl-format.txt" -o /dev/null https://your-deployment-id.cerebrium.app/health
```

### 12. Air-Gapped Specific Issues

#### No Internet Access Error
```
❌ Cannot download models during runtime
❌ Model files not found
```

**Solution**: Models are downloaded during deployment, not runtime
```bash
# Redeploy to ensure models are cached
cerebrium deploy

# Check deployment logs for model download
cerebrium logs voice-pipeline-airgapped | grep "Downloading"
```

#### Piper TTS Not Working
```
❌ Piper TTS service initialization failed
❌ No audio output
```

**Solutions**:
```bash
# Check if Piper models are available
curl https://your-deployment-id.cerebrium.app/debug

# Verify Piper configuration in cerebrium.toml
[cerebrium.secrets]
PIPER_MODEL = "en_US-lessac-medium"
PIPER_SAMPLE_RATE = "22050"
```

## 🛠️ Advanced Debugging

### Enable Verbose Logging

#### Server-Side (Cerebrium)
```python
# In src/pipecat_pipeline.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Client-Side
```python
# In local_client.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)

# Also enable websockets logging:
import websockets
websockets.logger.setLevel(logging.DEBUG)
```

### Test Components Individually

#### 1. Test Virtual Environment
```bash
# Check venv is working
source venv/bin/activate
echo "Python: $(which python)"
echo "Pip packages:"
pip list | grep -E "(websockets|sounddevice|numpy)"
```

#### 2. Test WebSocket Connection Only
```python
# With venv activated:
import asyncio
import websockets

async def test_connection():
    uri = "wss://your-deployment-id.cerebrium.app/ws"
    async with websockets.connect(uri) as ws:
        await ws.send("test")
        response = await ws.recv()
        print(f"Response: {response}")

asyncio.run(test_connection())
```

#### 3. Test Audio Devices Only
```python
# With venv activated:
import sounddevice as sd
import numpy as np

# Test microphone
print("Recording 3 seconds...")
audio = sd.rec(int(3 * 16000), samplerate=16000, channels=1, dtype='int16')
sd.wait()
print(f"Recorded {len(audio)} samples")

# Test speakers
print("Playing back...")
sd.play(audio, samplerate=16000)
sd.wait()
```

#### 4. Test Model Access (HF Token)
```bash
# Test Hugging Face token
curl -H "Authorization: Bearer $HF_TOKEN" \
     "https://huggingface.co/api/whoami"

# Test Ultravox model access
curl -H "Authorization: Bearer $HF_TOKEN" \
     "https://huggingface.co/api/models/fixie-ai/ultravox-v0_4_1-llama-3_1-8b"
```

### Monitor Resource Usage

#### Check Cerebrium Metrics
```bash
# View real-time logs
cerebrium logs voice-pipeline-airgapped --follow

# Check deployment status
cerebrium list

# View detailed deployment info
cerebrium describe voice-pipeline-airgapped
```

#### Local Resource Monitoring
```bash
# Monitor local CPU/Memory (with venv activated)
top -p $(pgrep -f local_client.py)

# Monitor network usage
netstat -i

# Check audio system
pulseaudio --check -v  # Linux
```

## 📞 Getting Help

### Log Collection
Before seeking help, collect these logs:

```bash
# 1. Virtual environment info
echo "Virtual env: $VIRTUAL_ENV"
which python
pip list > pip_packages.txt

# 2. Cerebrium deployment logs
cerebrium logs voice-pipeline-airgapped > cerebrium.log

# 3. Local client output (with venv activated)
source venv/bin/activate
python local_client.py 2>&1 | tee local_client.log

# 4. System information
python -c "import sys, platform; print(f'Python: {sys.version}'); print(f'Platform: {platform.platform()}')"

# 5. Audio device info
python -c "import sounddevice as sd; print(sd.query_devices())" > audio_devices.txt

# 6. Service status (NEW)
curl https://your-deployment-id.cerebrium.app/debug > service_status.json
```

### Common Log Patterns

#### Success Patterns
```
Virtual env: /path/to/voice-pipeline/venv    # ✅ venv activated
✅ Connected to voice pipeline!
🤖 Processing your speech...
🔊 Playing AI response...
✅ Ultravox STT service initialized successfully
✅ Local Piper TTS service initialized
```

#### Error Patterns
```
Virtual env:                                 # ❌ venv not activated
❌ Cannot connect to wss://...               # Connection issue
⚠️ Microphone error:                        # Audio device issue  
❌ Failed to initialize Ultravox:            # HF token/GPU issue
❌ Could not initialize Piper TTS:           # TTS model issue
⏰ No response from server:                  # Timeout issue
ERROR: Exception in ASGI:                   # Server-side error
ModuleNotFoundError: No module named:       # Dependencies issue
```

### Support Channels

1. **GitHub Issues**: Create issue with logs and system info
2. **Cerebrium Support**: For deployment-specific issues
3. **Pipecat Discord**: For framework-related questions
4. **Documentation**: Check other docs files for specific topics

## 🔄 Recovery Procedures

### Complete Reset
```bash
# 1. Stop local client
Ctrl+C

# 2. Deactivate and recreate venv
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r local_client_requirements.txt

# 4. Clean environment
unset WS_SERVER
unset HF_TOKEN

# 5. Redeploy server (if needed)
cerebrium deploy

# 6. Set fresh environment
export WS_SERVER="wss://your-deployment-id.cerebrium.app/ws"

# 7. Test connection
python local_client.py
```

### Air-Gapped Deployment Recovery
```bash
# 1. Check model availability
cerebrium logs voice-pipeline-airgapped | grep -E "(Downloading|Loading|model)"

# 2. Force model re-download
cerebrium deploy --force

# 3. Verify all services
curl https://your-deployment-id.cerebrium.app/debug

# Should see:
# "stt_available": true,
# "tts_available": true,
# "hf_token_present": true,
# "gpu_available": true
```

## 🎯 Performance Optimization

### For Faster Response Times
1. **Use warm instances**: Set `min_replicas = 1` in cerebrium.toml
2. **Optimize model loading**: Models are cached after first load
3. **Reduce audio buffer**: Lower `CHUNKS_PER_REQUEST` in client
4. **Use appropriate model**: 8B model is optimal for A10 GPU

### For Better Reliability
1. **Monitor GPU memory**: Stay within A10's 24GB limit
2. **Handle timeouts gracefully**: Increase client timeout for cold starts
3. **Use connection retry logic**: Add exponential backoff
4. **Check service health**: Regular health endpoint checks 