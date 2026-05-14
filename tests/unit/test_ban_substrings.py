from __future__ import annotations

from pathlib import Path

import pytest

from llm_guard_svc.scanners.ban_substrings import BanSubstringsScanner
from llm_guard_svc.scanners.base import ScanContext

FIXTURE = Path(__file__).parent.parent / "fixtures" / "pii-types.json"


@pytest.fixture
def scanner() -> BanSubstringsScanner:
    return BanSubstringsScanner(pii_types_path=str(FIXTURE))


@pytest.fixture
def ctx() -> ScanContext:
    return ScanContext(request_uuid="r1", direction="inbound")


async def test_no_hit_is_valid(scanner: BanSubstringsScanner, ctx: ScanContext) -> None:
    res = await scanner.scan("nothing to see here", ctx)
    assert res.is_valid is True
    assert res.risk_score == 0.0
    assert res.spans == []


async def test_codeword_hit(scanner: BanSubstringsScanner, ctx: ScanContext) -> None:
    res = await scanner.scan("leaked PROJECT_BLUE_ALPHA1 yesterday", ctx)
    assert res.is_valid is False
    assert res.risk_score == 1.0
    assert len(res.spans) == 1
    assert res.spans[0].category == "CODEWORD_PROJECT_BLUE"


async def test_secret_hit(scanner: BanSubstringsScanner, ctx: ScanContext) -> None:
    res = await scanner.scan("AKIAIOSFODNN7EXAMPLE", ctx)
    assert res.is_valid is False
    assert len(res.spans) == 1
    assert res.spans[0].category == "SECRET_AWS_ACCESS_KEY"


async def test_multiple_hits(scanner: BanSubstringsScanner, ctx: ScanContext) -> None:
    text = "PROJECT_BLUE_X and PROJECT_BLUE_Y2 in one message"
    res = await scanner.scan(text, ctx)
    assert res.is_valid is False
    assert len(res.spans) == 2


async def test_scanner_name_and_direction(scanner: BanSubstringsScanner) -> None:
    assert scanner.name == "ban_substrings"
    assert scanner.direction == "inbound"
