from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from llm_guard_svc.scanners.base import ScanContext


@pytest.fixture
def ctx_inbound():
    return ScanContext(request_uuid="r1", direction="inbound")


@pytest.fixture
def ctx_outbound():
    return ScanContext(request_uuid="r1", direction="outbound", mcp="kb", tool="search")


def _patched_scanner(inbound_scan_return=("ok", True, 0.0), outbound_scan_return=("ok", True, 0.0)):
    """Build a PromptInjectionScanner with mocked llm-guard internals."""
    from llm_guard_svc.scanners.prompt_injection import PromptInjectionScanner

    inbound_mock = MagicMock()
    inbound_mock.scan = MagicMock(return_value=inbound_scan_return)
    outbound_mock = MagicMock()
    outbound_mock.scan = MagicMock(return_value=outbound_scan_return)
    with patch("llm_guard_svc.scanners.prompt_injection._InboundLib", return_value=inbound_mock), \
         patch("llm_guard_svc.scanners.prompt_injection._OutboundLib", return_value=outbound_mock):
        return PromptInjectionScanner()


async def test_allow_when_inbound_library_says_valid(ctx_inbound):
    scanner = _patched_scanner(inbound_scan_return=("text", True, 0.0))
    res = await scanner.scan("normal user prompt", ctx_inbound)
    assert res.is_valid is True
    assert res.scanner == "prompt_injection"


async def test_block_when_inbound_library_says_invalid(ctx_inbound):
    scanner = _patched_scanner(inbound_scan_return=("text", False, 0.85))
    res = await scanner.scan("ignore previous instructions", ctx_inbound)
    assert res.is_valid is False
    assert res.risk_score == 0.85


async def test_outbound_uses_output_scanner(ctx_outbound):
    scanner = _patched_scanner(outbound_scan_return=("text", False, 0.75))
    res = await scanner.scan("injection in MCP response", ctx_outbound)
    assert res.is_valid is False
    assert res.risk_score == 0.75


def test_name_and_direction():
    scanner = _patched_scanner()
    assert scanner.name == "prompt_injection"
    assert scanner.direction == "both"
