"""Entry point for the voice pipeline demo."""
from __future__ import annotations

from .pipecat_pipeline import create_pipeline
from .websocket_server import main as websocket_server_main


def main() -> None:
    # Create pipeline early so the model loads on startup
    create_pipeline()
    websocket_server_main()


if __name__ == "__main__":
    main()
