"""uvicorn entrypoint: python -m llm_guard_svc"""
from __future__ import annotations

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "llm_guard_svc.server:create_app",
        host="0.0.0.0",  # noqa: S104 # nosec B104 — service is mesh-protected inbound
        port=int(os.environ.get("LLM_GUARD_PORT", "8080")),
        factory=True,
        log_level="warning",  # we have our own JSONL logger
    )


if __name__ == "__main__":
    main()
