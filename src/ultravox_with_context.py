"""
Context-aware Ultravox Service
==============================
This module extends the standard Ultravox service to maintain conversation history,
enabling natural conversational flow with memory of previous interactions.
"""

import json
import time
from typing import AsyncGenerator, List, Optional, Dict

import numpy as np
from loguru import logger

from pipecat.frames.frames import (
    AudioRawFrame,
    CancelFrame,
    EndFrame,
    ErrorFrame,
    Frame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMTextFrame,
    StartFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.ultravox.stt import UltravoxSTTService, AudioBuffer, UltravoxModel
from pipecat.processors.aggregators.openai_llm_context import (
    OpenAILLMContext,
    OpenAILLMContextFrame,
)


class UltravoxWithContextService(UltravoxSTTService):
    """
    Context-aware Ultravox service that maintains conversation history.
    
    This service extends the standard Ultravox to:
    1. Maintain conversation context across interactions
    2. Build on previous exchanges for contextual understanding
    3. Support natural turn-taking and continuous conversation
    """
    
    def __init__(
        self,
        *,
        model_name: str = "fixie-ai/ultravox-v0_5-llama-3_1-8b",
        hf_token: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 100,
        system_instruction: Optional[str] = None,
        **kwargs,
    ):
        # Don't pass system_instruction to parent class
        super().__init__(
            model_name=model_name,
            hf_token=hf_token,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Initialize conversation context
        self._context = OpenAILLMContext()
        
        # Set system instruction
        if system_instruction:
            self._context.set_messages([{
                "role": "system",
                "content": system_instruction
            }])
        else:
            # Default system instruction if none provided
            self._context.set_messages([{
                "role": "system",
                "content": "You are a helpful AI assistant."
            }])
            
        # Track whether we've seen user input yet
        self._first_interaction = True
        
        logger.info(f"Initialized UltravoxWithContextService with conversation memory")
        
    def set_context(self, context: OpenAILLMContext):
        """Set the conversation context."""
        self._context = context
        logger.info(f"Context set with {len(context.get_messages())} messages")
        
    def get_context(self) -> OpenAILLMContext:
        """Get the current conversation context."""
        return self._context
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process incoming frames, including context frames."""
        
        # Handle context frames to update conversation history
        if isinstance(frame, OpenAILLMContextFrame):
            self._context = frame.context
            logger.debug(f"Updated context with {len(self._context.get_messages())} messages")
            # Don't push context frames downstream, they're for internal use
            return
            
        # Let parent handle other frames
        await super().process_frame(frame, direction)
        
    async def _process_audio_buffer(self) -> AsyncGenerator[Frame, None]:
        """Process audio with full conversation context."""
        try:
            self._buffer.is_processing = True
            
            if not self._buffer.frames:
                logger.warning("No audio frames to process")
                yield ErrorFrame("No audio frames to process")
                return
                
            # Process audio frames
            audio_arrays = []
            for f in self._buffer.frames:
                if hasattr(f, "audio") and f.audio:
                    if isinstance(f.audio, bytes):
                        try:
                            arr = np.frombuffer(f.audio, dtype=np.int16)
                            if arr.size > 0:
                                audio_arrays.append(arr)
                        except Exception as e:
                            logger.error(f"Error processing bytes audio frame: {e}")
                    elif isinstance(f.audio, np.ndarray):
                        if f.audio.size > 0:
                            if f.audio.dtype != np.int16:
                                audio_arrays.append(f.audio.astype(np.int16))
                            else:
                                audio_arrays.append(f.audio)
                                
            if not audio_arrays:
                logger.warning("No valid audio data found in frames")
                yield ErrorFrame("No valid audio data found in frames")
                return
                
            # Concatenate and convert audio
            audio_data = np.concatenate(audio_arrays)
            audio_float32 = audio_data.astype(np.float32) / 32768.0
            
            # Build messages with full conversation context
            messages = self._context.get_messages().copy()
            
            # Add the audio input as the latest user message
            messages.append({
                "role": "user",
                "content": "<|audio|>\n"
            })
            
            logger.info(f"Processing audio with {len(messages)} messages in context")
            
            # Generate response using full context
            if self._model:
                try:
                    await self.start_ttfb_metrics()
                    await self.start_processing_metrics()
                    
                    yield LLMFullResponseStartFrame()
                    
                    response_text = ""
                    
                    async for response in self._model.generate(
                        messages=messages,
                        temperature=self._temperature,
                        max_tokens=self._max_tokens,
                        audio=audio_float32,
                    ):
                        await self.stop_ttfb_metrics()
                        
                        chunk = json.loads(response)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0]["delta"]
                            if "content" in delta:
                                new_text = delta["content"]
                                if new_text:
                                    response_text += new_text
                                    yield LLMTextFrame(text=new_text)
                                    
                    await self.stop_processing_metrics()
                    
                    # Add the complete response to context
                    if response_text:
                        # First add a placeholder for the user's audio input
                        self._context.add_message({
                            "role": "user",
                            "content": "[Audio input processed]"  # Placeholder for audio
                        })
                        
                        # Then add the assistant's response
                        self._context.add_message({
                            "role": "assistant",
                            "content": response_text
                        })
                        
                        logger.info(f"Added response to context. Total messages: {len(self._context.get_messages())}")
                    
                    yield LLMFullResponseEndFrame()
                    
                    # Push updated context frame
                    yield OpenAILLMContextFrame(context=self._context)
                    
                except Exception as e:
                    logger.error(f"Error generating text from model: {e}")
                    yield ErrorFrame(f"Error generating text: {str(e)}")
            else:
                logger.warning("No model available for text generation")
                yield ErrorFrame("No model available for text generation")
                
        except Exception as e:
            logger.error(f"Error processing audio buffer: {e}")
            import traceback
            logger.error(traceback.format_exc())
            yield ErrorFrame(f"Error processing audio: {str(e)}")
        finally:
            self._buffer.is_processing = False
            self._buffer.frames = []
            self._buffer.started_at = None
            
            
class ContextManager:
    """
    Manages conversation context and provides helper methods.
    """
    
    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        
    def trim_context(self, context: OpenAILLMContext) -> OpenAILLMContext:
        """Trim context to prevent it from growing too large."""
        messages = context.get_messages()
        
        # Always keep system message if present
        system_messages = [m for m in messages if m["role"] == "system"]
        other_messages = [m for m in messages if m["role"] != "system"]
        
        # Keep only the most recent messages
        if len(other_messages) > self.max_messages:
            other_messages = other_messages[-self.max_messages:]
            
        # Rebuild context
        new_messages = system_messages + other_messages
        new_context = OpenAILLMContext()
        new_context.set_messages(new_messages)
        
        return new_context 