#!/bin/bash

echo "Fixing onnxruntime GPU installation..."

# Step 1: Uninstall all onnxruntime versions
echo "Step 1: Uninstalling all onnxruntime versions..."
pip uninstall -y onnxruntime onnxruntime-gpu

# Step 2: Install onnxruntime-gpu first
echo "Step 2: Installing onnxruntime-gpu..."
pip install onnxruntime-gpu==1.22.0

# Step 3: Create a dummy onnxruntime package to prevent CPU version installation
echo "Step 3: Creating dummy onnxruntime package..."
python << 'EOF'
import site
import os

site_packages = site.getsitepackages()[0]
dummy_path = os.path.join(site_packages, "onnxruntime")
os.makedirs(dummy_path, exist_ok=True)

# Create __init__.py that imports from onnxruntime_gpu
with open(os.path.join(dummy_path, "__init__.py"), "w") as f:
    f.write("from onnxruntime_gpu import *\n")

# Create dummy dist-info to satisfy pip
dist_info_path = os.path.join(site_packages, "onnxruntime-1.22.0.dist-info")
os.makedirs(dist_info_path, exist_ok=True)

with open(os.path.join(dist_info_path, "METADATA"), "w") as f:
    f.write("""Metadata-Version: 2.1
Name: onnxruntime
Version: 1.22.0
Summary: Dummy package redirecting to onnxruntime-gpu
""")

with open(os.path.join(dist_info_path, "RECORD"), "w") as f:
    f.write("onnxruntime/__init__.py,,\n")

print("Dummy onnxruntime package created successfully!")
EOF

# Step 4: Install other dependencies
echo "Step 4: Installing other dependencies..."
pip install --no-deps pipecat-ai[whisper,websocket,silero]~=0.0.71
pip install kokoro-onnx~=0.4.8
pip install ctranslate2[cuda]~=4.6.0
pip install faster-whisper~=1.1.1

# Install remaining dependencies
pip install av~=14.4.0 tokenizers protobuf~=5.29.3 aiohttp~=3.11.12 loguru~=0.7.3 pydantic~=2.10.6 python-dotenv~=1.0.1 uvicorn~=0.30.5 phonemizer~=3.2.1 pyloudnorm~=0.1.1 resampy~=0.4.3 soxr~=0.5.0.post1 openai~=1.70.0 huggingface-hub pyyaml tqdm typing-extensions coloredlogs flatbuffers packaging sympy mpmath

echo "Installation complete! Testing GPU availability..."
python -c "import onnxruntime as ort; print('Available providers:', ort.get_available_providers())" 