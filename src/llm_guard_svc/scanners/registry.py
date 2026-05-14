"""Build the scanner registry from Settings.

The registry is built once at process start. Scanners are stateless after init
(ML ones load models in __init__; regex ones compile patterns in __init__).
Within a request we call them concurrently via asyncio.gather.

NOTE: subsequent tasks register prompt_injection, secrets, toxicity, ban_topics,
malicious_urls, sensitive in the builders dict.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from llm_guard_svc.config import Settings
from llm_guard_svc.scanners.ban_substrings import BanSubstringsScanner
from llm_guard_svc.scanners.base import Scanner
from llm_guard_svc.scanners.secrets import SecretsScanner


@dataclass(frozen=True)
class Registry:
    inbound: list[Scanner]
    outbound: list[Scanner]

    def for_direction(self, direction: Literal["inbound", "outbound"]) -> list[Scanner]:
        return self.inbound if direction == "inbound" else self.outbound


def build_registry(settings: Settings) -> Registry:
    builders: dict[str, Callable[[], Scanner]] = {
        "ban_substrings": lambda: BanSubstringsScanner(pii_types_path=settings.pii_types_path),
        "secrets": lambda: SecretsScanner(pii_types_path=settings.pii_types_path),
    }

    inbound: list[Scanner] = []
    for name in settings.inbound_scanners:
        if name not in builders:
            raise ValueError(f"unknown scanner in inbound_scanners: {name}")
        inbound.append(builders[name]())

    outbound: list[Scanner] = []
    for name in settings.outbound_scanners:
        if name not in builders:
            raise ValueError(f"unknown scanner in outbound_scanners: {name}")
        outbound.append(builders[name]())

    return Registry(inbound=inbound, outbound=outbound)
