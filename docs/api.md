# llm-guard API

## POST /scan

Request body:

```json
{
  "text": "<text to scan>",
  "request_uuid": "<UUID minted by the gateway>",
  "direction": "inbound" | "outbound",
  "mcp": "<MCP name, empty for inbound>",
  "tool": "<tool name, empty for inbound>"
}
```

Response (200):

```json
{
  "action": "allow" | "flag" | "block",
  "categories": ["prompt_injection", ...],
  "spans": [
    {"category": "secrets", "start": 12, "end": 48, "scanner": "Secrets"}
  ]
}
```

Errors return 400/500/503 with body `{"detail": {"error": "<CODE>"}}` (FastAPI's wrapping for HTTPException with dict detail). The gateway is fail-closed: any 5xx becomes a 503 to the end user.

## GET /healthz, /readyz, /metrics

- `/healthz` — liveness; 200 if process is up.
- `/readyz` — readiness; 200 only after all configured ML models loaded.
- `/metrics` — Prometheus exposition.

## Extending: adding a custom scanner

1. Create `src/llm_guard_svc/scanners/<name>.py` implementing the `Scanner` protocol (`name`, `direction`, async `scan(text, ctx)`).
2. Register a builder in `src/llm_guard_svc/scanners/registry.py`.
3. Add a `<name>_block_threshold` field to `Settings` and a corresponding entry in `_thresholds_from()` in `server.py` if needed.
4. Add unit tests under `tests/unit/test_<name>_scanner.py`. Integration tests for real model loads go under `tests/integration/`.
