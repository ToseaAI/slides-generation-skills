# Operating Model

This skill is scripts-first.

- ToseaAI backend: auth, billing, quota, storage, exports, and background execution
- Local scripts in this repo: thin wrappers around `/api/mcp/v1`
- Optional MCP server: an alternative transport only when the host already has a healthy `tosea` server
- In other words, MCP is optional and local scripts remain the default runtime.

Reliability notes:

- Expensive create, edit, render, and export operations should use explicit `idempotency_key` values.
- Polling is preferred over streaming for skill execution.
- Preserve `presentation_id` after the first successful create or parse call.
- For export and one-shot workflows, the authoritative completion signal is nested `data.job.status` when `data.job` exists.
- `409` means an active workflow is already running for the same presentation; do not treat it as success.

Security notes:

- Do not echo `sk_` secrets back to the user.
- Do not try to create or revoke API keys from this skill runtime.
- Treat local file paths as sensitive user input and mention them only when operationally necessary.

Mode notes:

- Default mode is local scripts.
- Optional MCP mode is acceptable only when the host explicitly provides a healthy `tosea` server and direct script execution is not the preferred path.
