"""Conformance tests for the published, signed llm-guard image.

Skips unless LLM_GUARD_CONFORMANCE_IMAGE is set. CI runs these after pushing
the signed image to GHCR.
"""
from __future__ import annotations

import os
import subprocess  # nosec B404 — required for cosign shell-out

import pytest

pytestmark = pytest.mark.conformance


_IMAGE = os.environ.get("LLM_GUARD_CONFORMANCE_IMAGE", "")
_IDENTITY = os.environ.get("LLM_GUARD_COSIGN_IDENTITY", "")
_OIDC_ISSUER = os.environ.get(
    "LLM_GUARD_COSIGN_OIDC_ISSUER",
    "https://token.actions.githubusercontent.com",
)


def _skip_if_missing() -> None:
    if not _IMAGE or not _IDENTITY:
        pytest.skip("LLM_GUARD_CONFORMANCE_IMAGE or LLM_GUARD_COSIGN_IDENTITY not set")


def test_cosign_verify_image():
    _skip_if_missing()
    result = subprocess.run(  # nosec B603, B607 — controlled cosign invocation  # noqa: S603
        [  # noqa: S607
            "cosign", "verify",
            "--certificate-identity", _IDENTITY,
            "--certificate-oidc-issuer", _OIDC_ISSUER,
            _IMAGE,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"cosign verify failed: {result.stderr}"


def test_image_has_slsa_provenance():
    _skip_if_missing()
    result = subprocess.run(  # nosec B603, B607  # noqa: S603
        [  # noqa: S607
            "cosign", "verify-attestation",
            "--certificate-identity", _IDENTITY,
            "--certificate-oidc-issuer", _OIDC_ISSUER,
            "--type", "slsaprovenance",
            _IMAGE,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"SLSA attestation verify failed: {result.stderr}"
