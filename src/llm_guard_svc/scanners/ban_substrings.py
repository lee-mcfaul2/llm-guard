"""BanSubstrings scanner — regex-based backstop sourced from lib-agent-prompt
shared categories (CODEWORD and SECRET kinds only; PII is handled by upstream
tokenization in the gateway).

Returns risk_score=1.0 on any hit (regex matches are deterministic).
"""
from __future__ import annotations

from typing import Literal

from llm_guard_svc.scanners.base import ScanContext, ScanResult, Scanner, Span
from llm_guard_svc.shared.categories import load_categories


class BanSubstringsScanner:
    name = "ban_substrings"
    direction: Literal["inbound", "outbound", "both"] = "inbound"

    def __init__(self, pii_types_path: str) -> None:
        self._categories = load_categories(pii_types_path, kinds={"CODEWORD", "SECRET"})

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


_: Scanner = BanSubstringsScanner.__new__(BanSubstringsScanner)  # type: ignore[assignment]
