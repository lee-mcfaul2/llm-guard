from __future__ import annotations

import asyncio
from typing import Any, Literal

from llm_guard_svc.scanners.base import ScanContext, Scanner, ScanResult


def _import_lib_class() -> Any:
    from llm_guard.input_scanners import Toxicity as _ToxicityLib  # type: ignore[import-untyped]
    return _ToxicityLib


_ToxicityLib = _import_lib_class()


class ToxicityScanner:
    name = "toxicity"
    direction: Literal["inbound", "outbound", "both"] = "inbound"

    def __init__(self) -> None:
        self._lib = _ToxicityLib()

    async def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        _, is_valid, risk = await asyncio.to_thread(self._lib.scan, text)
        return ScanResult(scanner=self.name, is_valid=bool(is_valid), risk_score=float(risk))


_: Scanner = ToxicityScanner.__new__(ToxicityScanner)  # structural conformance check
