"""Entry point for the voice pipeline demo."""
from __future__ import annotations

from .pipecat_pipeline import create_pipeline, run_server


def main() -> None:
    services = create_pipeline()
    print("Services created. Starting server...")
    import asyncio
    asyncio.run(run_server(services))


if __name__ == "__main__":
    main()
