"""PromptInjection scanner — wraps llm-guard's PromptInjection input scanner.

The installed llm-guard (0.3.16) ships PromptInjection only as an input scanner.
We use it for both directions: prompt injection in user inputs AND in MCP/tool
responses uses the same underlying classifier model.

Library loading happens at module import (`_InboundLib`/`_OutboundLib`) and is
patchable by unit tests so we don't pay the ~5-15s model-load cost in CI.
Instance construction calls `_InboundLib()`/`_OutboundLib()` which DOES load the
models — that's intentional, callers (the registry) build once per process.

`_OutboundLib` is an alias for `_InboundLib`; kept as a separate name so the
unit-test mock pattern (`patch("...prompt_injection._OutboundLib", ...)`) remains
valid and the two scanner instances remain independently mockable.
"""
from __future__ import annotations

import asyncio
from typing import Any, Literal

from llm_guard_svc.scanners.base import ScanContext, Scanner, ScanResult


def _import_lib_classes() -> tuple[Any, Any]:
    from llm_guard.input_scanners import (  # type: ignore[import-untyped]
        PromptInjection as _InboundLib,
    )
    # llm-guard 0.3.x has no output-side PromptInjection; use the same
    # input-scanner class for outbound — same model, same API.
    _OutboundLib = _InboundLib
    return _InboundLib, _OutboundLib


_InboundLib, _OutboundLib = _import_lib_classes()


class PromptInjectionScanner:
    name = "prompt_injection"
    direction: Literal["inbound", "outbound", "both"] = "both"

    def __init__(self) -> None:
        self._inbound = _InboundLib()
        self._outbound = _OutboundLib()

    async def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        # llm-guard's scan() is sync + GIL-bound; run in a thread so the
        # asyncio loop is free for other scanners running in parallel.
        if ctx.direction == "inbound":
            _, is_valid, risk = await asyncio.to_thread(self._inbound.scan, text)
        else:
            # Outbound: scan the MCP/tool response text for injected instructions.
            # Input-scanner API: scan(prompt) -> (sanitized, is_valid, risk_score).
            _, is_valid, risk = await asyncio.to_thread(self._outbound.scan, text)
        return ScanResult(
            scanner=self.name,
            is_valid=bool(is_valid),
            risk_score=float(risk),
        )


_: Scanner = PromptInjectionScanner.__new__(PromptInjectionScanner)  # structural conformance check
