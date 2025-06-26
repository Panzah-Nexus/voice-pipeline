# 6. Configuration Reference

This document provides a reference for all the environment variables and command-line arguments used to configure the voice pipeline.

## Environment Variables

Configuration is primarily handled through environment variables. Create a `.env` file in the project root to manage these settings.

### Core Pipeline
| Variable | Description | Default |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | The base URL for the Ollama server API. | `http://localhost:11434` |
| `LLM_MODEL` | The name of the LLM model to use from Ollama. | `llama3-8b` |

### TTS Service (`KokoroSubprocessTTSService`)
| Variable | Description | Default |
| --- | --- | --- |
| `KOKORO_PYTHON_PATH` | The absolute path to the Python executable inside the isolated TTS virtual environment. | `/venv/tts/bin/python` |
| `KOKORO_MODEL_PATH` | Path to the `kokoro-vX.Y.onnx` model file. | `assets/kokoro-v1.0.onnx` |
| `KOKORO_VOICES_PATH` | Path to the `voices-vX.Y.bin` file. | `assets/voices-v1.0.bin` |
| `KOKORO_VOICE_ID` | The default voice ID to use for synthesis. | `af_sarah` |
| `KOKORO_LANGUAGE` | The default language code. | `en-us` |
| `KOKORO_SPEED` | The default speaking speed. | `1.0` |

### STT Service (`FasterWhisperSTTService`)
| Variable | Description | Default |
| --- | --- | --- |
| `STT_MODEL` | The `faster-whisper` model to use. | `distil-medium-en` |

### Observability
| Variable | Description | Default |
| --- | --- | --- |
| `ENABLE_METRICS` | Set to `True` to enable `pipecat` service metrics. | `False` |
| `ENABLE_TRACING` | Set to `True` to enable OpenTelemetry tracing. | `False` |
| `OTEL_EXPORTER_OTLP_ENDPOINT`| The OTLP collector endpoint for traces. | `http://localhost:4317` |
| `OTEL_SERVICE_NAME` | The service name to report in traces. | `voice-pipeline` |

## Command-Line Arguments

The primary entry point `src/main.py` accepts command-line arguments that can override environment variables.

*   `--host`: The host interface to bind the server to. (Default: `0.0.0.0`)
*   `--port`: The port to bind the server to. (Default: `8000`)
*   `--log-level`: The logging level for the application. (Default: `INFO`) 