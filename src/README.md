# Source Code Structure

This directory contains the core deployment code for the voice pipeline.

## Core Files (Required for Deployment)

### main.py
Entry point for the voice pipeline server. Handles initialization and fallback logic.

### pipecat_pipeline.py
Main pipeline implementation using Pipecat framework:
- Integrates Ultravox for combined STT+LLM processing
- Uses custom Piper TTS service for air-gapped deployment
- Handles WebSocket connections via FastAPI
- No external API calls during operation

### piper_tts_service.py
Consolidated Pipecat-compatible TTS service that:
- Runs Piper TTS directly via subprocess (no HTTP server needed)
- Handles model downloading during deployment
- Provides proper Pipecat frame integration
- Supports audio resampling from 22050 Hz to 16000 Hz

## Architecture Notes

1. **Air-Gapped Design**: All AI processing happens locally on the GPU without external API calls
2. **Simplified TTS**: We use a direct subprocess approach instead of the official Pipecat Piper service to avoid HTTP server complexity
3. **Cerebrium Deployment**: Models are pre-downloaded during container build for fast startup

## Removed Files

The following files were removed during cleanup:
- `local_piper_tts.py` - Redundant wrapper, functionality merged into `piper_tts_service.py`
- `piper_service.py` - Lower-level implementation, merged into `piper_tts_service.py`
- `debug_websocket_handler.py` - Unused debugging code

Test utilities have been moved to the `utils/` directory. 