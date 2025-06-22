# Voice Pipeline Deployment Guide for RunPod

This guide provides a complete walkthrough for deploying the air-gapped voice pipeline on **RunPod**, covering both production and development workflows.

## 🎯 Overview

-   **Local Device (Your Computer)**: Runs a web-based client to interact with the pipeline.
-   **RunPod (NVIDIA L4 GPU)**: Hosts the AI pipeline in a Docker container, performing all heavy AI processing.
-   **Air-Gapped Operation**: Once deployed, no external API calls are made for the core AI processing.

## 📋 Prerequisites

-   A [RunPod](https://www.runpod.io/) account with billing set up.
-   A [Hugging Face](https://huggingface.co/) account with a Read token.
-   Basic familiarity with Docker concepts.
-   Node.js and `npm` installed on your local machine for the web client.
-   A microphone and speakers connected to your local machine.

## Phase 1: Deploy Pod on RunPod

### 1.1 Choose a Template
This project uses custom Docker images. You will deploy a pod using one of these templates.

1.  From the RunPod dashboard, navigate to **Templates** → **New Template**.
2.  Give the template a name (e.g., `voice-pipeline-prod`).
3.  For the **Container Image**, enter the name of the production image:
    `mlbra2006/voice-pipeline-airgapped:uvfix`
    *(Note: If this image is private, you will need to configure your RunPod account with credentials to pull from your container registry.)*
4.  Set the **Container Disk** to at least **40 GB**.
5.  Click **Save Template**.

### 1.2 Configure and Deploy the Pod
1.  Navigate to **Secure Cloud** or **Community Cloud** to deploy a new pod.
2.  Select the desired **NVIDIA L4** GPU.
3.  Under "Choose a Template," select the template you just created.
4.  **Expose TCP Ports**: Set the port mappings.
    -   Map public port `8000` to container port `8000` (for the web server).
    -   Map a public port (e.g., `2222`) to container port `22` (for SSH access in development).
5.  **Set Environment Variables**:
    -   `HF_TOKEN`: Your Hugging Face `Read` token for model downloads.
    -   You can also override defaults here, e.g., by setting `KOKORO_VOICE_ID`.
6.  Click **"Deploy"** and wait for the pod to initialize. The first launch will take several minutes to download the large Ultravox model.

## Phase 2: Configure and Run the Client

### 2.1 Get Your Pod's URL
1.  Once your pod is running, find the public HTTP address for port `8000` in the "My Pods" dashboard. This URL is **ephemeral** and will change every time you create a new pod.
    -   An example URL looks like this: `https://kkqc33rcg7qmwf-8000.proxy.runpod.net/`
2.  Copy this base HTTP URL. This is the only URL you need for the client configuration. The client will automatically handle appending `/connect` and deriving the WebSocket address.

### 2.2 Configure the Client
1.  Navigate to the web client directory on your local machine: `cd client/websocket-client`.
2.  If it doesn't exist, create a `.env` file from the example: `cp .env.example .env`.
3.  Open the `.env` file and paste the **base HTTP URL** you copied as the value for `VITE_WS_URL`.

### 2.3 Run the Client
1.  Install dependencies (only needed the first time): `npm install`.
2.  Run the client's development server: `npm run dev`.
3.  Open `http://localhost:5173` in your browser to start a conversation.

**IMPORTANT:** If you change the `VITE_WS_URL` in the `.env` file while the client is running, you must **stop the Vite server (`Ctrl+C`) and restart it (`npm run dev`)** for the change to take effect. The server only reads the `.env` file on startup.

---

## 🚀 Development & Fast Iteration Workflow

For active development, resetting a container is extraordinarily slow due to re-downloading the large models. The fastest way to iterate is to use the development Docker image and a git-based workflow.

### Step 1: Use the Development Template
Create a new RunPod template using the development image:
`mlbra2006/voice-pipeline-airgapped:dev`

This image contains a startup script that clones or pulls the latest code from your GitHub repository before running the application.

### Step 2: Set Development Environment Variables
When you deploy a pod with the `:dev` template, you **must** set these additional environment variables:
-   `GIT_USER`: Your GitHub username.
-   `GIT_REPO`: Your GitHub repository name (e.g., `voice-pipeline`).
-   `GIT_TOKEN`: A GitHub Personal Access Token with repository read access.

The `dev_start.sh` script (from `docker/Dockerfile.dev`) uses these to construct the git clone URL.

### Step 3: The Iteration Loop
1.  Push your code changes to your GitHub repository (the script is configured to pull from the `tts-test` branch by default).
2.  **Restart** (do not terminate) your running RunPod pod.
3.  Upon restarting, the script will automatically `git pull` your latest changes before launching the Python server.

### Important Notes on Container Management
-   **Restarting vs. Resetting**:
    -   **Restarting** is fast and is the key to the git-based workflow.
    -   **Resetting** or **Terminating** a pod is very slow, as it forces a complete re-download of the container image and models. Avoid this for small changes.
-   **Changing Branches**: The branch name is currently hardcoded in `docker/Dockerfile.dev`. To work on a different branch, you must edit the Dockerfile, rebuild the `:dev` image, push it to your registry, and then reset your pod with the new image.
-   **Production Image**: Restarting a pod with the production (`:uvfix`) image will **not** pull new changes. It will always use the cached, baked-in version of the code.
-   **Volumes**: Mounting a volume for source code could be an alternative, but as you noted, it costs more and has not been tested.

### A Word of Caution: Updating Dependencies
The git-based workflow is excellent for iterating on Python code, but it is **not** designed for changing dependencies (i.e., modifying `requirements.txt`). Updating dependencies is a slow, manual, and painful process. Be extremely careful when considering a dependency change.

The process involves:
1.  **Modify `docker/Dockerfile`**: Add your new system or Python dependencies.
2.  **Build New Base Image**: Build the production Dockerfile locally. This will be a long, non-cached build.
    ```bash
    docker build -f docker/Dockerfile -t your-registry/image-name:new-tag .
    ```
3.  **Push New Base Image**: Push the very large (~5-10 GB) base image to your Docker registry. This can take over 10 minutes.
4.  **Update `Dockerfile.dev`**: Change the `FROM` instruction in `docker/Dockerfile.dev` to point to your new base image tag.
5.  **Build and Push Dev Image**: Build and push the (much smaller) dev image.
6.  **Terminate the Pod**: You must **terminate** (not just restart) your old dev pod on RunPod.
7.  **Deploy New Pod**: Launch a new pod using your updated dev template. This startup can take another 10-15 minutes as it pulls the new base image for the first time.

This entire process can take **30-45 minutes** or more. It is, as you noted, "literal hell for progress," so dependency changes should be planned carefully and avoided when possible.

## Phase 3: Monitoring and Management

-   **Viewing Logs**: Use the **Logs** tab in the RunPod pod view to see real-time application output. This is essential for debugging.
-   **Stopping and Restarting**: Use the controls in the RunPod UI to manage your pod. Stopping the pod will incur minimal storage costs, while terminating it is permanent.
-   **Daily Workflow**: Start your pod, update the `.env` file with the latest WebSocket URL, run the client with `npm run dev`, and stop the pod when you're finished to save costs. 