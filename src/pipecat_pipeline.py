# This example demonstrates how to create an interruptible PURELY LOCAL audio pipeline using Pipecat.
# It uses the Moonshine ASR for speech-to-text, Kokoro for text-to-speech, and Ollama for LLM.
# The pipeline is designed to be interruptible, allowing for real-time interaction with the user.
#
# Note you need to have the following services running:
# - Ollama server running with the Llama 3.1 model
# - Kokoro-onnx in assets folder 
# $ pip install kokoro-onnx
# copy kokoro-v1.0.onnx and voices-v1.0.bin to the assets folder
# - Moonshine ASR onnx installed
# $ uv pip install useful-moonshine-onnx@git+https://git@github.com/usefulsensors/moonshine.git#subdirectory=moonshine-onnx
import os
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

FAST_VAD = SileroVADAnalyzer(
    params=VADParams(
        min_silence_ms=200,      # default 500
        speech_pad_ms=120,       # default 400 – keeps a bit of context
        window_ms=160,           # 10 × 16-kHz frames
    )
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask

from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.serializers.protobuf import ProtobufFrameSerializer

from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from src.kokoro.tts_subprocess_wrapper import KokoroSubprocessTTSService as _SubTTS
from pipecat.services.whisper.stt import WhisperSTTService, Model
from pipecat.services.ollama.llm import OLLamaLLMService
from pipecat.utils.tracing.setup import setup_tracing



from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")


async def run_bot(websocket_client):

    logger.info("Starting bot")

    transport = FastAPIWebsocketTransport(
        websocket=websocket_client,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_analyzer=FAST_VAD,
            serializer=ProtobufFrameSerializer(),
        ),
    )

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    stt = WhisperSTTService(
            model=Model.DISTIL_MEDIUM_EN,
            device="cuda",
            transcribe_options=dict(temperature=0) 
    )

    tts = _SubTTS(
        _SubTTS.InputParams(
            python_path=Path("/venv/tts/bin/python"),  # adjust to your pod layout
            model_path=Path("/app/assets/kokoro-v1.0.onnx"),
            voices_path=Path("/app/assets/voices-v1.0.bin"),
            voice_id="af_bella",
            language="en-us",
            speed=1.0,
            debug=False,
        )
    )

    llm = OLLamaLLMService(
        model="llama3:8b",
        base_url="http://localhost:11434/v1",
    )

    messages = [
        {
            "role": "system",
            "content": "You are a helpful LLM. Your goal is to demonstrate your capabilities in a succinct way. Your output will be converted to audio so don't include special characters in your answers. Respond to what the user said in a creative and helpful way.",
        },
    ]

    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [
            transport.input(),  # Transport user input
            rtvi,
            stt,
            context_aggregator.user(),  # User responses
            llm,  # LLM
            tts,  # TTS
            transport.output(),  # Transport bot output
            context_aggregator.assistant(),  # Assistant spoken responses
        ]
    )

    setup_tracing(
        console_export=True,  # Set to True for debug output
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
            report_only_initial_ttfb=False,
        ),
        observers=[RTVIObserver(rtvi)],
        enable_tracing=True,                                  # Enable tracing for this task
        enable_turn_tracking=True, 
    )

    messages.append({"role": "system", "content": "Please introduce yourself to the user."})
    await task.queue_frames([context_aggregator.user().get_context_frame()])

    runner = PipelineRunner()

    await runner.run(task)


if __name__ == "__main__":
    asyncio.run(run_bot())