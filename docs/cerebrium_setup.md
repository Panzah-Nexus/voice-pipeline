# Running on Cerebrium

This guide walks through creating a Cerebrium account and deploying the voice pipeline so you can talk to it from your local machine.

## 1. Sign up
1. Visit <https://www.cerebrium.ai> and click **Get started**.
2. Create an account with your email and password.
3. Verify the email sent by Cerebrium and log in.

## 2. Create a project
1. After logging in, choose **Create project** from the dashboard.
2. Pick a name and select an NVIDIA GPU such as the **A10**.
3. Continue to create the project. Cerebrium will provision a GPU instance for you.

## 3. Build your Docker image
Run these commands on your local machine (or Cloud shell):
```bash
cd docker
docker build -t voice-pipeline .
docker tag voice-pipeline YOUR_DOCKERHUB_USERNAME/voice-pipeline:latest
docker push YOUR_DOCKERHUB_USERNAME/voice-pipeline:latest
```
Replace `YOUR_DOCKERHUB_USERNAME` with your Docker Hub account name.

## 4. Deploy on Cerebrium
1. In your new project, click **Deploy Container** and enter the Docker image you pushed.
2. Add environment variables (`HUGGING_FACE_TOKEN`, `PIPER_BASE_URL`, etc.).
3. Expose port **8000** so the WebSocket server can be reached.
4. Click **Deploy** and wait for the container status to become **Running**. Take note of the public URL shown by Cerebrium.

## 5. Connect from your computer
On your local machine install the requirements and run the client:
```bash
pip install -r requirments.txt
WS_SERVER=wss://PUBLIC_CEREBRIUM_URL:8000 python -m src.websocket_client
```
Use the public URL from step 4 in place of `PUBLIC_CEREBRIUM_URL`.
The microphone audio will stream to the remote GPU and the response will play back through your speakers.
