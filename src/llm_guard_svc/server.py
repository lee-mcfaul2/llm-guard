"""FastAPI app factory + lifespan that loads scanner models."""
from __future__ import annotations

import threading
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from llm_guard_svc.config import Settings
from llm_guard_svc.obs.logging import get_logger
from llm_guard_svc.obs.metrics import (
    LLM_GUARD_MODEL_LOAD_DURATION_SECONDS,
    LLM_GUARD_MODELS_LOADED,
)
from llm_guard_svc.routes import Deps, make_router
from llm_guard_svc.scanners.registry import build_registry

log = get_logger("llm_guard_svc.server")


def _thresholds_from(settings: Settings) -> dict[str, float]:
    return {
        "prompt_injection": settings.prompt_injection_block_threshold,
        "secrets": settings.secrets_block_threshold,
        "toxicity": settings.toxicity_block_threshold,
        "ban_topics": settings.ban_topics_block_threshold,
        "malicious_urls": settings.malicious_urls_block_threshold,
        "sensitive": settings.sensitive_block_threshold,
        "ban_substrings": 1.0,  # regex hits are deterministic
    }


def create_app() -> FastAPI:
    settings = Settings()
    models_loaded = threading.Event()

    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
        log.info("startup", inbound=settings.inbound_scanners, outbound=settings.outbound_scanners)
        t0 = time.monotonic()
        registry = build_registry(settings)
        load_duration = time.monotonic() - t0
        LLM_GUARD_MODEL_LOAD_DURATION_SECONDS.observe(load_duration)
        LLM_GUARD_MODELS_LOADED.set(1)
        models_loaded.set()
        log.info("ready", load_seconds=round(load_duration, 2))

        deps = Deps(
            registry=registry,
            thresholds=_thresholds_from(settings),
            models_loaded_event=models_loaded,
        )
        app.include_router(make_router(deps))
        yield
        log.info("shutdown")

    return FastAPI(lifespan=_lifespan)
