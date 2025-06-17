"""Entry point for the voice pipeline demo."""
from __future__ import annotations

from .pipecat_pipeline import create_pipeline


def main() -> None:
    pipeline = create_pipeline()
    # TODO: integrate with websocket server
    print("Pipeline created:", pipeline)


if __name__ == "__main__":
    main()
