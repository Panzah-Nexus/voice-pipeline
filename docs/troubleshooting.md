# Troubleshooting Guide

This guide helps you diagnose and fix common issues with the voice pipeline.

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
cerebrium logs voice-pipeline
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

### 8. AI Service Errors
```
❌ Failed to initialize Ultravox STT service: Failed to infer device type
❌ STT service not available - check HUGGING_FACE_TOKEN
```

**Solutions:**

#### A. Verify API Keys
```bash
# Check Hugging Face token
curl -H "Authorization: Bearer $HUGGING_FACE_TOKEN" \
     https://huggingface.co/api/whoami

# Check OpenAI key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

#### B. Update Cerebrium Secrets (Air-Gapped)
```toml
# Edit cerebrium.toml
[cerebrium.secrets]
HUGGING_FACE_TOKEN = "hf_your_real_token_here"
# NO OpenAI key needed - air-gapped deployment!
PIPER_MODEL = "en_US-lessac-medium"
PIPER_SAMPLE_RATE = "22050"
```

#### C. Redeploy with New Secrets
```bash
cerebrium deploy
```

### 9. GPU/Memory Issues
```
RuntimeError: CUDA out of memory
RuntimeError: Failed to infer device type
```

**Solutions:**

#### A. Check GPU Configuration
```bash
# View deployment logs
cerebrium logs voice-pipeline

# Look for GPU initialization messages
```

#### B. Reduce Model Size
```python
# In src/pipecat_pipeline.py, try smaller model:
stt_service = UltravoxSTTService(
    model_size="300m",  # Instead of "1b"
    # ... other params
)
```

#### C. Scale Down Concurrency
```toml
# In cerebrium.toml
[cerebrium.scaling]
max_concurrency = 1  # Reduce from 5
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
cerebrium logs voice-pipeline
```

### 11. Slow Response Times
```
⏰ No response from server (timeout)
```

**Causes & Solutions:**

#### A. Cold Start Delay
- **First request**: 30-60 seconds normal
- **Solution**: Wait patiently or send test request to warm up

#### B. Model Loading Time
- **GPU memory allocation**: Can take 10-30 seconds
- **Solution**: Increase timeout in client

#### C. Network Latency
```bash
# Test network speed to deployment
ping your-deployment-id.cerebrium.app
curl -w "@curl-format.txt" -o /dev/null https://your-deployment-id.cerebrium.app/health
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

#### 4. Test API Keys
```bash
# Test Hugging Face
curl -H "Authorization: Bearer hf_your_token" \
     "https://huggingface.co/fixie-ai/ultravox-v0_3" 

# Test OpenAI
curl -H "Authorization: Bearer sk_your_key" \
     "https://api.openai.com/v1/audio/speech" \
     -H "Content-Type: application/json" \
     -d '{"model": "tts-1", "input": "test", "voice": "nova"}' \
     --output test.mp3
```

### Monitor Resource Usage

#### Check Cerebrium Metrics
```bash
# View real-time logs
cerebrium logs voice-pipeline --follow

# Check deployment status
cerebrium list

# View detailed deployment info
cerebrium describe voice-pipeline
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
cerebrium logs voice-pipeline > cerebrium.log

# 3. Local client output (with venv activated)
source venv/bin/activate
python local_client.py 2>&1 | tee local_client.log

# 4. System information
python -c "import sys, platform; print(f'Python: {sys.version}'); print(f'Platform: {platform.platform()}')"

# 5. Audio device info
python -c "import sounddevice as sd; print(sd.query_devices())" > audio_devices.txt
```

### Common Log Patterns

#### Success Patterns
```
Virtual env: /path/to/voice-pipeline/venv    # ✅ venv activated
✅ Connected to voice pipeline!
🤖 Processing your speech...
🔊 Playing AI response...
✅ Response sent to client
```

#### Error Patterns
```
Virtual env:                                 # ❌ venv not activated
❌ Cannot connect to wss://...               # Connection issue
⚠️ Microphone error:                        # Audio device issue  
❌ Failed to initialize Ultravox:            # API key/GPU issue
⏰ No response from server:                  # Timeout issue
ERROR: Exception in ASGI:                   # Server-side error
ModuleNotFoundError: No module named:       # Dependencies issue
```

### Support Channels

1. **GitHub Issues**: Create issue with logs and system info
2. **Cerebrium Support**: For deployment-specific issues
3. **Community Discord**: For general troubleshooting
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

# 5. Redeploy
cerebrium deploy

# 6. Get new URL and test
export WS_SERVER="wss://new-deployment-id.cerebrium.app/ws"
curl -I https://new-deployment-id.cerebrium.app/health

# 7. Restart client
python local_client.py
```

### Rollback Deployment
```bash
# If new deployment has issues
cerebrium rollback voice-pipeline

# Or deploy previous version
git checkout previous-commit
cerebrium deploy
```

## ✅ Prevention Tips

1. **Always Use Virtual Environment**: Never install packages globally
2. **Verify Environment**: Check `$VIRTUAL_ENV` before running commands
3. **Correct Dependencies**: Use `local_client_requirements.txt` for client
4. **Regular Testing**: Test health endpoint daily
5. **Monitor Logs**: Check `cerebrium logs` for warnings
6. **Update Dependencies**: Keep requirements.txt current
7. **Backup Configuration**: Version control cerebrium.toml
8. **Test Audio**: Verify microphone/speakers before each session 