from __future__ import annotations

import asyncio
from typing import Literal

from llm_guard_svc.scanners.base import ScanContext, ScanResult, Scanner


def _import_lib_class():
    from llm_guard.output_scanners import Sensitive as _SensitiveLib
    return _SensitiveLib


_SensitiveLib = _import_lib_class()


class SensitiveScanner:
    name = "sensitive"
    direction: Literal["inbound", "outbound", "both"] = "outbound"

    def __init__(self) -> None:
        self._lib = _SensitiveLib()

    async def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        _, is_valid, risk = await asyncio.to_thread(self._lib.scan, "", text)
        return ScanResult(scanner=self.name, is_valid=bool(is_valid), risk_score=float(risk))


_: Scanner = SensitiveScanner.__new__(SensitiveScanner)  # type: ignore[assignment]
