"""Prometheus metrics catalog.

Naming convention: snake_case with `llm_guard_` prefix.
All metrics use a dedicated CollectorRegistry so unit tests can exercise them
without polluting the default registry.
"""
from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

REGISTRY = CollectorRegistry()


LLM_GUARD_REQUESTS_TOTAL = Counter(
    "llm_guard_requests_total",
    "Scan requests served, by direction and final action.",
    labelnames=("direction", "action"),
    registry=REGISTRY,
)

LLM_GUARD_REQUEST_DURATION_SECONDS = Histogram(
    "llm_guard_request_duration_seconds",
    "End-to-end /scan latency.",
    labelnames=("direction",),
    buckets=(0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
    registry=REGISTRY,
)

LLM_GUARD_SCANNER_DURATION_SECONDS = Histogram(
    "llm_guard_scanner_duration_seconds",
    "Per-scanner duration (one observation per scanner per request).",
    labelnames=("scanner", "direction"),
    buckets=(0.005, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
    registry=REGISTRY,
)

LLM_GUARD_SCANNER_HITS_TOTAL = Counter(
    "llm_guard_scanner_hits_total",
    "Per-scanner detection hits — when is_valid=False, regardless of risk_score.",
    labelnames=("scanner", "direction"),
    registry=REGISTRY,
)

LLM_GUARD_SCANNER_ERRORS_TOTAL = Counter(
    "llm_guard_scanner_errors_total",
    "Per-scanner internal failures — paging-class.",
    labelnames=("scanner", "direction", "reason"),
    registry=REGISTRY,
)

LLM_GUARD_MODELS_LOADED = Gauge(
    "llm_guard_models_loaded",
    "1 once all configured ML scanners are loaded; 0 during cold start.",
    registry=REGISTRY,
)

LLM_GUARD_MODEL_LOAD_DURATION_SECONDS = Histogram(
    "llm_guard_model_load_duration_seconds",
    "Total time to load all ML models at process start.",
    buckets=(1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0),
    registry=REGISTRY,
)


def render_text() -> bytes:
    return generate_latest(REGISTRY)
