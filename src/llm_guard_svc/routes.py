"""FastAPI routes for /healthz, /readyz, /metrics, /scan."""
from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from llm_guard_svc.obs.logging import get_logger
from llm_guard_svc.obs.metrics import (
    LLM_GUARD_REQUEST_DURATION_SECONDS,
    LLM_GUARD_REQUESTS_TOTAL,
    LLM_GUARD_SCANNER_DURATION_SECONDS,
    LLM_GUARD_SCANNER_ERRORS_TOTAL,
    LLM_GUARD_SCANNER_HITS_TOTAL,
    render_text,
)
from llm_guard_svc.scanners.base import ScanContext, ScanResult
from llm_guard_svc.scanners.registry import Registry
from llm_guard_svc.verdict import aggregate

log = get_logger("llm_guard_svc.routes")


@dataclass(frozen=True)
class Deps:
    registry: Registry | Any
    thresholds: dict[str, float]
    models_loaded_event: threading.Event


class ScanRequest(BaseModel):
    text: str
    request_uuid: str
    direction: Literal["inbound", "outbound"]
    mcp: str = ""
    tool: str = ""


class ScanSpan(BaseModel):
    category: str
    start: int
    end: int
    scanner: str


class ScanResponse(BaseModel):
    action: Literal["allow", "flag", "block"]
    categories: list[str] = Field(default_factory=list)
    spans: list[ScanSpan] = Field(default_factory=list)


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

    @router.post("/scan")
    async def scan(req: ScanRequest) -> ScanResponse:
        if not deps.models_loaded_event.is_set():
            log.warning("scan_before_ready", request_uuid=req.request_uuid)
            raise HTTPException(status_code=503, detail={"error": "NOT_READY"})

        scanners = deps.registry.for_direction(req.direction)
        ctx = ScanContext(
            request_uuid=req.request_uuid,
            direction=req.direction,
            mcp=req.mcp,
            tool=req.tool,
        )
        request_start = time.monotonic()

        async def _run_one(scanner) -> ScanResult:
            t0 = time.monotonic()
            try:
                result = await scanner.scan(req.text, ctx)
            except Exception as exc:
                LLM_GUARD_SCANNER_ERRORS_TOTAL.labels(
                    scanner=scanner.name, direction=req.direction, reason=type(exc).__name__,
                ).inc()
                log.error(
                    "scanner_failed",
                    scanner=scanner.name,
                    request_uuid=req.request_uuid,
                    err=str(exc),
                )
                raise
            duration = time.monotonic() - t0
            LLM_GUARD_SCANNER_DURATION_SECONDS.labels(
                scanner=scanner.name, direction=req.direction,
            ).observe(duration)
            if not result.is_valid:
                LLM_GUARD_SCANNER_HITS_TOTAL.labels(
                    scanner=scanner.name, direction=req.direction,
                ).inc()
            return result

        try:
            results = await asyncio.gather(*(_run_one(s) for s in scanners))
        except Exception as exc:
            log.error("scan_failed", request_uuid=req.request_uuid, err=str(exc))
            raise HTTPException(status_code=500, detail={"error": "SCANNER_ERROR"}) from exc

        action, categories, spans = aggregate(list(results), deps.thresholds)

        duration = time.monotonic() - request_start
        LLM_GUARD_REQUEST_DURATION_SECONDS.labels(direction=req.direction).observe(duration)
        LLM_GUARD_REQUESTS_TOTAL.labels(direction=req.direction, action=action).inc()

        log.info(
            "scan",
            request_uuid=req.request_uuid,
            direction=req.direction,
            mcp=req.mcp or None,
            tool=req.tool or None,
            action=action,
            categories=categories,
            duration_ms=round(duration * 1000),
        )

        return ScanResponse(
            action=action,
            categories=categories,
            spans=[ScanSpan(**asdict(s)) for s in spans],
        )

    return router
