# 5. Observability: Metrics and Tracing

The voice pipeline includes built-in observability features to help you monitor performance, debug issues, and understand the system's behavior. These features are powered by `pipecat`'s internal metrics and OpenTelemetry for distributed tracing.

## Pipecat Service Metrics

When enabled, `pipecat` services can collect and log key performance indicators (KPIs). This is especially useful for understanding the latency and resource usage of the STT and TTS services.

### Enabling Metrics

To enable service metrics, set the following environment variable:

```bash
ENABLE_METRICS=True
```

### Reading Metrics

With metrics enabled, the services will periodically log their performance data to the console. The two most important metrics for our pipeline are:

*   **Time-to-First-Byte (TTFB):**
    *   For STT, this measures the time from receiving the audio until the first transcription result is ready.
    *   For TTS, it measures the time from receiving the text until the first audio chunk is generated. This is a critical metric for conversational latency.
*   **Processing Time:**
    *   Measures the total time spent within a service processing a request. A high processing time can indicate a performance bottleneck.

## OpenTelemetry (OTLP) Tracing

For a more detailed, end-to-end view of a request as it flows through the pipeline, you can enable OpenTelemetry tracing. This will generate distributed traces that can be sent to a collector and visualized in a UI like Jaeger or Langfuse.

### Enabling Tracing

Set the following environment variable to enable the OTLP exporter:

```bash
ENABLE_TRACING=True
```

By default, this will configure an OTLP exporter to send traces to a local collector. You can customize the exporter endpoint and other settings via environment variables. See [6. Configuration](./6_configuration.md) for details.

### Running Jaeger for Visualization

Jaeger is a popular open-source tool for visualizing distributed traces. You can run a local Jaeger instance with Docker to inspect the traces from the pipeline.

```bash
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

Once the container is running, you can access the Jaeger UI at `http://localhost:16686`.

### Reading Traces

In the Jaeger UI, you can search for traces from the `voice-pipeline` service. A single trace will show a complete request-response cycle as a series of connected "spans."

*   **Parent Span:** Represents the entire conversation turn.
*   **Child Spans:** Detail the time spent in each service: VAD, STT, LLM, and TTS.

Analyzing the trace waterfall chart makes it easy to spot which part of the pipeline is contributing the most to the overall latency. For example, you can precisely measure the time from the end of the STT span to the beginning of the TTS span to understand the LLM's processing time. 