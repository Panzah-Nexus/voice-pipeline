# Kokoro TTS Setup Guide

This guide provides details on the `KokoroTTSService`, the offline Text-to-Speech (TTS) engine used in this voice pipeline.

## What is Kokoro?

Kokoro is a high-quality, open-weight text-to-speech engine that runs efficiently on GPUs. By using Kokoro, the voice pipeline can generate natural-sounding speech in real-time without relying on any external, cloud-based TTS APIs. This is a critical component for maintaining the pipeline's fully air-gapped design.

## `KokoroTTSService`

This project uses a custom `KokoroTTSService` (defined in `src/kokoro_tts_service.py`) that integrates the Kokoro engine with the `pipecat-ai` framework.

-   It receives text frames from the `UltravoxWithContextService`.
-   It synthesizes the speech and generates raw audio frames.
-   It streams these audio frames back into the pipeline to be sent to the client.
-   It is designed for real-time streaming, which means audio starts playing on the client side almost immediately, without waiting for the full sentence to be generated.

## Configuration

The Kokoro TTS service is primarily configured through environment variables set in your RunPod pod template.

### Key Environment Variables

-   `KOKORO_MODEL_PATH`: The path inside the Docker container to the Kokoro ONNX model file (e.g., `/models/kokoro/model_fp16.onnx`).
-   `KOKORO_VOICES_PATH`: The path to the voices binary file (e.g., `/models/kokoro/voices-v1.0.bin`).
-   `KOKORO_VOICE_ID`: Specifies which voice to use. The default is `af_bella`, but you can choose any voice available in your voices file.
-   `KOKORO_SAMPLE_RATE`: The output sample rate. The default is `24000` Hz.

### Instantiation in `pipecat_pipeline.py`

The service is initialized in the main pipeline script with these variables:

```python
# 2️⃣ Local TTS (Kokoro)
tts = KokoroTTSService(
    model_path=KOKORO_MODEL_PATH,
    voices_path=KOKORO_VOICES_PATH,
    voice_id=KOKORO_VOICE_ID,
    sample_rate=SAMPLE_RATE,
)
```

## Troubleshooting

### TTS Fails to Initialize
If you see errors in your RunPod logs related to Kokoro, such as "model file not found" or "voices file not found":

1.  **Check Model Paths**: Verify that the paths set in your environment variables (`KOKORO_MODEL_PATH`, `KOKORO_VOICES_PATH`) are correct and point to where the models are located inside your Docker container.
2.  **Verify Model Files**: Ensure the model files were correctly added to your Docker image during the build process. Check your `Dockerfile` for `COPY` or `ADD` commands related to the `/models/kokoro/` directory.

### No Audio Output
If the pipeline appears to be working but you hear no spoken response:

1.  **Check Kokoro Logs**: Look for any errors from `KokoroTTSService` in the RunPod logs.
2.  **Check Voice ID**: Make sure the `KOKORO_VOICE_ID` you've set is valid and exists within your voices binary. An invalid ID may cause the service to fail silently.
3.  **Check Downstream**: Ensure there are no issues with the WebSocket connection sending the audio back to your client. 