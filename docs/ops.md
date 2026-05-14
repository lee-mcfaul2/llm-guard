# llm-guard ops

## Pinned llm-guard library version

The `llm-guard` Python library is pinned in `pyproject.toml`. To upgrade:

1. Bump the version in `pyproject.toml`.
2. Run `uv lock` to regenerate the lockfile.
3. Rebuild the image; the Dockerfile's model pre-load step picks up any new
   default model versions automatically.
4. Run integration tests with the `run-integration` PR label.

When upstream releases a meaningful prompt-injection model update, ops should
bump within a sprint. Track the [llm-guard release feed](https://github.com/protectai/llm-guard/releases).

## Configuration

All config is env-driven via `LLM_GUARD_*` variables. See `src/llm_guard_svc/config.py`.

| Env var | Purpose |
|---|---|
| `LLM_GUARD_PORT` | Listen port (default 8080) |
| `LLM_GUARD_PII_TYPES_PATH` | Path to mounted `pii-types.json` (required when ban_substrings or secrets enabled) |
| `LLM_GUARD_INBOUND_SCANNERS` | CSV list — defaults to all 5 inbound scanners |
| `LLM_GUARD_OUTBOUND_SCANNERS` | CSV list — defaults to all 4 outbound scanners |
| `LLM_GUARD_BAN_TOPICS` | CSV list of banned topics for BanTopics scanner |
| `LLM_GUARD_<SCANNER>_BLOCK_THRESHOLD` | Per-scanner block threshold (float 0..1) |
| `LLM_GUARD_MALICIOUS_URLS_TIMEOUT_SECONDS` | Per-URL probe budget |

## MaliciousURLs egress

The MaliciousURLs scanner makes outbound HTTP requests to check URL reachability. The Helm chart's `NetworkPolicy` allows egress to `0.0.0.0/0` on 80/443 (excluding RFC1918 ranges) for this purpose.

If your platform has an egress proxy for audit, set `HTTPS_PROXY` / `HTTP_PROXY` in the Deployment's env. Not implemented in v0.1.

## Pod readiness

Initial startup is 8–15s for ML model load (longer on first build when the model cache is cold). Readiness probe is `initialDelaySeconds: 10` with `failureThreshold: 18` to tolerate up to 90s of slow loads on contended nodes.

## Alerts (Prometheus rules — lives in secure-agent-demo)

- `llm_guard_scanner_errors_total` rate > 0 — page (a scanner is failing internally)
- `llm_guard_models_loaded == 0` for > 5min after pod start — page (model load is hanging)
- `gateway_llm_guard_enabled == 0` — page (gateway has llm_guard disabled, which is fine for dev but a security regression in prod)
