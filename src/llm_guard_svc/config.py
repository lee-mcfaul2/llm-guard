"""Env-driven configuration for the llm-guard service."""
from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, EnvSettingsSource, SettingsConfigDict


_DEFAULT_INBOUND = ["prompt_injection", "secrets", "ban_substrings", "toxicity", "ban_topics"]
_DEFAULT_OUTBOUND = ["secrets", "prompt_injection", "malicious_urls", "sensitive"]
_DEFAULT_BAN_TOPICS = ["violence", "illegal_activity"]


def _split_csv(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    return [s.strip() for s in value.split(",") if s.strip()]


class _CsvEnvSource(EnvSettingsSource):
    """EnvSettingsSource that treats plain CSV strings as list[str] fields.

    pydantic-settings 2.x tries to JSON-decode env vars whose field annotation is
    a complex type (e.g. list[str]).  For our scanner/topic lists we want plain
    comma-separated values, so we intercept decode_complex_value and split on
    commas unless the value already looks like a JSON array.
    """

    def decode_complex_value(
        self, field_name: str, field: Any, value: Any
    ) -> Any:
        if isinstance(value, str):
            stripped = value.strip()
            if not (stripped.startswith("[") or stripped.startswith("{")):
                return _split_csv(stripped)
        return super().decode_complex_value(field_name, field, value)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LLM_GUARD_", env_file=None)

    port: int = 8080

    inbound_scanners: list[str] = Field(default_factory=lambda: list(_DEFAULT_INBOUND))
    outbound_scanners: list[str] = Field(default_factory=lambda: list(_DEFAULT_OUTBOUND))

    prompt_injection_block_threshold: float = 0.7
    secrets_block_threshold: float = 1.0
    toxicity_block_threshold: float = 0.8
    ban_topics_block_threshold: float = 0.7
    malicious_urls_block_threshold: float = 0.9
    sensitive_block_threshold: float = 0.6

    malicious_urls_timeout_seconds: float = 0.5

    ban_topics: list[str] = Field(default_factory=lambda: list(_DEFAULT_BAN_TOPICS))

    pii_types_path: str = ""

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        **kwargs: Any,
    ) -> tuple[Any, ...]:
        return (_CsvEnvSource(settings_cls),)

    @field_validator("inbound_scanners", "outbound_scanners", "ban_topics", mode="before")
    @classmethod
    def _split(cls, v: str | list[str]) -> list[str]:
        return _split_csv(v)

    @model_validator(mode="after")
    def _check_backstop_paths(self) -> "Settings":
        needs_backstop = "ban_substrings" in self.inbound_scanners or (
            "secrets" in self.inbound_scanners or "secrets" in self.outbound_scanners
        )
        if needs_backstop and not self.pii_types_path:
            raise ValueError(
                "LLM_GUARD_PII_TYPES_PATH must be set when ban_substrings or secrets scanners are enabled. "
                "Mount lib-agent-prompt's shared pii-types.json and set the path."
            )
        return self
