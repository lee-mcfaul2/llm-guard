"""Secrets scanner.

For v0.1 we use ONLY the regex backstop (SECRET kind from pii-types.json).
The llm-guard library's Secrets scanner has overlapping coverage and adds
significant init cost; the regex backstops cover the high-precision cases
(AWS keys, etc.). We can layer the library scanner in later if we observe
false negatives.
"""
from __future__ import annotations

from typing import Literal

from llm_guard_svc.scanners.base import ScanContext, Scanner, ScanResult, Span
from llm_guard_svc.shared.categories import load_categories


class SecretsScanner:
    name = "secrets"
    direction: Literal["inbound", "outbound", "both"] = "both"

    def __init__(self, pii_types_path: str) -> None:
        self._categories = load_categories(pii_types_path, kinds={"SECRET"})

    async def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        spans: list[Span] = []
        for cat in self._categories:
            for m in cat.pattern.finditer(text):
                spans.append(Span(
                    category=cat.name,
                    start=m.start(),
                    end=m.end(),
                    scanner=self.name,
                ))
        if not spans:
            return ScanResult(scanner=self.name, is_valid=True, risk_score=0.0)
        return ScanResult(scanner=self.name, is_valid=False, risk_score=1.0, spans=spans)


_: Scanner = SecretsScanner.__new__(SecretsScanner)  # structural conformance check
