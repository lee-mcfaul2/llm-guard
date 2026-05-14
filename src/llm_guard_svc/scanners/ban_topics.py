from __future__ import annotations

import asyncio
from typing import Literal

from llm_guard_svc.scanners.base import ScanContext, ScanResult, Scanner


def _import_lib_class():
    from llm_guard.input_scanners import BanTopics as _BanTopicsLib
    return _BanTopicsLib


_BanTopicsLib = _import_lib_class()


class BanTopicsScanner:
    name = "ban_topics"
    direction: Literal["inbound", "outbound", "both"] = "inbound"

    def __init__(self, topics: list[str]) -> None:
        self._lib = _BanTopicsLib(topics=topics)

    async def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        _, is_valid, risk = await asyncio.to_thread(self._lib.scan, text)
        return ScanResult(scanner=self.name, is_valid=bool(is_valid), risk_score=float(risk))


_: Scanner = BanTopicsScanner.__new__(BanTopicsScanner)  # type: ignore[assignment]
