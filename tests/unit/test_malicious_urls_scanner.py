from __future__ import annotations

from unittest.mock import MagicMock, patch

from llm_guard_svc.scanners.base import ScanContext
from llm_guard_svc.scanners.malicious_urls import MaliciousURLsScanner


def _patched(scan_return=("text", True, 0.0)):
    lib = MagicMock()
    lib.scan = MagicMock(return_value=scan_return)
    with patch("llm_guard_svc.scanners.malicious_urls._MaliciousURLsLib", return_value=lib):
        return MaliciousURLsScanner(timeout_seconds=0.5)


async def test_allow():
    scanner = _patched()
    res = await scanner.scan(
        "text without urls",
        ScanContext(request_uuid="r", direction="outbound", mcp="kb", tool="s"),
    )
    assert res.is_valid is True


async def test_block_high_risk():
    scanner = _patched(scan_return=("text", False, 0.95))
    res = await scanner.scan(
        "click http://evil.example/",
        ScanContext(request_uuid="r", direction="outbound"),
    )
    assert res.is_valid is False
    assert res.risk_score == 0.95


def test_metadata():
    scanner = _patched()
    assert scanner.name == "malicious_urls"
    assert scanner.direction == "outbound"
