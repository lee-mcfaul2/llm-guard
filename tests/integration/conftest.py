from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def fixture_pii_path() -> str:
    return str(Path(__file__).parent.parent / "fixtures" / "pii-types.json")


@pytest.fixture(scope="session", autouse=True)
def _baseline_env(fixture_pii_path: str) -> None:
    os.environ["LLM_GUARD_PII_TYPES_PATH"] = fixture_pii_path
