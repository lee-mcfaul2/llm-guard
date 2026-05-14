"""Structured JSONL stderr logger.

Pure stdlib. No log content beyond the structured event + provided fields.
We never log scan text or other potentially sensitive payloads here.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from typing import TextIO


class _JSONLLogger:
    def __init__(self, name: str, stream: TextIO) -> None:
        self._name = name
        self._stream = stream
        self._lock = threading.Lock()

    def info(self, event: str, **fields: object) -> None:
        self._emit("info", event, fields)

    def warning(self, event: str, **fields: object) -> None:
        self._emit("warning", event, fields)

    def error(self, event: str, **fields: object) -> None:
        self._emit("error", event, fields)

    def _emit(self, level: str, event: str, fields: dict[str, object]) -> None:
        record: dict[str, object] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "level": level,
            "logger": self._name,
            "event": event,
        }
        for k, v in fields.items():
            if v is None:
                continue
            record[k] = v
        line = json.dumps(record, separators=(",", ":"), ensure_ascii=False)
        with self._lock:
            self._stream.write(line + "\n")
            self._stream.flush()


def get_logger(name: str, stream: TextIO | None = None) -> _JSONLLogger:
    return _JSONLLogger(name, stream or sys.stderr)
