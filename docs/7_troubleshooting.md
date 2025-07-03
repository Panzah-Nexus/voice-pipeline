# 7. Troubleshooting

## Common Issues

### GPU Not Detected
**Error**: `Could not find an enabled CUDA execution provider`

**Solution**:
```bash
# Check NVIDIA drivers
nvidia-smi

# Install NVIDIA Container Toolkit
# Follow: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/

# Run with GPU support
docker run --gpus all voice-pipeline
```

### TTS Service Fails
**Error**: `TTS subprocess terminated unexpectedly`

**Solution**:
```bash
# Check model files exist
ls assets/kokoro-v1.0.onnx
ls assets/voices-v1.0.bin

# Verify Python path
echo $KOKORO_PYTHON_PATH

# Test TTS manually
/venv/tts/bin/python src/kokoro/tts_subprocess_server.py --debug
```

### Ollama Not Running
**Error**: Connection refused to Ollama

**Solution**:
```bash
# Start Ollama
ollama serve

# Check model is available
ollama list

# Pull model if needed
ollama pull llama3:8b
```

### Whisper Model Not Found
**Error**: Whisper model download failed

**Solution**:
```bash
# Check CUDA is available
nvidia-smi

# Verify Faster Whisper installation
python -c "import faster_whisper; print('Faster Whisper OK')"

# Download model manually if needed
# Models are auto-downloaded on first use
```

### WebSocket Connection Fails
**Error**: WebSocket connection refused

**Solution**:
```bash
# Check server is running
curl http://localhost:8000/

# Check port is exposed
docker ps | grep 8000

# Test WebSocket endpoint
wscat -c ws://localhost:8000/ws
```

## Debug Commands

### Check System Status
```bash
# GPU status
nvidia-smi

# Docker status
docker ps
docker logs voice-pipeline

# Ollama status
ollama list
curl http://localhost:11434/api/tags
```

### Check Logs
```bash
# Container logs
docker logs -f voice-pipeline

# Application logs
docker exec voice-pipeline tail -f /app/logs/app.log

# TTS subprocess logs
docker exec voice-pipeline tail -f /app/logs/tts.log
```

### Performance Issues
**High Latency**: [TO BE ADDED]
- What causes high latency?
- How to measure latency?
- What optimizations to try?

**High Memory Usage**: [TO BE ADDED]
- What causes high memory usage?
- How to monitor memory?
- What memory optimizations?

**GPU Memory Issues**: [TO BE ADDED]
- What causes GPU OOM?
- How to reduce GPU memory?
- What GPU settings to adjust?

## Recovery Procedures

### Restart Services
```bash
# Restart container
docker restart voice-pipeline

# Restart Ollama
pkill ollama
ollama serve

# Restart client
# Refresh browser or restart client app
```

### Reset Configuration
```bash
# Clear cache
docker exec voice-pipeline rm -rf /app/cache/*

# Reset models
docker exec voice-pipeline rm -rf /app/models/*

# Rebuild container
docker build --no-cache -t voice-pipeline .
```

## Getting Help

### Information to Include
- **Error logs**: [TO BE ADDED] - What logs to include?
- **System info**: [TO BE ADDED] - What system details?
- **Configuration**: [TO BE ADDED] - What config to share?

### Debug Mode
```bash
# Enable debug logging
ENABLE_TRACING=True
ENABLE_METRICS=True
LOG_LEVEL=DEBUG

# Run with debug flags
docker run --gpus all -e LOG_LEVEL=DEBUG voice-pipeline
```

---

**Next**: Review [Contributing](./8_contributing.md) for development guidelines. 