# 3. Model Decisions

A core principle of this project is the exclusive use of **open-source, locally-hosted models**. This ensures data privacy, eliminates reliance on third-party APIs, and provides full control over the operational environment. All decisions described below were made with this principle as a primary driver.

## Framework Choices

### Pipecat + RTVI
**Chosen**: Pipecat framework with RTVI (Real-Time Voice Interaction)

**Alternatives Considered**:
- **Custom WebRTC pipeline**: Building a custom pipeline from scratch would offer maximum control but require significant development effort in handling real-time audio and service orchestration.
- **LangChain + custom audio**: While excellent for text-based chains, LangChain's native support for real-time, interruptible voice is less mature than Pipecat's.

**Why Pipecat**:
- **Built for Voice**: Pipecat is specifically designed for real-time voice applications, with features like interruptibility and low-latency streaming built-in.
- **Observability**: Comes with good tools for tracing and metrics, which is crucial for debugging a complex pipeline.
- **Extensible**: Provides a solid foundation of services while making it easy to integrate custom components like Kokoro TTS.

## Speech-to-Text (STT)

### Faster Whisper ASR
**Chosen**: Faster Whisper for local speech recognition

**Alternatives Considered**:
- **The original OpenAI Whisper**: The direct Python implementation is accurate but significantly slower and more memory-intensive than optimized forks.
- **Mozilla DeepSpeech**: An older but still viable open-source model, though generally less accurate than modern Whisper-based models.
- **NVIDIA NeMo ASR**: A powerful toolkit with high-accuracy models, but often requires a more complex setup and specific NVIDIA software dependencies.

**Why Faster Whisper**:
- **Open-Source & Local**: As a project committed to using locally-hosted models, Faster Whisper was the ideal choice. It's a highly optimized version of an open-source model.
- **Performance**: It delivers a 2-4x speed improvement and uses less VRAM compared to the original Whisper, which is critical for real-time responsiveness without needing top-tier enterprise GPUs.
- **Accuracy**: It maintains the high accuracy of the original Whisper models, providing reliable transcriptions.

**Model Configuration**:
- **Model**: `distil-medium-en` (a distilled version of Whisper, offering a great balance between speed and accuracy for English).
- **Device**: CUDA for GPU acceleration.
- **Temperature**: 0 for deterministic, consistent output.

## Language Model (LLM)

### Ollama + Llama 3.1 8B
**Chosen**: Ollama with Llama 3.1 8B parameter model

**Alternatives Considered**:
- **Mistral 7B**: A very strong open-source alternative, highly capable and fast. It was a close contender.
- **Phi-3-mini**: An excellent small language model that performs very well for its size, making it a great option for resource-constrained environments.
- **Llama-3-70B**: A much larger, more capable model that provides higher-quality responses but requires significantly more VRAM and compute resources, making it unsuitable for consumer-grade hardware.

**Why Ollama + Llama 3.1 8B**:
- **Ease of Use**: Sticking to the open-source principle, Ollama provides an incredibly easy way to serve various LLMs locally with a single command.
- **Balanced Performance**: `Llama-3-8B` hits the sweet spot for this pipeline. It's powerful enough for coherent, helpful conversation while being fast enough (~50-70 tokens/sec) for real-time interaction on a consumer-grade GPU.
- **Community & Support**: Llama 3 has massive community support and is widely available, ensuring long-term viability.

**Configuration**:
- **Context window**: `4096` tokens. This provides enough history for multi-turn coaching scenarios without excessively burdening the model.
- **Temperature**: `0.7`. This allows for creative but still coherent and controlled responses suitable for a coaching context.
- **System prompt**: A prompt designed to guide the AI to act as a supportive but challenging coach, such as: *"You are a helpful sales coaching assistant. Your goal is to roleplay as a customer and provide constructive feedback to the trainee. Be realistic and adapt your personality based on the scenario."*

## Text-to-Speech (TTS)

### Kokoro TTS
**Chosen**: Kokoro for local, high-quality speech synthesis

**Alternatives Considered**:
- **Piper TTS**: A very fast, lightweight open-source engine. The voice quality is good but can sound more robotic than Kokoro for some voices. It's an excellent choice for CPU-only or low-resource systems.
- **Coqui XTTS**: A powerful open-source model with very high-quality voices and zero-shot voice cloning capabilities. However, it is more resource-intensive than Kokoro.

**Why Kokoro**:
- **Voice Quality**: Kokoro was chosen for its high-quality, natural-sounding open-source voices that can run efficiently for real-time synthesis.
- **Performance**: It offers low-latency audio generation (~200ms TTFA), which is critical for conversational AI. Your work to GPU-accelerate it made it ~30x faster.
- **Isolated Subprocess**: A key benefit is its design to run in an isolated subprocess, which prevents Python dependency conflicts within the main application—a crucial factor for stable local deployment.

**Configuration**:
- **Voice**: `af_sarah`. Chosen for its clear, professional, and pleasant tone, which is well-suited for a coaching avatar.
- **Speed**: `1.0x`. The default speed provides a natural-sounding pace. This could be made configurable for different coaching styles.
- **Language**: `en-us`.

## Voice Activity Detection (VAD)

### Silero VAD
**Chosen**: Silero VAD for speech detection

**Alternatives Considered**:
- **WebRTC VAD**: A widely used, high-quality VAD, but Silero is often considered slightly more accurate and is very easy to integrate in Python projects.
- **Simple energy-based VAD**: The simplest method (checking audio volume), but highly prone to errors from background noise.

**Why Silero**:
- **Accuracy**: Highly accurate and robust against background noise.
- **Lightweight**: Runs efficiently on the CPU with minimal overhead.
- **Easy Integration**: Well-supported within the Pipecat framework.

**Parameters**:
- **min_silence_ms**: `200`. A short delay to ensure the user has finished their thought, making the AI feel less like it's interrupting while keeping the conversation flowing.
- **speech_pad_ms**: `120`. Keeps a small buffer of audio before speech starts, which can improve the ASR model's accuracy on initial words.
- **window_ms**: `160`. A standard window size for analyzing audio frames.

## Infrastructure Decisions

### Docker Deployment
**Chosen**: Docker containerization

**Alternatives Considered**:
- **Bare metal**: Running directly on the server lacks the reproducibility and dependency isolation that Docker provides, making setup and maintenance more difficult.
- **Kubernetes**: While powerful for scaling, K8s adds significant complexity and is overkill for a single-instance deployment.

**Why Docker**:
- **Reproducibility**: Guarantees a consistent environment across development and deployment.
- **GPU Support**: Mature and easy integration with NVIDIA GPUs via the NVIDIA Container Toolkit.
- **Dependency Management**: Isolates all Python and system dependencies, which was critical for solving the `onnxruntime` conflicts.

### WebSocket Transport
**Chosen**: WebSocket for real-time communication

**Alternatives Considered**:
- **gRPC**: Excellent for high-performance, bidirectional streaming between services, but lacks native browser support, requiring a proxy layer.
- **WebRTC**: The gold standard for peer-to-peer communication, but its complexity is unnecessary for a client-server architecture where all processing happens on the server.

**Why WebSocket**:
- **Bidirectional**: The ideal protocol for streaming audio from client to server and server to client simultaneously.
- **Native Browser Support**: Works out-of-the-box in all modern web browsers.
- **Simplicity**: Easier to set up and manage than a full WebRTC stack.

## Performance Trade-offs

### Latency vs Quality
- **ASR**: Using `distil-medium-en` is faster than `large-v3`. We accept a minor decrease in accuracy on very niche vocabulary for a major gain in speed.
- **LLM**: The `8B` model provides a good balance. A `70B` model would offer more nuanced responses but would increase latency and VRAM requirements beyond our hardware target. A smaller `3B` model like Phi-3 would be faster but might lack the reasoning ability for effective coaching.
- **TTS**: Kokoro provides a high-quality voice. A simpler TTS like Piper would be faster and run on CPU, but the voice quality is noticeably more robotic, which detracts from the realism of a coaching avatar.

### Resource Usage vs Performance
- **GPU memory**: The pipeline is optimized to run with **~12GB of VRAM**, making it accessible on consumer-grade cards like the NVIDIA L4/A10. This was a key decision factor over the more resource-intensive Ultravox pipeline (~20GB).
- **CPU usage**: Kept minimal by offloading all major AI models to the GPU.
- **Memory**: 16GB of system RAM is sufficient.

### Cost vs Performance
- **Cost of Self-Hosting**: The primary cost is the on-demand GPU rental from a service like Runpod. By optimizing for lower VRAM, we can use cheaper, more available GPUs.
- **Model size**: Choosing the `8B` LLM and `distil-medium-en` ASR model provides the best performance-per-watt and performance-per-dollar for this use case.

## Future Considerations

### Model Upgrades
- **STT**: [TO BE ADDED] - When to upgrade to Whisper v3 or newer models?
- **LLM**: [TO BE ADDED] - When to upgrade to Llama 3.2 or other models?
- **TTS**: [TO BE ADDED] - What's the roadmap for Kokoro improvements?

### Architecture Evolution
- **Scaling**: [TO BE ADDED] - How to handle multiple concurrent users?
- **Edge deployment**: [TO BE ADDED] - How to deploy on edge devices?
- **Hybrid cloud**: [TO BE ADDED] - When to use cloud vs local processing?

---

**Next**: Read [Performance](./4_performance.md) for detailed latency analysis and benchmarks. 