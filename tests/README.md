# Voice Pipeline Tests

This directory contains test utilities for the voice pipeline project.

## Available Tests

### test_piper_local.py
Tests the local Piper TTS service integration.

**Usage:**
```bash
cd voice-pipeline
python tests/test_piper_local.py
```

**Requirements:**
- Piper TTS models must be available
- `piper_service.py` must be properly configured

### test_docker_build.py
Tests that the Docker image builds correctly.

**Usage:**
```bash
cd voice-pipeline
python tests/test_docker_build.py
```

**Requirements:**
- Docker must be installed and running
- Build context requires access to `docker/Dockerfile`

## Running Tests

All tests can be run from the project root directory:

```bash
# Run Piper TTS test
python -m tests.test_piper_local

# Run Docker build test
python -m tests.test_docker_build
```

## Note

These are utility tests for development and deployment validation, not unit tests. They help ensure that:
- Local services (like Piper TTS) are working correctly
- Docker images can be built successfully
- The deployment pipeline is functioning 