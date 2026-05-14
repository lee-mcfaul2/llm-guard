from __future__ import annotations

from pathlib import Path

import pytest

from llm_guard_svc.scanners.base import ScanContext
from llm_guard_svc.scanners.secrets import SecretsScanner

FIXTURE = Path(__file__).parent.parent / "fixtures" / "pii-types.json"


@pytest.fixture
def scanner():
    return SecretsScanner(pii_types_path=str(FIXTURE))


@pytest.fixture
def ctx_inbound():
    return ScanContext(request_uuid="r1", direction="inbound")


@pytest.fixture
def ctx_outbound():
    return ScanContext(request_uuid="r1", direction="outbound", mcp="kb", tool="search")


async def test_no_secrets_is_valid(scanner, ctx_inbound):
    res = await scanner.scan("just normal text", ctx_inbound)
    assert res.is_valid is True


async def test_aws_key_detected_via_backstop(scanner, ctx_inbound):
    res = await scanner.scan("here is AKIAIOSFODNN7EXAMPLE", ctx_inbound)
    assert res.is_valid is False
    assert res.risk_score == 1.0
    assert any(s.category == "SECRET_AWS_ACCESS_KEY" for s in res.spans)


async def test_works_outbound_too(scanner, ctx_outbound):
    res = await scanner.scan("response contains AKIAIOSFODNN7EXAMPLE", ctx_outbound)
    assert res.is_valid is False


def test_direction_is_both(scanner):
    assert scanner.direction == "both"
    assert scanner.name == "secrets"
