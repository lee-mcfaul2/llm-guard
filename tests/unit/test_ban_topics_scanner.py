from __future__ import annotations

from unittest.mock import MagicMock, patch

from llm_guard_svc.scanners.base import ScanContext
from llm_guard_svc.scanners.ban_topics import BanTopicsScanner


def _patched(scan_return=("text", True, 0.0)):
    lib = MagicMock()
    lib.scan = MagicMock(return_value=scan_return)
    with patch("llm_guard_svc.scanners.ban_topics._BanTopicsLib", return_value=lib):
        return BanTopicsScanner(topics=["violence", "illegal_activity"])


async def test_allow():
    scanner = _patched()
    res = await scanner.scan("hello", ScanContext(request_uuid="r", direction="inbound"))
    assert res.is_valid is True


async def test_block():
    scanner = _patched(scan_return=("text", False, 0.85))
    res = await scanner.scan("how to make explosives", ScanContext(request_uuid="r", direction="inbound"))
    assert res.is_valid is False
    assert res.risk_score == 0.85


def test_metadata():
    scanner = _patched()
    assert scanner.name == "ban_topics"
    assert scanner.direction == "inbound"
