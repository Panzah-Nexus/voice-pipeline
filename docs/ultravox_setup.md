# Ultravox Setup Guide

This guide explains how the **Ultravox** model is integrated into the voice pipeline using the custom `UltravoxWithContextService` to enable low-latency, context-aware conversations.

## What is Ultravox?

Ultravox is a state-of-the-art multimodal model that combines Speech-to-Text (STT) and a Large Language Model (LLM) into a single, unified system. This approach offers significant advantages:

-   **Dramatically Lower Latency**: Processing audio directly into a language response eliminates the separate transcription step.
-   **Superior Audio Understanding**: The model can interpret nuances in speech like tone and pauses.
-   **No Transcription Errors**: Eliminates the risk of STT errors being passed to the LLM.

## `UltravoxWithContextService`

This project uses a custom `UltravoxWithContextService` (defined in `src/ultravox_with_context.py`) which extends the base Pipecat service to include **conversation memory**. It passes the conversation history back to the model with each new request, enabling a natural, coherent dialogue.

## Pipeline Integration

**Our Ultravox Approach (Faster and Context-Aware):**
`Audio → UltravoxWithContextService (STT+LLM) → Response Text → KokoroTTSService → Audio`

## Model Selection

The pipeline is configured to use a performant and high-quality version of Ultravox that runs efficiently on an NVIDIA L4 GPU.

| Model                                        | Size | Est. VRAM | Performance on L4 |
| -------------------------------------------- | ---- | --------- | ----------------- |
| `fixie-ai/ultravox-v0_5-llama-3_1-8b`        | 8B   | ~16-18 GB | **Excellent**     |

## Configuration in `pipecat_pipeline.py`

The service is instantiated in `src/pipecat_pipeline.py`. Key parameters include:

```python
ultravox_processor = UltravoxWithContextService(
    model_name="fixie-ai/ultravox-v0_5-llama-3_1-8b",
    hf_token=HF_TOKEN,  # Injected from RunPod environment variable
    temperature=0.3,    # Lower value for more consistent, less random responses
    max_tokens=50,      # Controls the max length of a response
    system_instruction=SYSTEM_INSTRUCTION, # Defines the AI's persona
)
```

-   `temperature`: Controls the "creativity" of the AI. Lower is better for factual, assistant-like roles.
-   `max_tokens`: Prevents overly long responses, keeping the conversation snappy.
-   `system_instruction`: A powerful feature used to set the AI's persona, rules, and objectives.

## Troubleshooting

### Model Fails to Load
If you see errors related to model loading in your RunPod logs (`401 Unauthorized` or file-not-found):

1.  **Check `HF_TOKEN`**: Ensure the `HF_TOKEN` environment variable is correctly set in your RunPod pod configuration.
2.  **Model Name**: Verify the model name in `pipecat_pipeline.py` is correct.
3.  **Network Access**: On first launch, the pod needs internet access to contact Hugging Face.

### GPU Memory Issues (CUDA Out of Memory)
While unlikely on an NVIDIA L4 with the 8B model, if you encounter this error, it may indicate a memory leak. Use `nvidia-smi` (by SSHing into the pod) to monitor VRAM usage.

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

