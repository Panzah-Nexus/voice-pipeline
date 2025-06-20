#!/bin/bash
# Build and Deploy Script for RunPod Migration
# Usage: ./build_and_deploy.sh [docker-username]

set -e  # Exit on any error

# Configuration
DOCKER_USERNAME=${1:-"your-username"}
IMAGE_NAME="voice-pipeline-airgapped"
TAG="latest"
FULL_IMAGE="${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"

echo "🚀 Starting build and deployment process..."
echo "Docker image: ${FULL_IMAGE}"

# Check if required tools are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python first."
    exit 1
fi

# Check if HF_TOKEN is set
if [ -z "$HF_TOKEN" ]; then
    echo "⚠️  Warning: HF_TOKEN environment variable is not set."
    echo "   Set it with: export HF_TOKEN='your-token-here'"
    read -p "   Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Build Docker image
echo ""
echo "📦 Step 1: Building Docker image (lightweight RunPod version)..."
docker build -f docker/Dockerfile.light -t ${IMAGE_NAME}:${TAG} .
echo "✅ Docker image built successfully!"

# Step 2: Tag for Docker Hub
echo ""
echo "🏷️  Step 2: Tagging image for Docker Hub..."
docker tag ${IMAGE_NAME}:${TAG} ${FULL_IMAGE}
echo "✅ Image tagged as: ${FULL_IMAGE}"

# Step 3: Push to Docker Hub
echo ""
echo "📤 Step 3: Pushing to Docker Hub..."
echo "   (You may need to login with: docker login)"
docker push ${FULL_IMAGE}
echo "✅ Image pushed successfully!"

# Step 4: Deploy to RunPod (optional)
echo ""
echo "🚀 Step 4: Deploy to RunPod?"
echo "   This will use the deployment script to create a RunPod instance."
read -p "   Deploy now? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Install RunPod SDK if not installed
    if ! python -c "import runpod" &> /dev/null; then
        echo "📦 Installing RunPod SDK..."
        pip install runpod>=1.5.0
    fi
    
    # Check if RUNPOD_API_KEY is set
    if [ -z "$RUNPOD_API_KEY" ]; then
        echo "❌ RUNPOD_API_KEY environment variable is not set."
        echo "   Get your API key from: https://runpod.io/console/user/settings"
        echo "   Then set it with: export RUNPOD_API_KEY='your-key-here'"
        exit 1
    fi
    
    # Update the deployment script with the correct image name
    echo "🔧 Updating deployment script with image name..."
    sed -i.bak "s|voice-pipeline-airgapped:latest|${FULL_IMAGE}|g" runpod_deploy.py
    
    # Run deployment
    echo "🚀 Deploying to RunPod..."
    python runpod_deploy.py deploy
    
    # Restore original deployment script
    mv runpod_deploy.py.bak runpod_deploy.py
    
    echo ""
    echo "🎉 Deployment complete!"
else
    echo ""
    echo "📋 Manual deployment steps:"
    echo "   1. Set RUNPOD_API_KEY: export RUNPOD_API_KEY='your-key'"
    echo "   2. Install RunPod SDK: pip install runpod"
    echo "   3. Update image in runpod_deploy.py to: ${FULL_IMAGE}"
    echo "   4. Run: python runpod_deploy.py deploy"
fi

echo ""
echo "✅ Build process complete!"
echo "📖 Next steps:"
echo "   1. Check your RunPod dashboard for deployment status"
echo "   2. Test the WebSocket connection using the provided URLs"
echo "   3. Update your client with the new RunPod URLs"
echo ""
echo "🏠 For on-premises deployment, use:"
echo "   docker run -d --gpus all -p 8000:8000 \\"
echo "     -e HF_TOKEN='$HF_TOKEN' \\"
echo "     -e PIPER_MODEL='en_US-lessac-medium' \\"
echo "     ${FULL_IMAGE}" 