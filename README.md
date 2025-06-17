# Voice Pipeline

This repository contains a basic framework for building a voice AI pipeline with
[Pipecat](https://github.com/spidercat/piepecat) and compatible Docker images.
The goal is to develop and test the pipeline on cloud compute (e.g. Cerebrium)
and then run the same code locally on an NVIDIA A10 GPU with minimal changes.

## Features

- **Dockerized Environment**: Scripts for building and running Docker containers that include the necessary dependencies.
- **Streaming via WebSockets**: Simple client/server example for routing microphone audio to the remote inference machine and returning synthesized speech back to local speakers.
- **Pipecat Integration**: Skeleton code for setting up Pipecat with the smallest available Ultravox model from Hugging Face.
- **TTS Service**: Example local service using [ultravox](https://github.com/rhasspy/ultravox) weights.

For full design details see [docs/pipeline_design.md](docs/pipeline_design.md).
See [docs/ultravox_setup.md](docs/ultravox_setup.md) for instructions on running
the Ultravox services.

## Quick Start

```bash
# Build the docker image
cd docker && docker build -t voice-pipeline .

# Run the container (replace device mapping if using GPU)
docker run --gpus all -p 8000:8000 -it voice-pipeline
```

## Directory Structure

- `src/` – Python modules for the pipeline
- `docker/` – Dockerfile and configuration scripts
- `docs/` – Additional documentation

## Requirements

- Docker 20.10+
- Python 3.10+
- PyTorch with CUDA (for GPU)
- [Pipecat-AI](https://pypi.org/project/pipecat-ai/) with the `ultravox` extra
  installed (see Dockerfile)
- [Ultravox](https://github.com/rhasspy/ultravox) models from Hugging Face
  (you'll need a `HUGGING_FACE_TOKEN` environment variable)

## Usage

1. Record your microphone audio using `websocket_client.py`.
2. Audio is sent to `pipecat_pipeline.py` running remotely inside the Docker
   container (e.g. on Cerebrium).
3. The pipeline runs STT via `UltravoxSTTService`, your chosen language model,
   and a TTS engine.
4. The audio is streamed back to your machine and played through your speakers.

## Notes

This repository only includes minimal skeleton code and documentation. You will
need to fill in the details for STT, LM, and TTS models. When testing on
Cerebrium (or another cloud GPU), run the Docker container and expose the
websocket port. The local `websocket_client.py` connects to that port to send
microphone audio and play back responses.

