# RunPod Deployment Guide

## Step 1: Deploy on RunPod

1. **Go to RunPod Console**: https://www.runpod.io/console/pods

2. **Deploy New Pod**:
   - Click "Deploy" 
   - Choose "Deploy On-Demand"

3. **GPU Configuration**:
   - Select **NVIDIA RTX A4000** (16GB VRAM) or **A10** if available
   - These GPUs match your on-premises target

4. **Container Configuration**:
   ```
   Container Image: mlbra2006/voice-pipeline-airgapped:latest
   Container Disk: 20GB
   Volume Disk: 10GB (optional)
   Expose HTTP Ports: 8000
   Expose TCP Ports: 22 (for SSH access)
   ```

5. **SSH Configuration** (HIGHLY RECOMMENDED):
   - **Add your public key**: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPdGs+b3grD0xJqCYt7IyPevrvJpo/tsp2tbmy6mxgHq ibrahim-mohammad@ibrahim-mohammad-XPS-15-9530`
   - This enables secure terminal access for debugging

6. **Security Options**:
   - **Volume Encryption**: ✅ **Enable** (recommended for production)
   - **Start/Stop Protection**: ✅ **Enable** (prevents accidental termination)

7. **Environment Variables**:
   ```
   HF_TOKEN = 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
   ```

8. **Advanced Options**:
   - Docker Command: `python src/main.py`
   - Container Start Command: (leave empty)

## Step 2: Get Your Pod URLs

Once deployed, your pod will have:
- **Pod ID**: Something like `abc123def456`
- **HTTP URL**: `https://abc123def456-8000.proxy.runpod.net`
- **WebSocket URL**: `wss://abc123def456-8000.proxy.runpod.net/ws`

## Step 3: Access Your Pod

### SSH Terminal Access
Once deployed, you can access your pod via SSH:
```bash
ssh root@YOUR_POD_ID-22.proxy.runpod.net
```

**Why SSH access is crucial:**
- Real-time log monitoring: `tail -f /var/log/*.log`
- Process inspection: `ps aux | grep python`
- GPU monitoring: `nvidia-smi`
- Network troubleshooting: `netstat -tlnp`
- File system debugging

### Web Terminal (Alternative)
RunPod also provides a web-based terminal in the console if SSH fails.

## Step 4: Test the Deployment

### Option A: Test Page (Recommended)
1. Open: `https://YOUR_POD_ID-8000.proxy.runpod.net/test-page`
2. This will show:
   - Connection status
   - WebSocket URL being used
   - Audio testing interface

### Option B: Connect Endpoint
1. Open: `https://YOUR_POD_ID-8000.proxy.runpod.net/connect`
2. Should return JSON like:
   ```json
   {
     "websocket_url": "wss://YOUR_POD_ID-8000.proxy.runpod.net/ws",
     "status": "ready"
   }
   ```

### Option C: WebSocket Client
1. Open: `client/websocket-client/index.html` in browser
2. Update the WebSocket URL to: `wss://YOUR_POD_ID-8000.proxy.runpod.net/ws`
3. Test audio connection

## Step 5: Expected Behavior

When working correctly:
1. WebSocket connects successfully
2. You hear the greeting: **"Hello! I'm your AI assistant. How can I help you today?"**
3. You can speak and get AI responses
4. Audio is clear and responsive

## Security Considerations

### Volume Encryption
**YES, enable volume encryption for these reasons:**

✅ **Enable encryption if:**
- Storing sensitive audio data
- Compliance requirements (HIPAA, GDPR)
- Production/customer-facing deployment
- Processing proprietary conversations

❌ **Skip encryption if:**
- Testing/development only
- No sensitive data stored
- Performance is critical (small overhead)

### SSH Key Security
- **Your public key is safe to share**: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI...`
- **Never share your private key**: Keep `~/.ssh/id_ed25519` secure
- **Add to RunPod**: Paste the public key in deployment settings

### Network Security
- RunPod provides HTTPS/WSS by default
- SSH access is restricted to your key only
- No sensitive environment variables in logs

## Troubleshooting

### Pod Won't Start
- Check logs in RunPod console
- Ensure HF_TOKEN is set correctly
- Try restarting the pod

### No Audio/WebSocket Issues
- Check the `/test-page` for diagnostics
- Verify WebSocket URL format
- Check browser console for errors

### Performance Issues
- Ensure you selected A4000/A10 GPU
- Check GPU utilization in RunPod console
- Monitor memory usage

### SSH Connection Issues
**Can't connect via SSH:**
```bash
# Test connection with verbose output
ssh -v root@YOUR_POD_ID-22.proxy.runpod.net

# If permission denied, check your key:
ssh-add ~/.ssh/id_ed25519
```

**SSH Commands for Voice Pipeline Debugging:**
```bash
# Check if service is running
ps aux | grep python

# Monitor real-time logs
tail -f /app/logs/* 2>/dev/null || echo "No logs yet"

# Check GPU usage
nvidia-smi

# Test WebSocket locally inside pod
curl -I http://localhost:8000/connect

# Check port bindings
netstat -tlnp | grep 8000
```

## Cost Estimation
- **A4000**: ~$0.50/hour
- **A10**: ~$0.80/hour  
- Same GPUs you'll use on-premises

## Next Steps
Once working on RunPod, the same container works on your on-premises A10 setup! 