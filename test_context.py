#!/usr/bin/env python3
"""
Test script to demonstrate conversational context functionality
===============================================================
This script shows how the Ultravox service maintains conversation memory.
"""

import asyncio
import numpy as np
from loguru import logger

from src.ultravox_with_context import UltravoxWithContextService
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext


async def test_conversation_context():
    """Test that the service maintains context across interactions."""
    
    # Initialize service with a simple system instruction
    service = UltravoxWithContextService(
        model_name="fixie-ai/ultravox-v0_5-llama-3_1-8b",
        temperature=0.3,
        max_tokens=50,
        system_instruction="You are a helpful assistant with memory of our conversation. Reference previous topics when relevant."
    )
    
    # Check initial context
    context = service.get_context()
    messages = context.get_messages()
    logger.info(f"Initial context: {len(messages)} messages")
    for msg in messages:
        logger.info(f"  {msg['role']}: {msg['content'][:50]}...")
    
    # Simulate first interaction
    logger.info("\n--- First interaction ---")
    # In a real scenario, this would be actual audio data
    # For testing, we'll just check the context management
    
    # Manually add a user message to simulate interaction
    service._context.add_message({
        "role": "user",
        "content": "Hi, my name is John and I love programming in Python."
    })
    
    service._context.add_message({
        "role": "assistant", 
        "content": "Hello John! It's great to meet a Python enthusiast. What kind of Python projects do you enjoy working on?"
    })
    
    # Check context after first interaction
    messages = service.get_context().get_messages()
    logger.info(f"\nContext after first interaction: {len(messages)} messages")
    for msg in messages:
        logger.info(f"  {msg['role']}: {msg['content']}")
    
    # Simulate second interaction
    logger.info("\n--- Second interaction ---")
    service._context.add_message({
        "role": "user",
        "content": "I mainly work on web applications. What's my name again?"
    })
    
    service._context.add_message({
        "role": "assistant",
        "content": "Your name is John! And it's interesting that you work on web applications with Python. Do you use frameworks like Django or Flask?"
    })
    
    # Check context after second interaction
    messages = service.get_context().get_messages()
    logger.info(f"\nContext after second interaction: {len(messages)} messages")
    for msg in messages:
        logger.info(f"  {msg['role']}: {msg['content']}")
    
    # Test context trimming
    logger.info("\n--- Testing context trimming ---")
    from src.ultravox_with_context import ContextManager
    
    context_manager = ContextManager(max_messages=4)  # Keep only 4 messages
    trimmed_context = context_manager.trim_context(service.get_context())
    
    logger.info(f"Trimmed context: {len(trimmed_context.get_messages())} messages")
    for msg in trimmed_context.get_messages():
        logger.info(f"  {msg['role']}: {msg['content']}")
    
    logger.info("\n✅ Context management test completed successfully!")


if __name__ == "__main__":
    logger.add("test_context.log", rotation="10 MB")
    asyncio.run(test_conversation_context()) 