#!/usr/bin/env python3
"""Quick test after redeployment."""

import asyncio
import aiohttp
import json

BASE_URL = "https://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped"

async def test_deployment():
    print("🔍 Testing redeployed voice pipeline")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test debug endpoint (should work now!)
        print("\n1️⃣ Testing /debug endpoint:")
        try:
            async with session.get(f"{BASE_URL}/debug") as resp:
                if resp.status == 200:
                    debug_info = await resp.json()
                    print("✅ Debug endpoint working!")
                    print(json.dumps(debug_info, indent=2))
                    
                    # Check service status
                    if debug_info.get("stt_available"):
                        print("✅ STT (Ultravox) is available")
                    else:
                        print("❌ STT (Ultravox) NOT available - check HF_TOKEN")
                        
                    if debug_info.get("tts_available"):
                        print("✅ TTS (Piper) is available")
                    else:
                        print("❌ TTS (Piper) NOT available")
                        
                    if debug_info.get("hf_token_present"):
                        print("✅ HF_TOKEN is present")
                    else:
                        print("❌ HF_TOKEN NOT present - add to cerebrium.toml")
                        
                else:
                    print(f"❌ Debug endpoint returned: {resp.status}")
        except Exception as e:
            print(f"❌ Debug endpoint failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_deployment()) 