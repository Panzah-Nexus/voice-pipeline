# 4. STT Service: Faster-Whisper

The Speech-to-Text (STT) service is responsible for transcribing raw audio into text with low latency and high accuracy. The pipeline uses the `FasterWhisperSTTService` provided by `pipecat`, which is a highly optimized implementation of OpenAI's Whisper model.

## Model and Configuration

*   **Model:** `distil-medium-en`
    *   This is a distilled version of the `medium.en` model, offering a significant speed-up with minimal impact on accuracy. It is well-suited for real-time applications on constrained hardware.

*   **Device:** `CUDA`
    *   The model runs on an NVIDIA GPU using the CUDA execution provider for maximum performance. The system will fall back to CPU if a compatible GPU is not detected, but this is not recommended for production use.

*   **Temperature:** `0`
    *   The transcription temperature is set to `0`. This forces the model to be deterministic, choosing the most likely next token at each step. It prevents randomness and "creative" transcriptions, which is ideal for this use case.

## Performance and Latency

The STT service is a critical component in the overall turn-taking latency. With the `distil-medium-en` model running on an NVIDIA L4 GPU, you can expect the following performance characteristics:

*   **Transcription Latency:** Typically **under 300ms** for short utterances (a few seconds of speech).
*   **Real-time Factor (RTF):** Well below 0.1, meaning it can transcribe audio much faster than real-time.

These numbers ensure that the time from when a user stops speaking to when the LLM receives the transcribed text is kept to a minimum, enabling a fluid conversational experience.

## Implementation Details

The `FasterWhisperSTTService` is a built-in `pipecat` service. The pipeline configures it with the specified model and device settings. It receives audio frames from the VAD, transcribes them, and emits a `TranscriptionFrame` for consumption by the LLM service. 