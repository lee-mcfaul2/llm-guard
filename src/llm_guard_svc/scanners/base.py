"""Shared types for scanner adapters.

Each scanner exposes a coroutine `scan(text, ctx) -> ScanResult`. The registry
runs all enabled scanners in parallel, then verdict.aggregate maps the per-scanner
results to a final (action, categories, spans) tuple.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol


@dataclass(frozen=True)
class ScanContext:
    request_uuid: str
    direction: Literal["inbound", "outbound"]
    mcp: str = ""
    tool: str = ""


@dataclass(frozen=True)
class Span:
    category: str
    start: int
    end: int
    scanner: str


@dataclass(frozen=True)
class ScanResult:
    scanner: str
    is_valid: bool
    risk_score: float
    spans: list[Span] = field(default_factory=list)


class Scanner(Protocol):
    name: str
    direction: Literal["inbound", "outbound", "both"]

    async def scan(self, text: str, ctx: ScanContext) -> ScanResult: ...
