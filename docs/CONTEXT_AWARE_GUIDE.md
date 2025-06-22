# Context-Aware Voice Pipeline Guide

## Overview

This guide explains the new context-aware implementation that enables natural conversational flow with memory across interactions. The system now maintains conversation history, allowing for contextual responses that build on previous exchanges.

## Key Features

### 1. **Continuous Conversation Memory**
- The AI remembers what was discussed throughout the entire conversation
- Each interaction builds on previous context rather than being isolated
- Conversation history is maintained in the `OpenAILLMContext` structure

### 2. **Natural Turn-Taking**
- Smooth back-and-forth conversation without awkward pauses
- The system understands when you're referring to previous topics
- Responses are contextually aware and relevant

### 3. **Real-Time Speech Interaction**
- Direct audio-to-response processing bypasses text bottlenecks
- Ultravox processes audio with full conversation context
- Faster, more natural responses with context awareness

### 4. **Contextual Understanding**
- Responses build on previous exchanges
- The AI can reference earlier topics naturally
- Maintains conversational continuity

## Architecture Changes

### Previous Architecture (No Context)
```
Audio → Ultravox → Response (isolated)
         ↑
         └─ Fixed prompt: [{"role": "user", "content": "<|audio|>\n"}]
```

### New Architecture (With Context)
```
Audio → UltravoxWithContext → Response (contextual)
         ↑                        ↓
         └─ Full conversation ←───┘
            history
```

## Implementation Details

### 1. **UltravoxWithContextService**

The new service extends the base Ultravox service with:

```python
class UltravoxWithContextService(UltravoxSTTService):
    # Maintains OpenAILLMContext internally
    # Passes full conversation history to model
    # Updates context after each interaction
```

Key methods:
- `set_context(context)`: Set the conversation context
- `get_context()`: Get the current conversation context
- `_process_audio_buffer()`: Processes audio with full context

### 2. **Context Management**

The system maintains conversation history in a structured format:

```python
[
    {"role": "system", "content": "System instruction..."},
    {"role": "user", "content": "[Audio input processed]"},
    {"role": "assistant", "content": "Hello! How can I help?"},
    {"role": "user", "content": "[Audio input processed]"},
    {"role": "assistant", "content": "Based on what you said earlier..."},
    # ... continues
]
```

### 3. **Context Trimming**

To prevent context from growing too large:

```python
context_manager = ContextManager(max_messages=20)
# Automatically trims to keep last 20 messages
# Preserves system message
```

## Usage Examples

### Basic Conversation Flow

```
User: "Hi, my name is Sarah and I'm learning Python"
Bot: "Hello Sarah! It's great that you're learning Python."

User: "What's a good project for beginners?"
Bot: "Since you're learning Python, Sarah, I'd suggest starting with a simple calculator or todo app."

User: "What was my name again?" (Testing memory)
Bot: "Your name is Sarah! You mentioned you're learning Python."
```

### Context References

The bot can now:
- Remember names and preferences
- Reference previous topics
- Build on earlier discussions
- Maintain conversation threads

## Configuration

### System Instruction

The system instruction sets the tone for contextual conversations:

```python
SYSTEM_INSTRUCTION = """You are a helpful AI assistant with full memory of our conversation. 

Key behaviors:
1. Remember and reference previous parts of our conversation naturally
2. Build on what we've discussed before without repeating yourself
3. If the user refers to something we discussed earlier, acknowledge it
4. Keep responses concise (1-2 sentences) unless more detail is needed
5. Maintain conversational continuity and flow
6. If context seems missing or unclear, politely ask for clarification

You have access to our full conversation history, so use it to provide contextual, relevant responses."""
```

### Parameters

- `max_messages`: Maximum messages to keep in context (default: 20)
- `temperature`: Controls response consistency (lower = more consistent)
- `max_tokens`: Maximum response length

## Monitoring

The pipeline includes context monitoring:

```python
async def monitor_context():
    # Logs context size every 10 seconds
    # Automatically trims if > 25 messages
    # Provides visibility into conversation state
```

## Best Practices

1. **Clear System Instructions**: Define how the AI should use context
2. **Appropriate Context Size**: Balance memory vs performance (20-30 messages)
3. **Context Resets**: Consider resetting context for new conversations
4. **Monitor Growth**: Watch context size to prevent excessive growth

## Troubleshooting

### Common Issues

1. **Context Not Persisting**
   - Check that `UltravoxWithContextService` is being used
   - Verify context frames are being processed

2. **Responses Not Contextual**
   - Ensure system instruction emphasizes context usage
   - Check that context contains previous messages

3. **Performance Degradation**
   - Reduce max_messages if context gets too large
   - Monitor context trimming logs

## Testing

Run the test script to verify context functionality:

```bash
python test_context.py
```

This will demonstrate:
- Context initialization
- Message accumulation
- Context trimming
- Memory persistence

## Future Enhancements

Potential improvements:
- Semantic context compression
- Long-term memory storage
- Context summarization
- Multi-session persistence 