#!/usr/bin/env python3
"""Test Docker build with simplified approach."""
import subprocess
import sys
import os

def test_docker_build():
    """Test building the Docker image."""
    print("🔨 Testing Docker build...")
    print("=" * 50)
    
    # Check if Docker is available
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        print(f"✅ Docker version: {result.stdout.strip()}")
    except:
        print("❌ Docker not available!")
        return False
    
    # Build with progress output
    print("\n📦 Building Docker image...")
    print("This may take a few minutes...\n")
    
    # Get parent directory (project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    cmd = [
        "docker", "build",
        "-f", os.path.join(project_root, "docker/Dockerfile"),
        "-t", "voice-pipeline-test",
        "--progress=plain",  # Show detailed output
        project_root  # Build context is project root
    ]
    
    try:
        # Run build and show output in real-time
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        
        if process.returncode == 0:
            print("\n✅ Docker build successful!")
            return True
        else:
            print(f"\n❌ Docker build failed with exit code: {process.returncode}")
            return False
            
    except Exception as e:
        print(f"\n❌ Build error: {e}")
        return False

def main():
    """Run the test."""
    print("🚀 Docker Build Test")
    print("=" * 50)
    
    if test_docker_build():
        print("\n✅ Build test passed! You can now deploy to Cerebrium.")
        print("\nNext steps:")
        print("1. cerebrium login")
        print("2. cerebrium deploy")
    else:
        print("\n❌ Build test failed. Please fix the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 