"""Load regex categories from lib-agent-prompt's shared pii-types.json.

Schema mounted as a ConfigMap in the Helm chart; path comes from
LLM_GUARD_PII_TYPES_PATH. We compile each entry's regex once at startup.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Category:
    name: str
    kind: str
    pattern: re.Pattern[str]


def load_categories(path: Path | str, kinds: set[str] | None = None) -> list[Category]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"pii-types.json not found at {p}")
    data = json.loads(p.read_text())
    out: list[Category] = []
    for entry in data.get("categories", []):
        kind = entry["kind"]
        if kinds is not None and kind not in kinds:
            continue
        out.append(Category(
            name=entry["name"],
            kind=kind,
            pattern=re.compile(entry["regex"]),
        ))
    return out
