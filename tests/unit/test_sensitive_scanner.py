from __future__ import annotations

from unittest.mock import MagicMock, patch

from llm_guard_svc.scanners.base import ScanContext
from llm_guard_svc.scanners.sensitive import SensitiveScanner


def _patched(scan_return=("text", True, 0.0)):
    lib = MagicMock()
    lib.scan = MagicMock(return_value=scan_return)
    with patch("llm_guard_svc.scanners.sensitive._SensitiveLib", return_value=lib):
        return SensitiveScanner()


async def test_allow():
    scanner = _patched()
    res = await scanner.scan(
        "nothing sensitive",
        ScanContext(request_uuid="r", direction="outbound", mcp="kb", tool="s"),
    )
    assert res.is_valid is True


async def test_block_pii():
    scanner = _patched(scan_return=("text", False, 0.65))
    res = await scanner.scan(
        "SSN 123-45-6789",
        ScanContext(request_uuid="r", direction="outbound"),
    )
    assert res.is_valid is False


def test_metadata():
    scanner = _patched()
    assert scanner.name == "sensitive"
    assert scanner.direction == "outbound"
