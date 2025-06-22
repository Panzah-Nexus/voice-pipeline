# Troubleshooting Guide for RunPod

This guide helps you diagnose and fix common issues with the voice pipeline deployed on RunPod.

## 🔍 Quick Diagnostics Checklist

Before diving deep, run through these quick checks:

1.  **Check Pod Status**: Is your pod running in the RunPod dashboard?
2.  **Check Pod Logs**: Open the **Logs** for your pod in RunPod. Are there any obvious errors like `ModuleNotFoundError`, `CUDA out of memory`, or tracebacks?
3.  **Verify WebSocket URL**: Does the `VITE_WS_URL` in your web client's `.env` file match the current URL from your pod's `/connect` endpoint? RunPod URLs can change if the pod restarts.
4.  **Test HTTP Endpoint**: Can you access the pod's public HTTP URL? Try opening `https://<your-pod-id>-8000.proxy.runpod.net/` in your browser. It should return a JSON response.

## 🚨 Common Issues & Solutions

### 1. Connection Refused / Timeout Error
You may see "Error: Connection failed" in the web client.

**Causes & Solutions:**

*   **Pod Not Ready**: The pod might still be starting, or the application inside it may have crashed.
    *   **Solution**: Check the pod's **Logs** in the RunPod UI. Look for `Uvicorn running on http://0.0.0.0:8000`. If you see errors before this, the server failed to start.

*   **Incorrect WebSocket URL**: The pod's public URL may have changed.
    *   **Solution**: Re-visit the `/connect` endpoint on your pod's HTTP URL to get the current `ws_url` and update the `VITE_WS_URL` in your client's `.env` file.

*   **Local Network/Firewall Issue**: Your local network, VPN, or firewall might be blocking the WSS connection.
    *   **Solution**: Try connecting from a different network or disabling your VPN temporarily.

### 2. AI Service Errors in Logs
You might see these errors in the RunPod pod logs:

```
❌ Failed to initialize Ultravox: 401 Client Error: Unauthorized for url
❌ RuntimeError: The `kokoro` package is not installed.
```

**Causes & Solutions:**

*   **Missing or Invalid `HF_TOKEN`**: The `401 Unauthorized` error means your Hugging Face token is missing or incorrect.
    *   **Solution**: Go to your pod's settings in RunPod, verify the `HF_TOKEN` environment variable exists and is correct. You may need to restart the pod after updating it.

*   **Incomplete Dependencies**: If a package is missing, the Docker image may not have built correctly.
    *   **Solution**: Ensure your `requirements.txt` file is complete and that the Docker build process runs successfully.

### 3. GPU / CUDA Memory Issues
```
RuntimeError: CUDA out of memory.
torch.cuda.OutOfMemoryError
```

**Causes & Solutions:**

*   **Model Too Large**: While an NVIDIA L4 has enough memory (24GB) for the 8B model, a custom, larger model could cause issues.
*   **Memory Leak**: A bug could be preventing GPU memory from being freed.
    *   **Solution**: Monitor GPU memory usage from the RunPod dashboard. If it consistently climbs, there may be a leak. Restarting the pod is a temporary fix.

### 4. Local Audio Device Issues
You may see an error in your browser console, or the client may not pick up your voice.

**Causes & Solutions:**

*   **No Browser Permission**: Your browser needs permission to access your microphone.
    *   **Solution**: When prompted, click "Allow" to grant microphone access. If you accidentally blocked it, you can change the permission in your browser's site settings (usually by clicking the lock icon in the address bar).
*   **No Default Device**: Your operating system may not have a default microphone selected.
    *   **Solution**: Open your system's sound settings and ensure a default input device is configured.

## 🛠️ Advanced Debugging on RunPod

### Viewing Pod Logs
The primary tool for debugging is the **Logs** tab in the RunPod UI for your pod.

### Connecting via SSH
For deeper, interactive debugging, you can connect to your running pod via SSH.

1.  In the RunPod UI, go to your pod and click **"Connect"**.
2.  Select the **"Connect via SSH"** option.
3.  RunPod will provide a command to connect. Copy and paste it into your local terminal.
4.  Once inside the pod, you can check `ps aux`, `nvidia-smi`, `pip list`, or run scripts manually.

### Complete Recovery
If all else fails:

1.  **Terminate** the problematic pod in RunPod.
2.  **Deploy a new pod** with the correct configuration.
3.  Connect to the new pod using its new WebSocket URL. 