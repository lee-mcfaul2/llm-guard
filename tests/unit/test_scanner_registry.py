from __future__ import annotations

from pathlib import Path

import pytest

from llm_guard_svc.config import Settings
from llm_guard_svc.scanners.registry import build_registry

FIXTURE_PII = str(Path(__file__).parent.parent / "fixtures" / "pii-types.json")


def test_registry_with_only_ban_substrings(monkeypatch):
    monkeypatch.setenv("LLM_GUARD_PII_TYPES_PATH", FIXTURE_PII)
    monkeypatch.setenv("LLM_GUARD_INBOUND_SCANNERS", "ban_substrings")
    monkeypatch.setenv("LLM_GUARD_OUTBOUND_SCANNERS", "")
    settings = Settings()
    registry = build_registry(settings)
    inbound = registry.for_direction("inbound")
    assert len(inbound) == 1
    assert inbound[0].name == "ban_substrings"
    assert registry.for_direction("outbound") == []


def test_unknown_scanner_raises(monkeypatch):
    monkeypatch.setenv("LLM_GUARD_PII_TYPES_PATH", FIXTURE_PII)
    monkeypatch.setenv("LLM_GUARD_INBOUND_SCANNERS", "totally_not_a_scanner")
    monkeypatch.setenv("LLM_GUARD_OUTBOUND_SCANNERS", "")
    settings = Settings()
    with pytest.raises(ValueError, match="unknown scanner"):
        build_registry(settings)
