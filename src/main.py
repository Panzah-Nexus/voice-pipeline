"""Entry point for the air-gapped voice pipeline demo."""


import asyncio
from fastapi import FastAPI, WebSocket
from pipecat.pipeline.runner import PipelineRunner                    # task runner :contentReference[oaicite:8]{index=8}
from pipecat.pipeline.task import PipelineTask

from .pipecat_pipeline import build_pipeline

app = FastAPI(title="Air-gapped Voice AI")

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):                          # FastAPI WebSocket transport :contentReference[oaicite:9]{index=9}
    await ws.accept()
    pipeline = build_pipeline(ws)
    task = PipelineTask(pipeline)
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
