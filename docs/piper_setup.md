# Piper TTS Setup Guide

This guide explains how Piper TTS is integrated with Pipecat for local, air-gapped text-to-speech.

## What is Piper?

Piper is a fast, local neural text-to-speech system that:
- Runs completely offline (no API calls)
- Optimized for edge devices and GPUs
- Supports 50+ languages with multiple voices
- Produces high-quality, natural-sounding speech
- Real-time synthesis with <200ms latency

## Integration with Pipecat

Piper is integrated as a TTS service in the Pipecat framework:

```python
from pipecat.services.piper.tts import PiperTTSService
import aiohttp

# Initialize Piper TTS
async def create_piper_tts():
    session = aiohttp.ClientSession()
    
    tts_service = PiperTTSService(
        base_url="http://localhost:5000/api/tts",  # Local Piper server
        aiohttp_session=session,
        sample_rate=22050
    )
    return tts_service
```

## Running Piper Server

### Option 1: Docker (Recommended)
```bash
# Start Piper TTS server locally
docker run -d \
  --name piper-tts \
  -p 5000:5000 \
  -v piper-models:/models \
  rhasspy/piper:latest \
  --model en_US-lessac-medium
```

### Option 2: Python Package
```bash
# Install Piper
pip install piper-tts

# Run server
piper --model en_US-lessac-medium.onnx --http-server 5000
```

## Available Voices

### English Voices
| Voice | Quality | Characteristics |
|-------|---------|----------------|
| `en_US-lessac-medium` | High | American, neutral |
| `en_US-amy-medium` | High | American, female |
| `en_GB-alan-medium` | High | British, male |
| `en_GB-jenny_dioco-medium` | High | British, female |

### Other Languages (Examples)
- German: `de_DE-thorsten-medium`
- French: `fr_FR-siwis-medium`
- Spanish: `es_ES-davefx-medium`
- Italian: `it_IT-riccardo-x_low`
- And 45+ more languages

## Configuration

In `cerebrium.toml`:
```toml
[cerebrium.secrets]
PIPER_MODEL = "en_US-lessac-medium"  # Voice selection
PIPER_SAMPLE_RATE = "22050"          # Audio quality
```

## Pipeline Integration

Piper receives text from Ultravox and generates audio:

```python
# In the Pipecat pipeline
pipeline = Pipeline([
    transport.input(),           # Audio from user
    ultravox_service,           # Audio → Text response
    piper_tts,                  # Text → Audio
    transport.output(),         # Audio to user
])
```

## Performance Optimization

### GPU Acceleration
Piper automatically uses GPU when available:
- CUDA for NVIDIA GPUs (like A10)
- Metal for Apple Silicon
- Falls back to CPU if needed

### Latency Optimization
- Pre-load models during deployment
- Use appropriate sample rates (22050 Hz is optimal)
- Enable streaming for real-time synthesis

### Memory Usage
- Medium models: ~100MB
- High models: ~200MB
- Low models: ~50MB

## Troubleshooting

### Piper Server Not Found
```bash
# Check if Piper is running
curl http://localhost:5000/health

# If not, start the server:
docker run -p 5000:5000 rhasspy/piper:latest
```

### Voice Model Issues
```bash
# List available models
curl http://localhost:5000/models

# Download specific model
curl -o en_US-amy-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx
```

### Audio Quality Issues
- Increase sample rate to 44100 for higher quality
- Use "high" quality models instead of "medium"
- Check audio output device compatibility

## Air-Gapped Deployment

For fully air-gapped operation:

1. **Pre-download Models**: During deployment, models are cached
2. **Local Server**: Piper runs within the Cerebrium container
3. **No Internet**: Once deployed, no external connections needed
4. **Data Privacy**: All synthesis happens on your infrastructure

## Advanced Configuration

### Custom Voices
```python
# Use different voice per response
tts_service = PiperTTSService(
    voice_id="en_GB-jenny_dioco-medium",  # British female
    speed=1.1,  # Slightly faster
    pause_ms=500,  # Pause between sentences
)
```

### Multi-language Support
```python
# Switch languages dynamically
voices = {
    "en": "en_US-amy-medium",
    "es": "es_ES-davefx-medium",
    "fr": "fr_FR-siwis-medium",
}

# Select based on detected language
tts_service.set_voice(voices[detected_lang])
```

## Comparison with Cloud TTS

| Feature | Piper (Local) | Cloud TTS |
|---------|---------------|-----------|
| Latency | <200ms | 500-1000ms |
| Privacy | Complete | Data sent to cloud |
| Cost | Free after setup | Per-character fees |
| Quality | Very good | Excellent |
| Languages | 50+ | 100+ |
| Internet | Not required | Required |

For air-gapped deployments, Piper provides the best balance of quality, performance, and privacy. 