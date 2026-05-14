# llm-guard threat model

## What we defend

- **Prompt injection** (inbound): user prompts trying to override the system instructions or bypass safety
- **Indirect prompt injection** (outbound): malicious instructions embedded in tool/MCP responses that try to hijack the agent
- **Secrets leakage**: API keys, AWS credentials, etc. either being sent by users (inbound) or returned by MCPs (outbound)
- **Codeword leakage**: corporate-specific project names (CODEWORD-class categories from lib-agent-prompt's pii-types)
- **PII leakage** in tool responses (defense-in-depth alongside the gateway's tokenizer)
- **Malicious URLs** returned in tool responses
- **Content-policy violations** (toxicity, banned topics)

## What we don't defend

- **Determined human adversaries with full LLM Guard knowledge**: prompt-injection ML models are evadable by sophisticated attackers; defense-in-depth (sandbox isolation, per-tool schemas, mesh authz) covers the residual.
- **Multi-turn injection**: each `/scan` call is stateless. A user could split an attack across multiple inputs that each pass individually.
- **Network-level threats**: covered by Linkerd mTLS + NetworkPolicy, not by this service.

## Trust assumptions

- The agent-gateway is the only authorized caller (mesh authz enforces this).
- The mounted `pii-types.json` is trustworthy; we don't re-validate it at runtime.
- The pinned `llm-guard` library version is trustworthy (signed Python package, locked via uv).
- The OCI image is signed (cosign keyless) and provenance-verified (SLSA L3) before deployment.

## Failure semantics

- Stateless service. Pod restarts are free.
- **5xx → gateway returns 503 to end user** (fail-closed). We never silently allow on internal error.
- `/readyz` returns 503 until models load; K8s won't route to the pod during cold start.

## Observability for forensics

- Every scan logs `request_uuid`, `direction`, `action`, `categories`, `duration_ms`. The gateway's audit trail joins back via `request_uuid` for full context.
- We never log the `text` field. The gateway has the snapshot if forensic recovery is needed.
