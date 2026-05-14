from __future__ import annotations

import pytest


def test_defaults(monkeypatch):
    monkeypatch.delenv("LLM_GUARD_INBOUND_SCANNERS", raising=False)
    monkeypatch.delenv("LLM_GUARD_OUTBOUND_SCANNERS", raising=False)
    monkeypatch.setenv("LLM_GUARD_PII_TYPES_PATH", "/tmp/pii.json")
    from llm_guard_svc.config import Settings
    s = Settings()
    assert s.port == 8080
    assert "prompt_injection" in s.inbound_scanners
    assert "secrets" in s.outbound_scanners
    assert s.prompt_injection_block_threshold == 0.7


def test_csv_parsed_into_list(monkeypatch):
    monkeypatch.setenv("LLM_GUARD_INBOUND_SCANNERS", "prompt_injection,secrets")
    monkeypatch.setenv("LLM_GUARD_PII_TYPES_PATH", "/tmp/pii.json")
    from llm_guard_svc.config import Settings
    s = Settings()
    assert s.inbound_scanners == ["prompt_injection", "secrets"]


def test_thresholds_override(monkeypatch):
    monkeypatch.setenv("LLM_GUARD_PROMPT_INJECTION_BLOCK_THRESHOLD", "0.9")
    monkeypatch.setenv("LLM_GUARD_PII_TYPES_PATH", "/tmp/pii.json")
    from llm_guard_svc.config import Settings
    s = Settings()
    assert s.prompt_injection_block_threshold == pytest.approx(0.9)


def test_ban_topics_csv(monkeypatch):
    monkeypatch.setenv("LLM_GUARD_BAN_TOPICS", "violence,illegal_activity,self_harm")
    monkeypatch.setenv("LLM_GUARD_PII_TYPES_PATH", "/tmp/pii.json")
    from llm_guard_svc.config import Settings
    s = Settings()
    assert s.ban_topics == ["violence", "illegal_activity", "self_harm"]


def test_pii_types_path_required_when_backstop_enabled(monkeypatch):
    monkeypatch.delenv("LLM_GUARD_PII_TYPES_PATH", raising=False)
    monkeypatch.setenv("LLM_GUARD_INBOUND_SCANNERS", "ban_substrings")
    monkeypatch.setenv("LLM_GUARD_OUTBOUND_SCANNERS", "")
    from llm_guard_svc.config import Settings
    with pytest.raises(ValueError, match="LLM_GUARD_PII_TYPES_PATH"):
        Settings()
