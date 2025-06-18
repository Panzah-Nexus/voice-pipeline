# API Setup Guide

Complete guide for obtaining and configuring the Hugging Face token for the air-gapped voice pipeline.

## Required Token

**Hugging Face Token** - For downloading Ultravox STT/LLM models

## Hugging Face Setup

### 1. Create Account
- Visit [huggingface.co](https://huggingface.co/)
- Sign up and verify email

### 2. Generate Token
- Go to [Settings → Tokens](https://huggingface.co/settings/tokens)
- Click "New token"
- Name: `voice-pipeline`
- Type: `Read`
- Click "Generate a token"
- Copy token (starts with `hf_`)

### 3. Test Access
```bash
curl -H "Authorization: Bearer hf_your_token" \
     "https://huggingface.co/api/whoami"
```

## Configuration

### Cerebrium Secrets (Production)
Edit `cerebrium.toml`:
```toml
[cerebrium.secrets]
HF_TOKEN = "hf_your_token_here"
# Optional: Configure Piper TTS model
PIPER_MODEL = "en_US-lessac-medium"
PIPER_SAMPLE_RATE = "22050"
```

### Environment Variables (Local Testing)
```bash
export HF_TOKEN="hf_your_token_here"
```

## Model Information

### Ultravox Models
Ultravox combines Speech-to-Text and Language Model capabilities in a single model:
- **8B Model**: `fixie-ai/ultravox-v0_4_1-llama-3_1-8b` (Recommended)
- **70B Model**: `fixie-ai/ultravox-v0_4_1-llama-3_1-70b` (Requires more VRAM)
- **7B Mistral**: `fixie-ai/ultravox-v0_4-mistral-7b` (Alternative)

### Piper TTS Models
Piper runs locally on the GPU for text-to-speech:
- **Default**: `en_US-lessac-medium` (American English)
- **Alternatives**: Multiple voices available in 50+ languages
- Models are downloaded automatically on first use

## Cost Information

### Hugging Face
- **Free tier**: Generous limits for model downloads
- **Pro**: $20/month for higher download speeds and priority access

### Infrastructure
- **Cerebrium A10**: ~$0.50-1.00/hour when active
- **Auto-scaling**: Scales to zero when idle (no cost)

## Security Best Practices

- ✅ Use Cerebrium secrets for production
- ✅ Add .env to .gitignore  
- ❌ Never commit tokens to git
- ❌ Don't share tokens in messages

## Troubleshooting

### Common Errors
```bash
# 401 Unauthorized - Check token validity
# 403 Forbidden - Check model access permissions
# 429 Rate Limited - Wait or upgrade to Pro
```

### Verification Commands
```bash
# Test Hugging Face token
curl -H "Authorization: Bearer $HF_TOKEN" \
     "https://huggingface.co/api/whoami"

# Check model access
curl -H "Authorization: Bearer $HF_TOKEN" \
     "https://huggingface.co/api/models/fixie-ai/ultravox-v0_4_1-llama-3_1-8b"
```

## Support Resources

- **Hugging Face**: [huggingface.co/docs](https://huggingface.co/docs)
- **Ultravox Models**: [fixie-ai on HuggingFace](https://huggingface.co/fixie-ai)
- **Piper TTS**: [rhasspy/piper](https://github.com/rhasspy/piper)
- **Cerebrium**: [docs.cerebrium.ai](https://docs.cerebrium.ai) 