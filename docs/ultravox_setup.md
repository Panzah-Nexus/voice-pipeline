# Ultravox Setup

This page collects notes on running Ultravox locally and remotely.

## Installation

Inside your Docker image install Pipecat with the Ultravox extras:

```bash
pip install pipecat-ai[ultravox] websockets sounddevice
```

The service needs a Hugging Face token with access to the Ultravox models.
Set `HUGGING_FACE_TOKEN` in the environment.

## Pipeline Snippet

```python
from pipecat import Pipeline
from pipecat.services.ultravox import UltravoxSTTService

stt = UltravoxSTTService(
    model_size="1b",
    hf_token=os.environ.get("HUGGING_FACE_TOKEN"),
    temperature=0.5,
    max_tokens=150,
)

pipeline = Pipeline(stt)
```

## Cloud Deployment

Follow Cerebrium's guide for deploying Ultravox containers:
<https://www.cerebrium.ai/blog/deploying-ultravox-on-cerebrium>
Use the same Dockerfile as provided here and expose the websocket port when
running the container.

