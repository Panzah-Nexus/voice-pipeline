#!/usr/bin/env python3
"""
Test the health and debug endpoints of the deployed service.
"""

import requests
import json
import os

# Get the deployment URL
BASE_URL = os.environ.get("CEREBRIUM_URL", "https://api.cortex.cerebrium.ai/v4/p-468ff80b/voice-pipeline-airgapped")

def test_endpoints():
    """Test various endpoints."""
    print("🧪 Testing Cerebrium Deployment Endpoints")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print()
    
    # Test health endpoint
    print("1️⃣ Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test ready endpoint
    print("2️⃣ Testing /ready endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/ready", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test debug endpoint
    print("3️⃣ Testing /debug endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/debug", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("✅ Tests completed")

if __name__ == "__main__":
    test_endpoints() 