# Utility Scripts

This directory contains test and development utilities that are NOT required for deployment.

## Files

### audio_utils.py
Audio helper functions for microphone capture and playback. Used by the test client.

### websocket_client.py
Test client for streaming microphone audio to the server. Useful for local testing.

**Usage:**
```bash
export WS_SERVER="ws://localhost:8000/ws"
python -m utils.websocket_client
```

### simple_test_server.py
Echo test server that returns audio back without AI processing. Useful for testing WebSocket connectivity.

**Usage:**
```bash
python -m utils.simple_test_server
```

## Note

These utilities are for development and testing only. They are not included in the Cerebrium deployment. 