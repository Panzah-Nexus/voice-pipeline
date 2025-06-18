#!/usr/bin/env python3
"""
Setup script for Piper TTS HTTP server (OPTIONAL).

NOTE: The current voice pipeline implementation does NOT require this HTTP server.
The pipeline uses Piper directly via subprocess for air-gapped deployment.

This script is kept for reference if you want to use the official Pipecat Piper
service that requires an HTTP server, or for testing purposes.
"""

import subprocess
import sys
from pathlib import Path

def check_docker():
    """Check if Docker is available."""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is available")
            return True
        else:
            print("❌ Docker is not available")
            return False
    except FileNotFoundError:
        print("❌ Docker is not installed")
        return False

def start_piper_docker():
    """Start Piper TTS server using Docker."""
    print("🚀 Starting Piper TTS server with Docker...")
    
    # Check if container is already running
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=piper-tts", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    
    if "piper-tts" in result.stdout:
        print("✅ Piper TTS server is already running")
        return True
    
    # Start the container
    cmd = [
        "docker", "run", "-d",
        "--name", "piper-tts",
        "-p", "5000:5000",
        "rhasspy/piper:latest"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Piper TTS server started successfully")
            print("🌐 Server available at: http://localhost:5000")
            return True
        else:
            print(f"❌ Failed to start Piper TTS server: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error starting Piper TTS server: {e}")
        return False

def install_piper_local():
    """Install Piper TTS locally (alternative to Docker)."""
    print("📦 Installing Piper TTS locally...")
    
    try:
        # Install piper-tts package
        subprocess.run([sys.executable, "-m", "pip", "install", "piper-tts"], check=True)
        print("✅ Piper TTS installed successfully")
        
        # Create a simple HTTP server wrapper for Piper
        server_script = """
#!/usr/bin/env python3
import asyncio
import subprocess
import tempfile
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class TTSRequest(BaseModel):
    text: str
    voice: str = "en_US-lessac-medium"

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/tts")
async def synthesize(request: TTSRequest):
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            # Run piper command
            cmd = [
                "python", "-m", "piper",
                "--model", request.voice,
                "--output_file", temp_file.name
            ]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=request.text)
            
            if process.returncode == 0:
                # Read the generated audio file
                with open(temp_file.name, 'rb') as f:
                    audio_data = f.read()
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
                return {"audio": audio_data}
            else:
                raise HTTPException(status_code=500, detail=f"TTS failed: {stderr}")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
"""
        
        # Write the server script
        script_path = Path("piper_server.py")
        script_path.write_text(server_script)
        print(f"✅ Created Piper server script: {script_path}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Piper TTS: {e}")
        return False

async def test_piper_server():
    """Test if Piper TTS server is responding."""
    print("🔍 Testing Piper TTS server...")
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get("http://localhost:5000/health", timeout=10) as response:
                if response.status == 200:
                    print("✅ Piper TTS server is responding")
                    return True
                else:
                    print(f"❌ Piper TTS server returned status: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Failed to connect to Piper TTS server: {e}")
        return False

def main():
    """Main setup function."""
    print("🎤 Setting up Piper TTS server for voice pipeline...")
    
    # Try Docker first
    if check_docker():
        if start_piper_docker():
            print("\n✅ Piper TTS server setup complete!")
            print("🌐 Server running at: http://localhost:5000")
            print("\n📋 Next steps:")
            print("1. Test your setup by running: python test_piper_server.py")
            print("2. Start your voice pipeline: python src/pipecat_pipeline.py")
            return
    
    # Fallback to local installation
    print("\n🔄 Docker not available, trying local installation...")
    if install_piper_local():
        print("\n✅ Piper TTS installed locally!")
        print("📋 To start the server, run:")
        print("   python piper_server.py")
        print("\n📋 Then start your voice pipeline:")
        print("   python src/pipecat_pipeline.py")
    else:
        print("\n❌ Failed to set up Piper TTS server")
        print("📋 Manual setup options:")
        print("1. Install Docker and run: docker run -p 5000:5000 rhasspy/piper:latest")
        print("2. Or install piper-tts: pip install piper-tts")

if __name__ == "__main__":
    main() 