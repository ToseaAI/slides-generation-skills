# Operating Model

This skill is opinionated about separation of concerns:

- ToseaAI backend: auth, billing, quota, storage, exports
- MCP server: robust transport, local file upload, polling, error normalization
- Skill: workflow choice, retry discipline, user-facing summaries

Reliability notes:

- Expensive create/upload actions are not auto-retried by the MCP server.
- Polling is preferred over streaming for MCP tools.
- The agent should avoid duplicate charges by tracking `presentation_id` and using idempotency keys on supported mutations and create calls.
- For export and one-shot workflows, the authoritative completion signal is the nested backend job state when `data.job` is present.

Security notes:

- Do not echo `sk_` secrets back to the user.
- Do not attempt JWT-only API key management through MCP runtime tools.
- Treat local file paths as sensitive user input and mention them only when operationally necessary.
