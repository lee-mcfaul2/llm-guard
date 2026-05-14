"""FastAPI routes for /healthz, /readyz, /metrics.

/scan is added in Task 9. Keep this module minimal for now so the health checks
can be tested in isolation.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, HTTPException, Response

from llm_guard_svc.obs.metrics import render_text
from llm_guard_svc.scanners.registry import Registry


@dataclass(frozen=True)
class Deps:
    registry: Registry | Any
    thresholds: dict[str, float]
    models_loaded_event: threading.Event


def make_router(deps: Deps) -> APIRouter:
    router = APIRouter()

    @router.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/readyz")
    async def readyz() -> dict[str, str]:
        if not deps.models_loaded_event.is_set():
            raise HTTPException(status_code=503, detail="models not loaded")
        return {"status": "ok"}

    @router.get("/metrics")
    async def metrics() -> Response:
        return Response(content=render_text(), media_type="text/plain; version=0.0.4")

    return router
