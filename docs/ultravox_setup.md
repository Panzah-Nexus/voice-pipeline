# Ultravox Setup Guide

This guide explains how Ultravox is integrated with Pipecat for the air-gapped voice pipeline.

## What is Ultravox?

Ultravox is a breakthrough multimodal LLM that combines Speech-to-Text (STT) and Language Model (LLM) capabilities into a single model. This eliminates the traditional cascaded pipeline approach, resulting in:

- **60% faster response times** (1-2 seconds vs 2-5 seconds)
- **Better audio understanding** (tone, emotion, context)
- **No transcription errors** between STT and LLM
- **Lower GPU memory usage** than running separate models

## How Ultravox Works with Pipecat

In Pipecat, Ultravox is implemented as a specialized STT service that also handles the LLM functionality:

```python
from pipecat.services.ultravox.stt import UltravoxSTTService

# Initialize Ultravox (combines STT + LLM)
ultravox = UltravoxSTTService(
    model_size="fixie-ai/ultravox-v0_4_1-llama-3_1-8b",
    hf_token=os.environ.get("HF_TOKEN"),
    temperature=0.5,
    max_tokens=150,
)
```

## Pipeline Architecture

Traditional cascaded approach:
```
Audio → STT → Text → LLM → Response → TTS → Audio
```

Ultravox approach (faster):
```
Audio → Ultravox (STT+LLM) → Response → Piper TTS → Audio
```

## Model Selection

| Model | Size | VRAM Required | Speed | Quality |
|-------|------|---------------|-------|---------|
| `ultravox-v0_4_1-llama-3_1-8b` | 8B | ~16GB | Fast | Excellent |
| `ultravox-v0_4_1-llama-3_1-70b` | 70B | ~80GB | Slower | Best |
| `ultravox-v0_4-mistral-7b` | 7B | ~14GB | Fastest | Good |

For Cerebrium A10 (24GB VRAM), the 8B model is recommended.

## Configuration in Pipecat

The Ultravox service is configured in `src/pipecat_pipeline.py`:

```python
# Initialize Ultravox with optimal settings for A10
stt_service = UltravoxSTTService(
    model_size="fixie-ai/ultravox-v0_4_1-llama-3_1-8b",
    hf_token=get_secret("HF_TOKEN"),  # Only for model download
    temperature=0.5,  # Balance between creativity and accuracy
    max_tokens=150,   # Reasonable response length
)
```

## Air-Gapped Benefits

1. **No External API Calls**: Once deployed, Ultravox runs entirely on the GPU
2. **Data Privacy**: Audio never leaves your infrastructure
3. **Predictable Performance**: No network latency to external services
4. **Cost Effective**: No per-request API fees

## Performance Tuning

### Temperature Settings
- `0.3-0.5`: More deterministic, better for commands
- `0.5-0.7`: Balanced, good for conversation
- `0.7-0.9`: More creative, better for storytelling

### Max Tokens
- `50-100`: Quick responses, commands
- `100-200`: Normal conversation
- `200-500`: Detailed explanations

## Troubleshooting

### Model Not Loading
```bash
# Check if HF token is set
echo $HF_TOKEN

# Verify model access
curl -H "Authorization: Bearer $HF_TOKEN" \
     "https://huggingface.co/api/models/fixie-ai/ultravox-v0_4_1-llama-3_1-8b"
```

### GPU Memory Issues
```bash
# Monitor GPU usage during deployment
cerebrium logs voice-pipeline-airgapped | grep "CUDA"

# If OOM errors, consider:
# 1. Reducing max_tokens
# 2. Lowering max_concurrency in cerebrium.toml
# 3. Using smaller model (7B Mistral variant)
```

## Integration with Piper TTS

Ultravox outputs text that's passed directly to Piper TTS:

```python
pipeline = Pipeline([
    transport.input(),
    context_aggregator.user(),
    ultravox_service,  # Processes audio → text response
    piper_tts,         # Converts text → audio
    context_aggregator.assistant(),
    transport.output(),
])
```

This creates a fully air-gapped voice pipeline with no external dependencies during operation.

