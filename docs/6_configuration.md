# 6. Configuration

## Environment Variables

Create a `.env` file in the project root:

```bash
# Core Settings
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3:8b

# TTS Settings
KOKORO_VOICE_ID=af_sarah
KOKORO_LANGUAGE=en-us
KOKORO_SPEED=1.0

# STT Settings
STT_MODEL=distil-medium-en
STT_DEVICE=cuda
STT_TEMPERATURE=0

# Observability
ENABLE_METRICS=True
ENABLE_TRACING=True
```

## Key Settings

### Model Paths
- **Kokoro Model**: [TO BE ADDED] - Where is kokoro-v1.0.onnx located?
- **Kokoro Voices**: [TO BE ADDED] - Where is voices-v1.0.bin located?
- **Python Path**: [TO BE ADDED] - What's the TTS Python path?

### Performance Tuning
- **VAD Parameters**: [TO BE ADDED] - What are the optimal VAD settings?
- **STT Temperature**: 0 (deterministic transcription)
- **LLM Temperature**: [TO BE ADDED] - What creativity level for responses?
- **TTS Speed**: [TO BE ADDED] - What's the optimal speech rate?

### Deployment Settings
- **Host**: [TO BE ADDED] - What host to bind to?
- **Port**: [TO BE ADDED] - What port to use?
- **GPU Memory**: [TO BE ADDED] - How much GPU memory to allocate?

## Docker Configuration

### GPU Requirements
```dockerfile
# [TO BE ADDED] - What GPU requirements?
--gpus all
--shm-size=2g
```

### Volume Mounts
```bash
# [TO BE ADDED] - What volumes to mount?
-v /path/to/models:/app/assets
-v /path/to/cache:/app/cache
```

### Resource Limits
```bash
# [TO BE ADDED] - What resource limits?
--memory=8g
--cpus=4
```

## Client Configuration

### WebSocket Settings
```javascript
// [TO BE ADDED] - What WebSocket settings?
const wsUrl = 'ws://localhost:8000/ws';
const audioConfig = {
  sampleRate: 16000,
  channels: 1
};
```

### Audio Settings
- **Sample Rate**: [TO BE ADDED] - What sample rate to use?
- **Channels**: [TO BE ADDED] - Mono or stereo?
- **Bit Depth**: [TO BE ADDED] - What bit depth?

## Validation

**Configuration Check**: [TO BE ADDED]
- How to validate all settings are correct?
- What tests to run?
- What logs to check?

---

**Next**: Read [Troubleshooting](./7_troubleshooting.md) for common issues and solutions. 