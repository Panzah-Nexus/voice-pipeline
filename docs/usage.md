# Usage Guide

This guide explains how to use the air-gapped voice pipeline system effectively once it's deployed and configured.

## 🎯 Quick Start

### 1. Activate Virtual Environment
```bash
# Navigate to your project directory
cd /path/to/voice-pipeline

# Activate virtual environment (REQUIRED!)
source venv/bin/activate

# Verify activation
echo "Virtual env: $VIRTUAL_ENV"
which python  # Should show venv/bin/python
```

### 2. Set Server URL
```bash
# Set your deployment URL (with venv activated)
export WS_SERVER="wss://your-deployment-id.cerebrium.app/ws"

# Verify it's set
echo $WS_SERVER
```

### 3. Start a Voice Session
```bash
# With venv activated, start the voice client
python local_client.py
```

### 4. Expected Output
```
🎯 Voice Pipeline Local Client
========================================
🔗 Connecting to wss://your-deployment-id.cerebrium.app/ws
✅ Connected to voice pipeline!
🎙️ Speak into your microphone. Press Ctrl+C to stop.
```

### 5. Have a Conversation
1. **Speak clearly** into your microphone for ~5 seconds
2. Wait for: `🤖 Processing your speech...`
3. Listen to: `🔊 Playing AI response...`
4. Continue the conversation naturally!

## 🐍 Virtual Environment Management

### Why It's Important
The voice pipeline uses **lightweight dependencies** for the local client:
- `websockets` for communication
- `sounddevice` for audio
- `numpy` for processing

Installing heavy ML libraries locally is unnecessary and can cause conflicts.

### Daily Workflow
```bash
# 1. Navigate to project
cd /path/to/voice-pipeline

# 2. Activate virtual environment
source venv/bin/activate

# 3. Set server URL (if not persistent)
export WS_SERVER="wss://your-deployment-id.cerebrium.app/ws"

# 4. Run client
python local_client.py

# 5. When done, deactivate (optional)
deactivate
```

### Environment Persistence (Optional)
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
# Auto-setup for voice pipeline
alias voice-start="cd /path/to/voice-pipeline && source venv/bin/activate && export WS_SERVER='wss://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped/ws"
```

Then just run: `voice-start` followed by `python local_client.py`

## 🎙️ Speaking Tips

### Best Practices
- **Clear articulation**: Speak clearly and at normal pace
- **Optimal distance**: 6-12 inches from microphone
- **Quiet environment**: Minimize background noise
- **Natural speech**: Speak conversationally, not robotic
- **Complete thoughts**: Finish sentences before pausing

### Timing
- **5-second chunks**: System processes every ~5 seconds
- **Wait for processing**: Don't speak while "Processing..." is shown
- **Continuous conversation**: You can speak immediately after response plays

### What to Expect
- **Processing time**: 1-2 seconds total round-trip (60% faster with Ultravox)
- **Response quality**: Natural, conversational AI responses
- **Context awareness**: AI remembers recent conversation context
- **Voice quality**: Neural TTS with Piper sounds natural

## 💬 Conversation Examples

### Getting Started
```
You: "Hello, can you hear me?"
AI: "Yes, I can hear you clearly! How are you doing today?"

You: "I'm doing well, thanks. What can you help me with?"
AI: "I can help with a wide variety of tasks like answering questions, having conversations, helping with analysis, creative writing, and much more. What would you like to explore?"
```

### Q&A Session
```
You: "What's the weather like in San Francisco today?"
AI: "I don't have access to real-time weather data since I'm running in an air-gapped environment, but I'd recommend checking a weather service for current conditions in San Francisco."

You: "Can you explain how photosynthesis works?"
AI: "Certainly! Photosynthesis is the process by which plants convert sunlight, carbon dioxide, and water into glucose and oxygen..."
```

### Creative Tasks
```
You: "Can you help me write a short story about a robot?"
AI: "I'd be happy to help! Let's start with a brief story about a robot. Here's a beginning: 'In the year 2087, a small maintenance robot named Circuit discovered something unusual in the abandoned subway tunnels...' Would you like me to continue or would you prefer to take it in a different direction?"
```

## ⚙️ Configuration Options

### Audio Settings
You can modify audio parameters in `local_client.py`:

```python
# Audio configuration
SAMPLE_RATE = 16000           # 16kHz (recommended for speech)
CHUNK_DURATION_SEC = 0.5      # 0.5 second chunks
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_SEC)

# Processing timing
CHUNKS_PER_REQUEST = 10       # ~5 seconds of audio
```

### Response Timeouts
```python
# In local_client.py
response_timeout = 10.0       # 10 seconds max wait for response
```

### Voice Selection (Server-Side)
In `cerebrium.toml`, you can change the Piper TTS voice:

```toml
[cerebrium.secrets]
PIPER_MODEL = "en_US-lessac-medium"   # American English, medium quality
PIPER_SAMPLE_RATE = "22050"           # Audio sample rate
```

Available Piper voices include:
- `en_US-lessac-medium` - American English
- `en_GB-alan-medium` - British English  
- `de_DE-thorsten-medium` - German
- `fr_FR-siwis-medium` - French
- And many more in 50+ languages

## 🛠️ Advanced Usage

### Custom Server URL
```bash
# For development/testing
export WS_SERVER="ws://localhost:8000/ws"

# For custom Cerebrium deployment
export WS_SERVER="wss://custom-name.cerebrium.app/ws"

# For secure local testing
export WS_SERVER="wss://localhost:8000/ws"
```

### Audio Device Selection
```python
# With venv activated, list available devices
import sounddevice as sd
print(sd.query_devices())

# Set specific devices in local_client.py
sd.default.device = [input_device_id, output_device_id]
```

### Testing Dependencies
```bash
# With venv activated, verify all dependencies work
python -c "import websockets, sounddevice, numpy; print('✅ All dependencies working')"

# Test audio system
python -c "import sounddevice as sd; print('Audio devices:'); print(sd.query_devices())"

# Test WebSocket library
python -c "import websockets; print('✅ WebSocket library ready')"
```

### Batch Processing Mode
For processing multiple audio files (not real-time):

```python
# Example: Process audio file
import soundfile as sf
import websockets

async def process_audio_file(file_path, server_url):
    audio, samplerate = sf.read(file_path)
    # Resample to 16kHz if needed
    # Send to server and get response
```

## 📊 Monitoring Your Session

### Status Indicators
- 🔗 **Connecting**: Establishing WebSocket connection
- ✅ **Connected**: Ready to receive audio
- 🎙️ **Listening**: Capturing microphone input
- 🤖 **Processing**: AI analyzing your speech with Ultravox
- 🔊 **Playing**: Piper TTS audio playing
- ⚠️ **Warning**: Non-critical issue occurred
- ❌ **Error**: Problem needs attention

### Performance Metrics
```python
# You can add timing to local_client.py
import time

start_time = time.time()
# ... send audio and receive response
end_time = time.time()
print(f"Round-trip time: {end_time - start_time:.2f} seconds")
```

### Quality Indicators
- **Fast responses** (<2 seconds): Ultravox optimized performance
- **Clear audio playback**: Piper TTS working well
- **Accurate transcription**: Ultravox audio understanding
- **Relevant responses**: AI context awareness

## 🔧 Session Management

### Starting and Stopping
```bash
# Start session (with venv activated)
source venv/bin/activate
export WS_SERVER="wss://your-deployment-id.cerebrium.app/ws"
python local_client.py

# Stop session (any of these)
Ctrl+C              # Graceful shutdown
Ctrl+Z              # Suspend (Linux/macOS)
Close terminal      # Force stop

# Clean shutdown
deactivate          # Deactivate virtual environment
```

### Handling Interruptions
- **Network disconnection**: Client will show connection error
- **Server maintenance**: "Cannot connect" message
- **Audio device changes**: Restart client with venv activated
- **GPU limits**: Check Cerebrium quota

### Session Recovery
```bash
# If connection lost, restart with proper environment
source venv/bin/activate
export WS_SERVER="wss://your-deployment-id.cerebrium.app/ws"
python local_client.py

# If audio issues, check devices (with venv activated)
python -c "import sounddevice as sd; print(sd.query_devices())"

# If server issues, check deployment
curl -I https://your-deployment-id.cerebrium.app/health
```

## 💡 Use Cases

### 1. Voice Assistant
- Ask questions and get spoken answers
- Request information or explanations
- Get help with problem-solving

### 2. Language Practice
- Practice speaking and pronunciation
- Have conversations in different languages
- Get feedback on communication

### 3. Accessibility Tool
- Voice interface for hands-free computing
- Audio-based interaction for visual impairments
- Speech-to-text for communication assistance

### 4. Creative Collaboration
- Brainstorm ideas through voice
- Dictate and develop written content
- Interactive storytelling sessions

### 5. Learning and Education
- Ask questions about complex topics
- Request explanations and examples
- Practice presentation skills

## 🚫 Limitations

### Technical Limitations
- **Processing delay**: 1-2 second response time (improved with Ultravox)
- **Audio quality**: Depends on microphone and internet connection
- **Context memory**: Limited to recent conversation
- **Language support**: Best with English, other languages vary

### Usage Limitations
- **Background noise**: Can affect transcription accuracy
- **Multiple speakers**: Designed for single speaker
- **Continuous speech**: Processes in ~5 second chunks
- **Real-time interruption**: Supported but may have slight delay

### Infrastructure Limitations
- **GPU memory**: 8B model requires ~16GB VRAM
- **Concurrent users**: 3-5 per A10 instance
- **Model loading**: Initial connection may take 30-60s if cold start
- **No internet access**: System is air-gapped, no real-time data

## 📈 Optimization Tips

### For Better Performance
1. **Use wired internet**: More stable than WiFi
2. **Close unnecessary apps**: Reduce local resource usage
3. **Use quality microphone**: USB or headset microphone preferred
4. **Optimize environment**: Quiet space with minimal echo

### For Better Accuracy
1. **Speak clearly**: Enunciate words properly
2. **Use natural pace**: Not too fast or slow
3. **Minimize background noise**: Close windows, turn off fans
4. **Complete sentences**: Full thoughts work better than fragments

### For Cost Efficiency
1. **Monitor usage**: Check Cerebrium billing dashboard
2. **Use efficiently**: System scales to zero when idle
3. **Batch conversations**: Group usage to minimize cold starts
4. **Optimize settings**: Use appropriate model size for your needs

## 🔄 Updates and Maintenance

### Keeping System Updated
```bash
# With venv activated, update local dependencies
source venv/bin/activate
pip install -r local_client_requirements.txt --upgrade

# Redeploy with latest code
git pull origin main
cerebrium deploy

# Models update automatically on redeploy
```

### Monitoring Health
```bash
# Daily health check
curl -I https://your-deployment-id.cerebrium.app/health

# Check service status
curl https://your-deployment-id.cerebrium.app/debug

# Weekly full test (with venv activated)
source venv/bin/activate
python local_client.py
# Test a short conversation

# Monthly review
cerebrium logs voice-pipeline-airgapped | grep ERROR
```

### Virtual Environment Maintenance
```bash
# Check venv health
source venv/bin/activate
pip check  # Check for dependency conflicts

# Recreate if issues
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r local_client_requirements.txt
``` 