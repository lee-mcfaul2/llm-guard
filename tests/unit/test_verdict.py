from __future__ import annotations

from llm_guard_svc.scanners.base import ScanResult, Span
from llm_guard_svc.verdict import aggregate


def test_all_pass_means_allow():
    results = [
        ScanResult(scanner="a", is_valid=True, risk_score=0.0),
        ScanResult(scanner="b", is_valid=True, risk_score=0.0),
    ]
    action, categories, spans = aggregate(results, {"a": 0.7, "b": 0.7})
    assert action == "allow"
    assert categories == []
    assert spans == []


def test_high_score_blocks():
    results = [
        ScanResult(scanner="a", is_valid=False, risk_score=0.9, spans=[Span("a", 0, 5, "a")]),
    ]
    action, categories, spans = aggregate(results, {"a": 0.7})
    assert action == "block"
    assert "a" in categories
    assert len(spans) == 1


def test_low_score_flags():
    results = [
        ScanResult(scanner="a", is_valid=False, risk_score=0.4),
    ]
    action, categories, _ = aggregate(results, {"a": 0.7})
    assert action == "flag"
    assert "a" in categories


def test_block_dominates_flag():
    results = [
        ScanResult(scanner="a", is_valid=False, risk_score=0.4),
        ScanResult(scanner="b", is_valid=False, risk_score=0.9),
    ]
    action, categories, _ = aggregate(results, {"a": 0.7, "b": 0.7})
    assert action == "block"
    assert set(categories) == {"a", "b"}


def test_missing_threshold_defaults_to_one():
    results = [
        ScanResult(scanner="a", is_valid=False, risk_score=0.99),
    ]
    action, _, _ = aggregate(results, {})
    assert action == "flag"


def test_categories_deduplicated():
    results = [
        ScanResult(scanner="a", is_valid=False, risk_score=0.9, spans=[Span("a", 0, 1, "a")]),
        ScanResult(scanner="a", is_valid=False, risk_score=0.95, spans=[Span("a", 2, 3, "a")]),
    ]
    _, categories, spans = aggregate(results, {"a": 0.7})
    assert categories == ["a"]
    assert len(spans) == 2
