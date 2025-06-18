"""Entry point for the air-gapped voice pipeline demo."""
from __future__ import annotations

import os
import sys

def main() -> None:
    """Main entry point with fallback handling for air-gapped deployment."""
    
    # Check if we have required environment variables
    hf_token = os.environ.get("HF_TOKEN")
    
    if not hf_token:
        print("⚠️  HF_TOKEN not found in environment")
        print("   The Ultravox STT service will not be available")
        
    print("🔒 Air-gapped deployment - no external API calls")
    print("🚀 Starting Voice Pipeline Server...")
    
    try:
        # Try to import and run the full pipeline
        from .pipecat_pipeline import run_server
        print("📡 Initializing AI services...")
        
        import asyncio
        asyncio.run(run_server())
        
    except Exception as e:
        print(f"❌ Failed to start full AI pipeline: {e}")
        print("🔄 Falling back to simple echo server for testing...")
        
        try:
            # Import from utils instead of src
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from utils.simple_test_server import run_server as run_test_server
            import asyncio
            asyncio.run(run_test_server())
        except Exception as e2:
            print(f"❌ Failed to start test server: {e2}")
            print("💡 Try running: python -m utils.simple_test_server")
            sys.exit(1)

if __name__ == "__main__":
    main()
