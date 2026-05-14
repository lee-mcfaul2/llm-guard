from __future__ import annotations

from pathlib import Path


FIXTURE_PII = str(Path(__file__).parent.parent / "fixtures" / "pii-types.json")


def test_create_app_imports(monkeypatch):
    # Avoid loading the real ML scanners by restricting the enabled set
    # to regex-only backstops.
    monkeypatch.setenv("LLM_GUARD_PII_TYPES_PATH", FIXTURE_PII)
    monkeypatch.setenv("LLM_GUARD_INBOUND_SCANNERS", "ban_substrings,secrets")
    monkeypatch.setenv("LLM_GUARD_OUTBOUND_SCANNERS", "secrets")
    from llm_guard_svc.server import create_app
    app = create_app()
    assert app is not None


def test_main_module_importable():
    import llm_guard_svc.__main__  # noqa: F401
