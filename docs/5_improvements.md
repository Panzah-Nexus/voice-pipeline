# 5. Improvements & Enhancements

Based on the project's journey, the following are potential improvements, categorized by effort and impact, to better serve the goal of creating a real-time coaching avatar.

## Immediate Optimizations (Low Effort, High Impact)

### 1. Refine Interruption Handling
- **Problem**: The initial Ultravox prototype sometimes fed unspoken (interrupted) tokens into the conversation history. This could still be a subtle issue.
- **Goal**: Ensure that when a user interrupts the AI, only the audio generated *before* the interruption is saved to context.
- **Benefit**: More accurate conversation history and more coherent follow-up responses from the LLM.

### 2. Advanced VAD Parameter Tuning
- **Current**: The VAD settings are tuned for general responsiveness.
- **Goal**: Fine-tune the VAD to be more aggressive in detecting the end of speech. For role-playing, a slightly shorter silence threshold could make the AI feel more eager to respond.
- **Benefit**: Reduce "dead air" and make the conversation feel more natural and fast-paced.

### 3. Quantize ASR and TTS Models
- **Current**: The LLM is quantized, but the ASR and TTS models are likely running at full precision.
- **Goal**: Explore `int8` quantization for Faster Whisper and Kokoro models.
- **Benefit**: Further reduce VRAM usage below the current ~12GB, potentially enabling larger LLMs or more concurrent pipelines on the same hardware.

## Medium-Term Enhancements

### 1. Implement Mid-Chat Prompt Changing
- **Goal**: A key requirement for a coaching avatar is the ability for a "coach" to change the scenario mid-conversation (e.g., "now the customer is angry").
- **Implementation**: Create a mechanism (like a special WebSocket message or a separate endpoint) to dynamically update the system prompt used by the LLM without restarting the pipeline.
- **Benefit**: Unlocks the core use case of real-time, adaptive role-playing.

### 2. Explore LLM Tool Calling
- **Goal**: Allow the LLM to use "tools" to enhance its coaching capabilities.
- **Examples**:
  - `get_user_performance`: A tool that could retrieve metrics on the trainee's speech pace, use of filler words, etc.
  - `lookup_product_info`: In a sales roleplay, the AI could look up product details it doesn't know.
- **Benefit**: Creates a much more dynamic and intelligent coaching agent that can provide data-driven feedback.

### 3. Integrate a Native Kokoro Service
- **Current**: Kokoro TTS runs in an isolated subprocess to avoid dependency conflicts, which introduces slight IPC overhead.
- **Goal**: Investigate resolving the `onnxruntime-gpu` dependency conflicts directly. This might involve creating a custom Docker image with specific library versions or contributing a fix upstream.
- **Benefit**: Simplifies the architecture and removes potential latency from inter-process communication.

## Long-Term Vision

### 1. Re-evaluate End-to-End Models
- **Context**: The project began by exploring Ultravox but found it immature. The open-source voice AI space moves incredibly fast.
- **Goal**: Periodically re-evaluate the landscape for high-performance, end-to-end models that provide the necessary features (context, tool-calling).
- **Benefit**: A mature end-to-end model could drastically simplify the pipeline and reduce latency even further.

### 2. Multi-Modal Coaching Analysis
- **Goal**: Enhance the coaching avatar by allowing it to analyze more than just audio.
- **Implementation**: Integrate video processing to analyze a trainee's facial expressions, eye contact, and body language during roleplay.
- **Benefit**: Provides a holistic performance review for trainees, a feature that would set this tool apart.

### 3. Fine-Tune a Domain-Specific LLM
- **Goal**: Move beyond a general-purpose model like Llama 3.1 and fine-tune a model specifically for coaching conversations.
- **Implementation**: Create a dataset of ideal sales/customer service conversations and use it to fine-tune a smaller, faster model (like Phi-3 or Mistral 7B).
- **Benefit**: A specialized model would provide more relevant, higher-quality responses and could be smaller and faster than the general-purpose 8B model.

## Implementation Roadmap

### Phase 1: Core Coaching Features (1-2 months)
1. **Implement Mid-Chat Prompt Changing**: This is the highest priority for the core use case.
2. **Refine Interruption Handling**: Ensure conversation context is always clean.
3. **Explore ASR/TTS Quantization**: Quickest win for VRAM reduction.

### Phase 2: Advanced Interaction (3-6 months)
1. **Implement Tool Calling**: Start with a simple tool for performance metrics.
2. **Fine-Tune a Small LLM**: Begin creating a dataset for a specialized coaching model.
3. **Investigate Native Kokoro Service**: Tackle the dependency challenge to simplify the architecture.

---
**Next**: Review [Configuration](./6_configuration.md) for current settings. 