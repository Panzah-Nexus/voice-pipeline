# Hardware Guide

This guide provides recommendations and comparisons for the GPU hardware used to run the voice pipeline. While the documentation is standardized on the **NVIDIA L4**, the pipeline is flexible and can be deployed on other GPUs.

## Recommended GPU: NVIDIA L4

The NVIDIA L4 is the recommended GPU for this pipeline when deploying on public clouds like RunPod.

-   **Architecture**: Ada Lovelace
-   **VRAM**: 24 GB GDDR6
-   **Performance**: Excellent performance-per-watt, making it highly efficient for inference workloads like this one. It can easily handle the 8B Ultravox model and Kokoro TTS with very low latency.
-   **Cost-Effectiveness**: The L4 typically offers one of the best price-to-performance ratios for modern inference tasks, making it an ideal choice for development, testing, and production use.

## On-Premises Target: NVIDIA A10

For the final on-premises, air-gapped deployment, the NVIDIA A10 is a strong and previously targeted candidate.

-   **Architecture**: Ampere
-   **VRAM**: 24 GB GDDR6
-   **Performance**: The A10 is a very capable GPU for AI inference. While the L4 is newer and more efficient, the A10 delivers more than enough performance to run this pipeline with low latency. It can comfortably run the 8B model.
-   **Availability**: It is a widely available and mature data center GPU.

**Comparison: L4 vs. A10**
-   The **L4** is more power-efficient and has a more advanced architecture, which can result in slightly lower latency for inference tasks.
-   The **A10** is a proven, reliable workhorse. Performance differences for this specific pipeline are likely to be minor.
-   **Conclusion**: Both are excellent choices. If deploying today on the cloud, the L4 is preferred. For an existing or planned on-premises deployment, the A10 is perfectly suitable.

## High-End Option: NVIDIA L40

You initially mentioned the L40 by mistake, but it's worth noting as a high-end alternative for scenarios requiring massive throughput.

-   **Architecture**: Ada Lovelace
-   **VRAM**: 48 GB GDDR6
-   **Performance**: The L40 is a powerhouse. Its primary benefit is not just lower latency for a single user, but the ability to handle many concurrent users or run much larger models (e.g., 70B parameter models) without running out of VRAM.
-   **Use Case**: Overkill for a single-user pipeline with an 8B model, but would be the right choice for a large-scale, multi-user deployment where you need to serve dozens of simultaneous conversations from a single server.

## Summary

| GPU         | VRAM  | Architecture | Ideal Use Case                                                                |
| :---------- | :---- | :----------- | :---------------------------------------------------------------------------- |
| **NVIDIA L4** | 24 GB | Ada Lovelace | **Recommended**: Best price/performance for cloud-based development and production. |
| **NVIDIA A10** | 24 GB | Ampere       | **On-Premises**: Excellent choice for a dedicated, local air-gapped server.     |
| **NVIDIA L40** | 48 GB | Ada Lovelace | **High-Scale**: Best for supporting many concurrent users or much larger models. |

The pipeline is designed to be portable. As long as the target machine has a compatible NVIDIA GPU with CUDA drivers and at least 24 GB of VRAM, the same Docker container can be deployed with no code changes. 