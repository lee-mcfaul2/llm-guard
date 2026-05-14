"""Aggregate per-scanner results into a final (action, categories, spans).

Rules:
  - is_valid=True (no hit) → nothing
  - is_valid=False AND risk_score >= block_threshold → block
  - is_valid=False AND risk_score < block_threshold → flag
Final action is the highest-severity contribution: block > flag > allow.
Missing threshold defaults to 1.0 (treat as flag unless score is also 1.0).
"""
from __future__ import annotations

from typing import Literal

from llm_guard_svc.scanners.base import ScanResult, Span

Action = Literal["allow", "flag", "block"]


def aggregate(
    results: list[ScanResult],
    thresholds: dict[str, float],
) -> tuple[Action, list[str], list[Span]]:
    action: Action = "allow"
    categories_ordered: list[str] = []
    seen_categories: set[str] = set()
    spans: list[Span] = []

    for r in results:
        if r.is_valid:
            continue
        threshold = thresholds.get(r.scanner, 1.0)
        new_contribution: Action = "block" if r.risk_score >= threshold else "flag"
        if _severity(new_contribution) > _severity(action):
            action = new_contribution
        if r.scanner not in seen_categories:
            categories_ordered.append(r.scanner)
            seen_categories.add(r.scanner)
        spans.extend(r.spans)

    return action, categories_ordered, spans


def _severity(action: Action) -> int:
    return {"allow": 0, "flag": 1, "block": 2}[action]
