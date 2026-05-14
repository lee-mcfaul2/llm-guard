from __future__ import annotations

from pathlib import Path

import pytest

from llm_guard_svc.shared.categories import load_categories

FIXTURE = Path(__file__).parent.parent / "fixtures" / "pii-types.json"


def test_load_all_categories():
    cats = load_categories(FIXTURE)
    assert len(cats) == 3
    by_name = {c.name: c for c in cats}
    assert "CODEWORD_PROJECT_BLUE" in by_name
    assert by_name["CODEWORD_PROJECT_BLUE"].kind == "CODEWORD"


def test_filter_by_kind():
    cats = load_categories(FIXTURE, kinds={"CODEWORD", "SECRET"})
    kinds = {c.kind for c in cats}
    assert kinds == {"CODEWORD", "SECRET"}


def test_compile_regex():
    cats = load_categories(FIXTURE)
    aws = next(c for c in cats if c.name == "SECRET_AWS_ACCESS_KEY")
    assert aws.pattern.search("AKIAIOSFODNN7EXAMPLE") is not None
    assert aws.pattern.search("hello world") is None


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_categories(Path("/tmp/definitely-not-there.json"))  # noqa: S108
