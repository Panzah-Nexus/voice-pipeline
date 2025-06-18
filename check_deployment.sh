#!/bin/bash

# Voice Pipeline Deployment Check Script

echo "🔍 Voice Pipeline Deployment Status Check"
echo "========================================"
echo ""

BASE_URL="https://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped"

# Test 1: Health endpoint
echo "1️⃣ Testing /health endpoint:"
curl -s -w "\nHTTP Status: %{http_code}\n" "$BASE_URL/health"
echo ""

# Test 2: Ready endpoint  
echo "2️⃣ Testing /ready endpoint:"
curl -s -w "\nHTTP Status: %{http_code}\n" "$BASE_URL/ready"
echo ""

# Test 3: Debug endpoint (most important)
echo "3️⃣ Testing /debug endpoint (service status):"
curl -s "$BASE_URL/debug" | python3 -m json.tool 2>/dev/null || curl -s "$BASE_URL/debug"
echo ""

# Test 4: Check if Cerebrium deployment is running
echo "4️⃣ Cerebrium deployment status:"
echo "Run: cerebrium list"
echo ""

# Test 5: Recent logs
echo "5️⃣ To check recent logs:"
echo "Run: cerebrium logs voice-pipeline-airgapped --tail 50"
echo ""

# Test 6: Check for common errors
echo "6️⃣ To check for initialization errors:"
echo "Run: cerebrium logs voice-pipeline-airgapped | grep -E '(ERROR|Failed|error|failed|❌)'"
echo ""

echo "💡 Quick diagnosis based on /debug output:"
echo "- If stt_available=false: Ultravox model not loaded (check HF_TOKEN)"
echo "- If tts_available=false: Piper TTS not initialized"
echo "- If hf_token_present=false: HF_TOKEN not set in secrets"
echo "- If gpu_available=false: GPU/CUDA issues" 