# 1. Quick Start

This guide explains how to build and run the Voice Pipeline using Docker for both local development and deployment on a RunPod cloud GPU instance.

## Prerequisites


*   **Docker:** Ensure Docker is installed and the Docker daemon is running.
*   **NVIDIA GPU:** A local or cloud-based NVIDIA GPU with CUDA drivers installed is required for hardware acceleration for cuda 12.x and cudnn 9.
*   **Git:** For cloning the repository.
*   **Ollama:** Make sure you have Ollama running with the `llama3-8b` model pulled.
*   **Assets(kokoro files)** https://github.com/thewh1teagle/kokoro-onnx/releases (kokoro-v1.0.onnx and voices-v1.0.bin) which you then create an assets dir.

## Local Development & Testing

### 1. Clone the Repository

```bash
git clone https://github.com/Panzah-Nexus/voice-pipeline/
cd voice-pipeline
```

### 2. Configure Environment Variables

Create a `.env` file in the project root by copying the example file:

```bash
cp .env.example .env
```

Review the `.env` file and ensure the variables are set correctly for your local environment. At a minimum, you will likely need to configure `OLLAMA_BASE_URL`.


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

## Running the client
Follow the instructions in this [README](..\client\websocket-client\README.md) 