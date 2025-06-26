# 1. Quick Start

This guide explains how to build and run the Voice Pipeline using Docker for both local development and deployment on a RunPod cloud GPU instance.

## Prerequisites

*   **Docker:** Ensure Docker is installed and the Docker daemon is running.
*   **NVIDIA GPU:** A local or cloud-based NVIDIA GPU with CUDA drivers installed is required for hardware acceleration.
*   **Git:** For cloning the repository.
*   **Ollama:** Make sure you have Ollama running with the `llama3-8b` model pulled.

## Local Development & Testing

Running the pipeline locally is the fastest way to test changes. The provided Docker development environment mounts the local source code, so changes are reflected without rebuilding the image.

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/voice-pipeline.git
cd voice-pipeline
```

### 2. Configure Environment Variables

Create a `.env` file in the project root by copying the example file:

```bash
cp .env.example .env
```

Review the `.env` file and ensure the variables are set correctly for your local environment. At a minimum, you will likely need to configure `OLLAMA_BASE_URL`.

### 3. Build the Development Docker Image

The `Dockerfile.dev` image contains all dependencies but keeps your local source code mounted for live updates.

```bash
docker build -t voice-pipeline:dev -f docker/Dockerfile.dev .
```

### 4. Run the Docker Container

Run the container, mounting the `src` directory and exposing the necessary ports.

```bash
docker run -it --rm \
  --gpus all \
  -v ./src:/app/src \
  -p 8000:8000 \
  --env-file .env \
  voice-pipeline:dev
```

> **💡 Tip:** The `--gpus all` flag enables NVIDIA GPU access within the container. You may need to install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

## Production Deployment (RunPod)

For a production-like environment, you can deploy the pipeline on a RunPod NVIDIA L4 GPU instance. This involves building a production-ready Docker image and running it on the pod.

### 1. Build the Production Image

This command builds the final image using the production `Dockerfile`.

```bash
docker build -t voice-pipeline:latest -f docker/Dockerfile .
```

### 2. (Optional) Push the Image to a Registry

To make the image accessible to your RunPod instance, you can push it to a container registry like Docker Hub, GCR, or AWS ECR.

```bash
docker tag voice-pipeline:latest your-registry/voice-pipeline:latest
docker push your-registry/voice-pipeline:latest
```

### 3. Run on a RunPod L4 Instance

When configuring your RunPod pod:
1.  Select an **NVIDIA L4** GPU.
2.  Set the Docker image to the one you just built (e.g., `your-registry/voice-pipeline:latest`). If you didn't push to a registry, you can set up a private registry or load the image directly onto the pod.
3.  Expose TCP port `8000`.
4.  Configure the environment variables from your `.env` file in the RunPod template settings.

Once the pod is running, the voice pipeline will be accessible via the pod's public endpoint on port `8000`. 