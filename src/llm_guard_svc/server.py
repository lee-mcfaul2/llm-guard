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


class _LazyRegistry:
    """Placeholder until the real Registry is built off-thread.

    `/healthz`, `/readyz`, and `/scan` are mounted at process start so the
    kubelet liveness/readiness probes get an HTTP answer immediately. Model
    loading (slow on a shared node, and potentially a runtime HuggingFace
    download) runs in a background thread; `for_direction` only ever gets
    called from `/scan`, which is gated behind `models_loaded_event` and so
    cannot reach a lazy registry.
    """

    def for_direction(self, direction: str) -> list:  # pragma: no cover - guarded by event
        raise RuntimeError("registry accessed before models finished loading")


def create_app() -> FastAPI:
    settings = Settings()
    models_loaded = threading.Event()

    # Deps is constructed up front with a placeholder registry. The router
    # (health/ready/metrics/scan) is included immediately so probes resolve
    # from t=0 instead of 404/502 while models load.
    deps = Deps(
        registry=_LazyRegistry(),
        thresholds=_thresholds_from(settings),
        models_loaded_event=models_loaded,
    )

    def _load_models() -> None:
        t0 = time.monotonic()
        registry = build_registry(settings)
        load_duration = time.monotonic() - t0
        # Swap the real registry in, then flip the readiness gate. /scan only
        # touches deps.registry after the event is set, so this ordering is safe.
        object.__setattr__(deps, "registry", registry)
        LLM_GUARD_MODEL_LOAD_DURATION_SECONDS.observe(load_duration)
        LLM_GUARD_MODELS_LOADED.set(1)
        models_loaded.set()
        log.info("ready", load_seconds=round(load_duration, 2))

    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
        log.info("startup", inbound=settings.inbound_scanners, outbound=settings.outbound_scanners)
        loader = threading.Thread(target=_load_models, name="model-loader", daemon=True)
        loader.start()
        yield
        log.info("shutdown")

    app = FastAPI(lifespan=_lifespan)
    app.include_router(make_router(deps))
    return app
