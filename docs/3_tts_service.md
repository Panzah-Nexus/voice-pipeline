# 3. TTS Service: Isolated Subprocess

The Text-to-Speech (TTS) service is one of the most critical and resource-intensive parts of the pipeline. To ensure stability and avoid dependency conflicts, it runs in a completely isolated Python virtual environment, managed as a sub-process.

This document explains the rationale behind this design and how it works.

## Rationale for Isolation

The Kokoro TTS engine relies on `kokoro-onnx` and, for GPU support, `onnxruntime-gpu`. These packages have large, complex dependencies, including specific versions of CUDA libraries, that can easily clash with other libraries in the main application.

By running the TTS service in a separate process with its own virtual environment (`/venv/tts`), we achieve two goals:

1.  **Dependency Encapsulation:** The main application environment remains clean and lightweight. Heavy GPU libraries are only loaded within the sub-process.
2.  **Stability:** Any crashes or memory issues within the TTS engine are contained within the sub-process and will not bring down the entire voice pipeline. The parent process can detect the failure and restart it.

## Communication Protocol: JSONL

The main application communicates with the TTS sub-process (`src/kokoro/tts_subprocess_server.py`) over its `stdin` and `stdout` streams using a simple newline-delimited JSON (JSONL) protocol.

### Request

The parent process sends a single-line JSON object to the sub-process's `stdin` for each synthesis request.

*   **Format:**
    ```json
    {"text": "Hello world", "voice_id": "af_sarah", "language": "en-us", "speed": 1.0}
    ```
*   **Fields:**
    *   `text` (required): The UTF-8 text to synthesize.
    *   Other keys (`voice_id`, `language`, `speed`) are optional and will fall back to the defaults configured at startup.

### Response Stream

For each request, the sub-process writes a series of JSON objects to `stdout`, each terminated by a newline. The parent reads this as a stream and converts the messages into `pipecat` frames.

*   **Format & Sequence:**
    ```json
    {"type": "started"}
    {"type": "audio_chunk", "sample_rate": 24000, "data": "<base64_encoded_pcm>"}
    // ... 0 or more audio_chunk messages
    {"type": "stopped"}
    {"type": "eof"}
    ```
*   **Message Types:**
    *   `started` / `stopped`: Map to `TTSStartedFrame` and `TTSStoppedFrame`.
    *   `audio_chunk`: Contains the raw audio data as a base64-encoded string, which is decoded and wrapped in a `TTSAudioRawFrame`.
    *   `eof`: A sentinel message that signals the end of the response stream for the current request.
    *   `error`: If something goes wrong, an error message is sent: `{"type": "error", "message": "..."}`.

## Audio Chunking and Buffer Limits

A crucial implementation detail is how the audio data is streamed. The `asyncio.StreamReader` used by the parent process has a default buffer limit of 64 KB per line. A long sentence could easily produce enough audio to exceed this limit if sent as a single base64-encoded chunk.

To prevent this, the TTS sub-process server preemptively splits the raw PCM audio into **16 KB chunks** *before* base64 encoding. This ensures that the final JSON line for each `audio_chunk` message remains safely under the 64 KB limit.

## Process Lifecycle and Management

The entire sub-process lifecycle is managed by the `KokoroSubprocessTTSService` class (`src/kokoro/tts_subprocess_wrapper.py`).

1.  **Lazy Initialization:** The sub-process is not started when the pipeline is created. It is launched on the first call to `run_tts()`.
2.  **Re-use:** The same sub-process is kept alive and reused for subsequent TTS requests to avoid the overhead of re-initializing the Kokoro model.
3.  **Termination:** The sub-process is automatically terminated if the `run_tts()` task is cancelled (e.g., by a user interruption) or if a fatal error occurs, ensuring clean shutdown. 