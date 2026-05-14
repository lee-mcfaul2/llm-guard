from __future__ import annotations

import threading
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from llm_guard_svc.routes import Deps, make_router


def _event(set_: bool):
    e = threading.Event()
    if set_:
        e.set()
    return e


def _deps(models_loaded: bool = True) -> Deps:
    return Deps(
        registry=MagicMock(),
        thresholds={},
        models_loaded_event=_event(models_loaded),
    )


def test_healthz_always_200():
    app = FastAPI()
    app.include_router(make_router(_deps(models_loaded=False)))
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_readyz_503_before_models_loaded():
    app = FastAPI()
    app.include_router(make_router(_deps(models_loaded=False)))
    client = TestClient(app)
    r = client.get("/readyz")
    assert r.status_code == 503


def test_readyz_200_after_models_loaded():
    app = FastAPI()
    app.include_router(make_router(_deps(models_loaded=True)))
    client = TestClient(app)
    r = client.get("/readyz")
    assert r.status_code == 200


def test_metrics_returns_prometheus_text():
    app = FastAPI()
    app.include_router(make_router(_deps()))
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "llm_guard_requests_total" in r.text
