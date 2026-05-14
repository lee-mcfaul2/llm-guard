from __future__ import annotations

from unittest.mock import MagicMock, patch

from llm_guard_svc.scanners.base import ScanContext
from llm_guard_svc.scanners.toxicity import ToxicityScanner


def _patched(scan_return=("text", True, 0.0)):
    lib = MagicMock()
    lib.scan = MagicMock(return_value=scan_return)
    with patch("llm_guard_svc.scanners.toxicity._ToxicityLib", return_value=lib):
        return ToxicityScanner()


async def test_allow():
    scanner = _patched(scan_return=("text", True, 0.0))
    res = await scanner.scan("hello", ScanContext(request_uuid="r", direction="inbound"))
    assert res.is_valid is True


async def test_block():
    scanner = _patched(scan_return=("text", False, 0.9))
    res = await scanner.scan("toxic content", ScanContext(request_uuid="r", direction="inbound"))
    assert res.is_valid is False
    assert res.risk_score == 0.9


def test_metadata():
    scanner = _patched()
    assert scanner.name == "toxicity"
    assert scanner.direction == "inbound"
