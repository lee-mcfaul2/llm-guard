# llm-guard

Prompt-injection and secret-leakage scanner for the AI Agent Security Platform.

Wraps [Protect AI's `llm-guard`](https://github.com/protectai/llm-guard) library
plus in-house regex backstops sourced from `lib-agent-prompt`'s shared
`pii-types.json`. Called by `agent-gateway` over HTTP for both inbound (user
prompts) and outbound (MCP responses) scanning.

## Quick start

```bash
make install
make test
make run
```

See `docs/api.md` for the request/response contract,
`docs/ops.md` for operational concerns,
`docs/threat-model.md` for the security posture.
