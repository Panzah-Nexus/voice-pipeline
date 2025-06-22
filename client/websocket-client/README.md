# JavaScript Voice Client

A basic web client for the voice pipeline, built with TypeScript and Vite, using the [Pipecat JavaScript SDK](https://docs.pipecat.ai/client/js/introduction).

## Setup & Configuration

1.  **Get the Server URL**: First, ensure your main voice pipeline server is deployed and running on RunPod. Follow the main [Deployment Guide](../../docs/deployment_guide.md) to get the **base HTTP URL** for your running pod (e.g., `https://<pod-id>-8000.proxy.runpod.net/`).

2.  **Configure the Client**:
    -   Navigate to this directory (`client/websocket-client`).
    -   Create a `.env` file by copying the example: `cp .env.example .env`.
    -   Open the new `.env` file and paste the **base HTTP URL** you obtained from your pod as the value for `VITE_WS_URL`. The client will handle the rest.

3.  **Install Dependencies**:
    ```bash
    npm install
    ```

## Running the Client

1.  **Start the Dev Server**:
    ```bash
    npm run dev
    ```
    **Note**: If you change the `VITE_WS_URL` in the `.env` file, you must stop (`Ctrl+C`) and restart the dev server for the change to take effect.

2.  **Open in Browser**: Visit `http://localhost:5173` in your browser.

3.  **Connect**: Click the "Connect" button to establish a connection with the voice pipeline server.
