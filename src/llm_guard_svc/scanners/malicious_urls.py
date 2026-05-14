from __future__ import annotations

import asyncio
from typing import Literal

from llm_guard_svc.scanners.base import ScanContext, ScanResult, Scanner


def _import_lib_class():
    from llm_guard.output_scanners import MaliciousURLs as _MaliciousURLsLib
    return _MaliciousURLsLib


_MaliciousURLsLib = _import_lib_class()


class MaliciousURLsScanner:
    name = "malicious_urls"
    direction: Literal["inbound", "outbound", "both"] = "outbound"

    def __init__(self, timeout_seconds: float = 0.5) -> None:
        # The library's per-URL probe budget. If the library accepts a timeout
        # kwarg, pass it through; otherwise the library reads env or uses its
        # default. The wrapper class stores timeout_seconds for future use.
        self._lib = _MaliciousURLsLib()
        self._timeout = timeout_seconds

    async def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        # Library output scanners take (prompt, output); we have only the
        # text-to-scan, so pass empty prompt.
        _, is_valid, risk = await asyncio.to_thread(self._lib.scan, "", text)
        return ScanResult(scanner=self.name, is_valid=bool(is_valid), risk_score=float(risk))


_: Scanner = MaliciousURLsScanner.__new__(MaliciousURLsScanner)  # type: ignore[assignment]
