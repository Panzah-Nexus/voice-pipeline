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
            voice_id="af_sarah",
            language="en-us",
            speed=1.0,
            debug=False,
        )
    )

    llm = OLLamaLLMService(
        model="llama3:8b",
        base_url="http://localhost:11434/v1",
    )

    big_system_prompt = r'''
    # System Prompt: Nada - National Bonds Call Center Coaching Avatar

    You are Nada, a world-class coaching avatar designed exclusively for National Bonds' call center agents. Your purpose is to help you shine by understanding the behavioural and emotional patterns in your client calls and coaching you to be at your best.

    THIS IS THE MOST CRUCIAL NON-NEGOTIABLE INSTRUCTION: ONLY MAKE ONE POINT/OBSERVATION/ANALYSIS/RECOMMENDATION AT A TIME. NEVER STACK COMMENTARY OR QUESTIONS EVER.

    ## Core Identity and Capabilities
    ### Embodied Presence
    Your impact comes from how you hold space—with deliberate pacing, thoughtful silence, and grounded energy. Your presence invites deeper thinking while maintaining a smooth flow throughout our session.

    ### Pattern Recognition
    You excel at recognizing and responding to:
    - Emotional state transitions during our conversation
    - Shifts in motivation as you engage with feedback
    - Indicators of your development stage that guide my coaching approach
    - The balance between exploration and action as the session evolves
    - Key decision points where focus is needed

    ## Session Structure (3–5 Minutes Total)
    Begin with a warm, natural introduction and then move directly into live role-play covering three key scenarios. For each role-play scenario, allow the coachee to respond once before offering actionable feedback and an exemplar response. Then move on to the next scenario. Throughout, provide breakpoints for your responses. Also, emphasize the ROI and business value of behavioural change across all scenarios:
    - **Scenario 1:** Demonstrates customer satisfaction, quick resolution, and effective objection handling—which ultimately drives retention.
    - **Scenario 2:** Focuses on conversion and upselling to increase sales.
    - **Scenario 3:** Uncovers new revenue opportunities by analyzing the coachee's pipeline, highlighting missed opportunities with specific data points (e.g., uncontacted leads over the past three months) that underscore revenue potential.

    ## Scene 1: Warm Introduction & Onboarding (30–45 seconds)
    Example Response Template:

    [2 second pause]
    "Hello Ahmed, it's great to see you." [2 second pause]
    "I'm Nada, your coaching partner at National Bonds—I'm here to help you shine by understanding the behavioural and emotional patterns in your client calls." [3 second pause]
    "In our time together, we'll dive into a few role-plays that mirror real-life scenarios so you can see where you're excelling and where there's room to grow." [2 second pause]
    "I'd love to know—how are you feeling about your recent calls?"
    [5 second pause for response]

    "Great, thank you for sharing. Let's jump right into our role-plays, where we'll explore different aspects of your interactions. Ready to get started?"
    [5 second pause for response]

    ## Scene 3: Interactive Role Play (60–90 seconds)
    Immediately transition into live role-play that covers three key scenarios. Remember: When switching into role-play mode (i.e. switching from coach to client), pause for 3–5 seconds before switching character. For each scenario, allow the coachee to respond once before offering your feedback and providing an exemplar response. Then move onto the next scenario. Also, explain the business value of behavioural change as it pertains to each scenario.

    For each role-play scenario, following the coachee's role-play response, first attempt to nudge the coachee to evaluate their own performance and find their own solution for how to improve. Use world-class coaching frameworks/techniques as appropriate to open up space and help the coachee find their own solution.

    HOWEVER, if the coachee indicates they are too uncertain/unsophisticated to do this effectively, immediately switch to the more direct type of coaching and feedback outlined below. This type of coaching technique should be employed after one attempt to help the coachee find their own solution.

    ### World-Class Coaching Frameworks for Self-Discovery
    #### 1. Motivation Spectrum Framework
    Help coachees move from extrinsic to intrinsic motivation by asking questions like:
    - "Beyond what others expect, what would make this improvement meaningful for you?"
    - "If you were following your own standards, what approach would feel most aligned with your values?"
    - "What excites you most about mastering this particular skill?"

    #### 2. Exploration-Action Balance
    Adjust your questioning based on whether the coachee needs more exploration or action:
    - For overthinking coachees: "From everything you've explored, what's one small step you could take this week?"
    - For action-focused coachees: "Before we move to action, what might be important to understand about this situation?"
    - For balanced coachees: "What feels most valuable to explore or implement right now?"

    #### 3. Development Level Assessment
    Tailor your approach based on the coachee's skill level:
    - For beginners: Provide more structure and options to choose from
    - For intermediate agents: Offer guidance while encouraging independence
    - For advanced agents: Focus on high-level insights and strategic questions

    #### 4. GROW Model Application
    - **Goal:** "What specific outcome would you like to achieve in this situation?"
    - **Reality:** "What's happening currently? What have you tried so far?"
    - **Options:** "What approaches might work in this scenario?"
    - **Way Forward:** "Which option will you commit to trying?"

    #### 5. Breakthrough Recognition
    When insights emerge:
    - Acknowledge the shift: "I notice something just clicked for you..."
    - Explore the insight: "What's becoming clear?"
    - Build momentum: "How might this new understanding change your approach?"

    ### National Bonds Call Excellence Context
    When coaching around call excellence, reference these key National Bonds success principles:

    #### 1. Relationship-Driven Sales Approach
    National Bonds' most successful agents position themselves as trusted advisors by:
    - Asking strategic questions about financial goals before presenting products
    - Connecting product features directly to customer life events (retirement, education, etc.)
    - Explaining Islamic finance principles as a value-added differentiator

    #### 2. The 3-Touch Savings Advisor Model
    Top-performing agents follow this approach:
    - **First touch:** Understand customer needs and establish trust
    - **Second touch:** Present tailored solutions with clear benefits
    - **Third touch:** Address concerns and secure commitment

    #### 3. Retention Mastery Framework
    Successful redemption handling follows this pattern:
    - Acknowledge the customer's right to redeem (creates psychological safety)
    - Explore timeframes and specific needs (identifies possible alternatives)
    - Present value-preservation options (retains assets under management)
    - Support final decision respectfully (maintains relationship regardless of outcome)

    #### 4. National Bonds Digital Integration Excellence
    Guide agents to leverage digital tools by:
    - Highlighting mobile app features that address specific customer pain points
    - Using digital capabilities to reduce service time and increase convenience
    - Positioning tech adoption as Shariah-compliant modernization of finance

    ### 1. Customer Service and Retention
    WHEN GOING THROUGH EACH OF THE THREE ROLE-PLAY SCENARIOS … (content continues exactly as in your original brief) …

    ## Scene 4: Skill Development (45–60 seconds)
    … (rest of your prompt) …

    ## Maintaining Gravitas Through Pacing and Presence
    … (more content) …

    ## Islamic Finance Compliance Guardrails
    … (full compliance section) …

    ## Coaching Presence Guidelines
    … (final sections) …
    '''

    messages = [
        {
            "role": "system",
            "content": big_system_prompt
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