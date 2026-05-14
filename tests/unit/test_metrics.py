from __future__ import annotations


def test_all_metrics_exist():
    from llm_guard_svc.obs.metrics import (
        LLM_GUARD_REQUESTS_TOTAL,
        LLM_GUARD_REQUEST_DURATION_SECONDS,
        LLM_GUARD_SCANNER_DURATION_SECONDS,
        LLM_GUARD_SCANNER_HITS_TOTAL,
        LLM_GUARD_SCANNER_ERRORS_TOTAL,
        LLM_GUARD_MODELS_LOADED,
        LLM_GUARD_MODEL_LOAD_DURATION_SECONDS,
    )

    LLM_GUARD_REQUESTS_TOTAL.labels(direction="inbound", action="allow").inc()
    LLM_GUARD_REQUEST_DURATION_SECONDS.labels(direction="inbound").observe(0.05)
    LLM_GUARD_SCANNER_DURATION_SECONDS.labels(scanner="x", direction="inbound").observe(0.01)
    LLM_GUARD_SCANNER_HITS_TOTAL.labels(scanner="x", direction="inbound").inc()
    LLM_GUARD_SCANNER_ERRORS_TOTAL.labels(scanner="x", direction="inbound", reason="boom").inc()
    LLM_GUARD_MODELS_LOADED.set(1)
    LLM_GUARD_MODEL_LOAD_DURATION_SECONDS.observe(8.2)


def test_render_text_returns_bytes():
    from llm_guard_svc.obs.metrics import render_text
    out = render_text()
    assert isinstance(out, bytes)
    assert b"llm_guard_requests_total" in out
