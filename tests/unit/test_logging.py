from __future__ import annotations

import io
import json

from llm_guard_svc.obs.logging import get_logger


def test_logger_emits_jsonl():
    stream = io.StringIO()
    log = get_logger("test", stream=stream)
    log.info("scan", request_uuid="r1", direction="inbound", action="allow", duration_ms=42)
    line = stream.getvalue().strip()
    parsed = json.loads(line)
    assert parsed["event"] == "scan"
    assert parsed["request_uuid"] == "r1"
    assert parsed["level"] == "info"
    assert parsed["logger"] == "test"
    assert "ts" in parsed


def test_logger_error_level():
    stream = io.StringIO()
    log = get_logger("test", stream=stream)
    log.error("scanner_failed", scanner="prompt_injection", err="boom")
    parsed = json.loads(stream.getvalue().strip())
    assert parsed["level"] == "error"
    assert parsed["err"] == "boom"


def test_logger_skips_none_fields():
    stream = io.StringIO()
    log = get_logger("test", stream=stream)
    log.info("scan", request_uuid="r1", mcp=None, tool=None)
    parsed = json.loads(stream.getvalue().strip())
    assert "mcp" not in parsed
    assert "tool" not in parsed
