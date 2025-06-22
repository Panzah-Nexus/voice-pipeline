# Voice Pipeline Deployment Guide for RunPod

This guide provides a complete walkthrough for deploying the air-gapped voice AI pipeline on **RunPod** using an **NVIDIA L4 GPU** and connecting it to your local machine.

## 🎯 Overview

-   **Local Device (Your Computer)**: Runs a web-based client to capture microphone audio, send it via a WebSocket, and play the AI's spoken response.
-   **RunPod (L4 GPU)**: Hosts the AI pipeline in a Docker container. It runs the WebSocket server, processes audio with `UltravoxWithContextService`, generates speech with `KokoroTTSService`, and streams the audio response back to your client.
-   **Air-Gapped Operation**: Once deployed, no external API calls are made for the core AI processing.

## 📋 Prerequisites

-   A [RunPod](https://www.runpod.io/) account with billing set up.
-   A [Hugging Face](https://huggingface.co/) account with a Read token.
-   Basic familiarity with Docker concepts.
-   Node.js and `npm` installed on your local machine for the web client.
-   A microphone and speakers connected to your local machine.

## Phase 1: Deploy on RunPod

### 1.1 Choose a Template
1.  Navigate to **Secure Cloud** or **Community Cloud** in RunPod to deploy a new pod.
2.  Select the desired **NVIDIA L4** GPU.
3.  For the template, choose **"RunPod Pytorch 2.2"** or a similar official PyTorch template. This provides the necessary CUDA drivers and Python environment.

### 1.2 Configure the Pod
1.  **Customize Deployment**: Set your desired container and volume disk sizes. A 20 GB container disk and 50 GB volume disk is a safe starting point.
2.  **Set Environment Variables**: This is a critical step.
    -   Click **"Add Environment Variable"**.
    -   Create a variable named `HF_TOKEN` and paste your Hugging Face token as the value.
    -   You can also override defaults by adding `KOKORO_VOICE_ID`.
3.  **Set Start Command**:
    -   In the "Docker Command" or "Run Command" field, enter: `python src/main.py`
4.  **Expose Ports**:
    -   The application runs on port `8000`. RunPod automatically maps this to a public-facing TCP port. No manual configuration is needed.

### 1.3 Deploy and Verify
1.  Click **"Deploy"** and wait for the pod to initialize.
2.  Once running, check the **Logs**. The first launch will take several minutes to download the Ultravox model.
3.  Look for a log message like `Starting voice pipeline server on 0.0.0.0:8000`.

## Phase 2: Local Client Setup

### 2.1 Get Your WebSocket URL
The application running on your RunPod pod exposes a `/connect` endpoint to help you determine the correct WebSocket URL.

1.  In the RunPod UI for your pod, find the **HTTP port `8000`** and click the corresponding link to open the public URL. It will look like `https://<your-pod-id>-8000.proxy.runpod.net/`.
2.  Navigate to the `/connect` endpoint in your browser: `https://<your-pod-id>-8000.proxy.runpod.net/connect`.
3.  This will return a JSON object containing the `ws_url`. Copy this URL.

### 2.2 Configure the Client
1.  Navigate to the web client directory: `cd client/websocket-client`.
2.  If it doesn't exist, create a `.env` file by copying the example: `cp .env.example .env`.
3.  Open the `.env` file and paste the `ws_url` you copied as the value for `VITE_WS_URL`.

### 2.3 Run the Client
1.  Install the dependencies: `npm install`.
2.  Run the client's development server: `npm run dev`.
3.  Open `http://localhost:5173` in your browser to start a conversation.

## Phase 3: Monitoring and Management

-   **Viewing Logs**: Use the **Logs** tab in the RunPod pod view to see real-time application output. This is essential for debugging.
-   **Stopping and Restarting**: Use the controls in the RunPod UI to manage your pod. Stopping the pod will incur minimal storage costs, while terminating it is permanent.
-   **Daily Workflow**: Start your pod, update the `.env` file with the latest WebSocket URL, run the client with `npm run dev`, and stop the pod when you're finished to save costs. 