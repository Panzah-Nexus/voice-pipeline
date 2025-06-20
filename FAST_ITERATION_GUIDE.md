# Fast Iteration Development Guide

## The Problem
You're in production but need to iterate quickly on pipeline changes without:
- ❌ Rebuilding 7GB Docker images every time
- ❌ Waiting "10 years" for pushes/pulls
- ❌ Losing development velocity

## Solution: 3-Tier Development Strategy

### **Tier 1: SSH Direct Editing (Fastest - Seconds)**
**For quick testing/debugging:**

```bash
# SSH into your running pod
ssh root@POD_ID-22.proxy.runpod.net

# Edit files directly
nano /app/src/pipecat_pipeline.py

# Restart service
pkill python && python /app/src/main.py &

# Test immediately
curl http://localhost:8000/connect
```

**Use for:** Bug fixes, parameter tweaks, small logic changes

### **Tier 2: Volume + Git Updates (Fast - 1-2 minutes)**
**For systematic changes:**

1. **Push changes to git** (GitHub/GitLab)
2. **SSH into pod and update:**
   ```bash
   # One-time setup
   cd /workspace
   git clone https://github.com/YOUR_REPO/voice-pipeline.git

   # For each iteration
   cd /workspace/voice-pipeline
   git pull
   cp -r src/* /app/src/
   pkill python && python /app/src/main.py &
   ```

**Use for:** Feature changes, algorithm updates, configuration changes

### **Tier 3: New Docker Image (Slow - 5-10 minutes)**
**Only when dependencies change:**

```bash
# Local machine - only rebuild when requirements.txt changes
./build_and_deploy.sh mlbra2006

# Deploy new pod with updated image
```

**Use for:** New pip packages, system dependencies, major refactoring

## **Recommended RunPod Template Settings**

```
Container Image: mlbra2006/voice-pipeline-airgapped:latest
Volume Disk: 10 GB  # Critical for fast restarts!
Volume Mount Path: /workspace
Container Start Command: bash -c "cd /workspace && if [ -d voice-pipeline ]; then git pull; cp -r voice-pipeline/src/* /app/src/; fi; python /app/src/main.py"
```

## **Development Workflow**

### **Daily Development:**
1. Edit code locally
2. Push to git: `git push origin main`
3. SSH to pod: `ssh root@POD_ID-22.proxy.runpod.net`
4. Update: `cd /workspace/voice-pipeline && git pull && cp -r src/* /app/src/`
5. Restart: `pkill python && python /app/src/main.py &`
6. Test: Visit `https://POD_ID-8000.proxy.runpod.net/test-page`

### **Hot Fixes (Super Fast):**
1. SSH to pod
2. Edit directly: `nano /app/src/main.py`
3. Restart: `pkill python && python /app/src/main.py &`
4. Copy changes back to local: `cat /app/src/main.py` (copy/paste)

### **Dependency Changes (Occasional):**
1. Update `requirements.txt` locally
2. Rebuild Docker image: `./build_and_deploy.sh mlbra2006`
3. Deploy new pod with updated image

## **Pro Tips for Fast Iteration**

### **1. Keep Pods Running**
- Don't terminate pods between sessions
- Use volume storage to persist git repos
- Stop/start instead of terminate/redeploy

### **2. Development Scripts**
Create aliases in pod:
```bash
# Add to pod's ~/.bashrc
alias update-code='cd /workspace/voice-pipeline && git pull && cp -r src/* /app/src/'
alias restart-app='pkill python && python /app/src/main.py &'
alias quick-deploy='update-code && restart-app'
```

### **3. Multiple Environments**
- **Dev Pod**: For experimentation (can break)
- **Staging Pod**: For testing before production
- **Production Pod**: Stable version for customers

### **4. Code Sync Strategy**
```bash
# In pod startup script
if [ ! -d "/workspace/voice-pipeline" ]; then
    cd /workspace
    git clone https://github.com/YOUR_REPO/voice-pipeline.git
fi
```

## **Time Comparison**

| Change Type | Tier 1 (SSH Edit) | Tier 2 (Git Update) | Tier 3 (New Image) |
|------------|-------------------|---------------------|---------------------|
| Bug fix | 30 seconds | 2 minutes | 10 minutes |
| Feature add | 1 minute | 3 minutes | 10 minutes |
| New dependency | N/A | N/A | 10 minutes |

## **Cost Optimization**

- **Development**: Use cheaper GPUs (RTX 3090) for iteration
- **Production**: Use A4000/A10 for customer-facing
- **Volume**: 10GB costs ~$0.10/hour but saves massive time

This strategy gives you **production-grade deployment** with **development-speed iteration**! 