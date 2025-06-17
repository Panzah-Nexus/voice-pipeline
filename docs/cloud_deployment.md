# Cloud Deployment (Cerebrium)

This document summarizes the steps for running the pipeline on Cerebrium. The instructions are adapted from Cerebrium's tutorial on deploying Ultravox.

1. **Install cerebrium CLI**
   ```bash
   pip install --upgrade cerebrium
   cerebrium login
   ```
2. **Initialize a new project**
   ```bash
   cerebrium init voice-ultravox
   ```
   This generates a `cerebrium.toml` and example `main.py`.
3. **Create `.env` with required secrets**
   ```text
   DAILY_TOKEN=<YOUR_DAILY_TOKEN>
   CARTESIA_API_KEY=<YOUR_CARTESIA_API_KEY>
   HF_TOKEN=<YOUR_HUGGINGFACE_TOKEN>
   ```
   Upload these secrets to the Cerebrium dashboard.
4. **Configure `cerebrium.toml`** using the A10 GPU:
   ```toml
   [cerebrium.deployment]
   name = "voice-ultravox"
   python_version = "3.11"
   docker_base_image_url = "debian:bookworm-slim"

   [cerebrium.runtime.custom]
   port = 8765
   entrypoint = ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8765"]
   healthcheck_endpoint = "/health"

   [cerebrium.hardware]
   cpu = 4
   memory = 16.0
   compute = "AMPERE_A10"

   [cerebrium.scaling]
   min_replicas = 0
   max_replicas = 5
   cooldown = 90
   replica_concurrency = 1
   scaling_metric = "concurrency_utilization"
   scaling_target = 80
   scaling_buffer = 1

   [cerebrium.dependencies.pip]
   "pipecat-ai[cartesia,daily,silero,ultravox]" = "0.0.62"
   fastapi = "latest"
   uvicorn = "latest"
   ```
5. **Deploy**
   ```bash
   cerebrium deploy
   ```
   The first deploy downloads the Ultravox model. Subsequent deploys are faster.

Once deployed, create a Daily room and POST to your `/run` endpoint with the room URL and token to start the pipeline as described in the Cerebrium blog.
