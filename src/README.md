# 🎙️ Local Voice Pipeline - Source Code

This directory contains the core pipeline implementation for the **Local Cascaded Voice Pipeline**.

## 🏗️ Architecture

### **Cascaded Components:**
- **`WhisperSTTService`** - Local speech-to-text (CUDA accelerated)
- **`OLLamaLLMService`** - Local language model with conversation memory
- **`KokoroTTSService`** - PyTorch-based text-to-speech

### **Key Files:**

| File | Purpose |
|------|---------|
| `main.py` | FastAPI server entry point |
| `pipecat_pipeline.py` | **Main pipeline logic** - cascaded STT → LLM → TTS |
| `kokoro_tts_service.py` | TTS service implementation (PyTorch) |
| `audio_frame_serializer.py` | Audio frame handling utilities |

## 🎯 **Core Features:**

- **✅ Full conversation memory** - OpenAI-compatible context management
- **✅ Function calling support** - Built-in tool calling capabilities
- **✅ Fast interruption handling** - Smooth conversational flow
- **✅ English-only enforcement** - Strong language constraints
- **✅ Component-level debugging** - Isolate and troubleshoot each stage
- **✅ No external dependencies** - Completely offline operation

## 🔄 **Migration Notes:**

This implementation replaces the previous Ultravox-based approach with a proper cascaded pipeline for better:
- Conversation memory and context handling
- Function calling and tool integration
- Performance debugging and optimization
- Language model flexibility and updates

