# API Setup Guide

Complete guide for obtaining and configuring API keys for the voice pipeline.

## Required API Keys

1. **Hugging Face Token** - For Ultravox STT/LLM
2. **OpenAI API Key** - For text-to-speech

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

## OpenAI Setup

### 1. Create Account
- Visit [platform.openai.com](https://platform.openai.com/)
- Sign up and add billing information

### 2. Generate API Key
- Go to [API Keys](https://platform.openai.com/api-keys)
- Click "Create new secret key"
- Name: `voice-pipeline-tts`
- Copy key (starts with `sk-`)

### 3. Test Access
```bash
curl -H "Authorization: Bearer sk_your_key" \
     "https://api.openai.com/v1/models"
```

## Configuration

### Cerebrium Secrets (Production)
Edit `cerebrium.toml`:
```toml
[cerebrium.secrets]
HUGGING_FACE_TOKEN = "hf_your_token_here"
OPENAI_API_KEY = "sk_your_key_here"
OPENAI_TTS_VOICE = "nova"
OPENAI_TTS_MODEL = "tts-1"
```

### Environment Variables (Local)
```bash
export HUGGING_FACE_TOKEN="hf_your_token_here"
export OPENAI_API_KEY="sk_your_key_here"
```

## Voice Options

### Available OpenAI Voices
- **nova** (default) - Balanced, natural
- **alloy** - Neutral, professional  
- **echo** - Slightly robotic
- **fable** - Warm, storytelling
- **onyx** - Deep, authoritative
- **shimmer** - Bright, energetic

### Models
- **tts-1** (default) - Fast, good quality
- **tts-1-hd** - Higher quality, slower

## Cost Information

### OpenAI TTS Pricing
- **TTS-1**: $15.00 per 1M characters
- **TTS-1-HD**: $30.00 per 1M characters
- **Typical conversation**: ~$0.01-0.05

### Hugging Face
- **Free tier**: Generous limits
- **Pro**: $20/month for higher limits

## Security Best Practices

- ✅ Use Cerebrium secrets for production
- ✅ Add .env to .gitignore  
- ❌ Never commit keys to git
- ❌ Don't share keys in messages

## Troubleshooting

### Common Errors
```bash
# 401 Unauthorized - Check token validity
# 403 Forbidden - Check permissions/billing
# 429 Rate Limited - Reduce request frequency
```

### Verification Commands
```bash
# Test Hugging Face
curl -H "Authorization: Bearer $HUGGING_FACE_TOKEN" \
     "https://huggingface.co/api/whoami"

# Test OpenAI  
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     "https://api.openai.com/v1/models"
```

## Support Resources

- **Hugging Face**: [huggingface.co/docs](https://huggingface.co/docs)
- **OpenAI**: [platform.openai.com/docs](https://platform.openai.com/docs)
- **Cerebrium**: [docs.cerebrium.ai](https://docs.cerebrium.ai) 