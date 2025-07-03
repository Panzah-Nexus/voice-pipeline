# 4. Performance Analysis

## Latency Breakdown

The most critical metric for a real-time coaching avatar is the "end of speech to start of speech" latency. The target is to keep this as low as possible to feel like a natural conversation.

**End-to-End Latency**: **~1100ms** (1.1s)
*This is the measured time from when the user stops speaking to when the AI's voice is first heard on the client side, including network latency.*

```mermaid
sequenceDiagram
    participant Client (UK)
    participant Server (France)
    
    Client->>Server: User Finishes Speaking (t=0ms)
    Note right of Client: Final audio chunk travels (~40ms)
    
    subgraph Server Processing
        Note over Server: VAD waits for 200ms silence (t=240ms)
        Note over Server: ASR transcribes text (~350ms) (t=590ms)
        Note over Server: LLM generates first token (~200ms) (t=790ms)
        Note over Server: TTS generates first audio (~200ms) (t=990ms)
    end
    
    Server-->>Client: First Audio Chunk
    Note left of Server: Audio chunk travels (~40ms)

    Note over Client: Audio Heard by User (t~1100ms)
```

### Component Latency Estimates
- **VAD (Voice Activity Detection)**: The processing itself is fast (`<20ms`), but it waits for **200ms** of silence (`min_silence_ms`) on the server before triggering. This is the largest fixed application delay.
- **ASR (Faster Whisper)**: **~350ms** for an average 3-4 second utterance.
- **LLM (Llama 3.1 8B)**: **~200ms** time-to-first-token (TTFT).
- **TTS (Kokoro)**: **~200ms** time-to-first-audio (TTFA).
- **Network Latency**: **~80ms** total. This accounts for two one-way trips over the internet between the UK client and France server (the final user audio chunk traveling to the server, and the first AI audio chunk returning to the client).
- **Internal Overhead**: **~70ms** for internal Pipecat processing, WebSocket framing, and client-side audio buffering.

## Resource Utilization

These metrics are based on the final cascading pipeline running on an NVIDIA L4 GPU.

### GPU Requirements
- **Minimum VRAM**: 12 GB
- **Recommended VRAM**: 16 GB (to allow for larger models or context windows)
- **Peak Usage**: ~12.5 GB
- **Sustained Usage**: ~12 GB

### CPU & Memory Requirements
- **Recommended Cores**: 4 Cores
- **Recommended RAM**: 16 GB

## Performance Benchmarks

### Latency Comparison
| Component | Current (Estimate) | Target |
|-----------|--------------------|--------|
| VAD Silence Wait | 200 ms | 150 ms |
| ASR Processing | 350 ms | <300 ms |
| LLM TTFT | 200 ms | <200 ms |
| TTS TTFA | 200 ms | <200 ms |
| **Total E2E** | **~1100 ms** | **<800 ms** |

### Quality vs. Speed Trade-offs
- **ASR**: Using `distil-medium-en` is much faster than `large-v3`. We accept a minor decrease in accuracy on very niche vocabulary for a major gain in speed.
- **LLM**: The `8B` model is fast. A `70B` model would provide more nuanced responses but would increase TTFT and VRAM requirements beyond our hardware target. A smaller `3B` model like Phi-3 would be faster but might lack the reasoning ability needed for good coaching.
- **TTS**: Kokoro provides high-quality voice. A simpler TTS like Piper would be faster and run on CPU, but the voice quality is noticeably more robotic, which detracts from the realism of a coaching avatar.

## Optimization Opportunities

### Current Bottlenecks
1.  **VAD Silence Period**: The fixed 200ms wait is the single largest, non-processing-related delay.
2.  **ASR Transcription**: At ~350ms, this is the most computationally expensive part of the latency chain.

### Potential Improvements
1.  **Model Quantization**: The LLM is already quantized. Applying `int8` quantization to the ASR and TTS models could reduce VRAM and potentially speed up inference.
2.  **ASR Model Size**: Experimenting with `distil-small-en` could dramatically reduce the ASR processing time, with a trade-off in accuracy. This may be acceptable for many coaching scenarios.
3.  **Speculative Decoding for LLM**: Could be implemented to reduce LLM latency further if it becomes a bottleneck.

## Scalability Analysis


### Multi-User Scaling
- **Concurrent users**: [TO BE ADDED] - How many users can be supported?
- **Resource scaling**: [TO BE ADDED] - How do resources scale with users?
- **Latency degradation**: [TO BE ADDED] - How does latency change with load?

## Monitoring and Metrics

### Key Performance Indicators (KPIs)
1. **End-to-end latency**: Target < 1000ms
2. **First word latency**: Target < 500ms
3. **Uptime**: Target > 99.9%
4. **Error rate**: Target < 1%

### Measurement Tools
- **Pipecat metrics**: [TO BE ADDED] - What metrics are available?
- **Custom timing**: [TO BE ADDED] - What custom measurements are needed?
- **Resource monitoring**: [TO BE ADDED] - How to monitor GPU/CPU/memory?

## Performance Testing

### Test Scenarios
1. **Cold start**: [TO BE ADDED] - How long does initial startup take?
2. **Warm start**: [TO BE ADDED] - How long does subsequent startup take?
3. **Long conversation**: [TO BE ADDED] - How does performance degrade over time?
4. **Interruptions**: [TO BE ADDED] - How does interruption affect performance?

### Benchmarking Tools
- **Load testing**: [TO BE ADDED] - What tools to use for load testing?
- **Latency measurement**: [TO BE ADDED] - How to measure precise latencies?
- **Resource profiling**: [TO BE ADDED] - How to profile resource usage?

## Cost Analysis

### Infrastructure Costs
- **GPU cost**: [TO BE ADDED] - What's the cost per hour of GPU usage?
- **Memory cost**: [TO BE ADDED] - What's the cost of additional memory?
- **Storage cost**: [TO BE ADDED] - What's the cost of model storage?

### Performance vs Cost Optimization
- **Model size vs cost**: [TO BE ADDED] - How does model size affect cost?
- **Quality vs cost**: [TO BE ADDED] - How does quality affect infrastructure cost?
- **Scaling vs cost**: [TO BE ADDED] - How does scaling affect cost?

## Recommendations

### Immediate Optimizations
1. **[TO BE ADDED]** - What's the quickest win for performance?
2. **[TO BE ADDED]** - What's the biggest impact change?
3. **[TO BE ADDED]** - What's the lowest effort improvement?

### Long-term Improvements
1. **[TO BE ADDED]** - What architectural changes would help?
2. **[TO BE ADDED]** - What model upgrades are planned?
3. **[TO BE ADDED]** - What infrastructure changes are needed?

---

**Next**: Read [Improvements](./5_improvements.md) for detailed enhancement proposals. 