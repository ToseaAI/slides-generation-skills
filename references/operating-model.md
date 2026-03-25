# Operating Model

This skill is scripts-first.

## Architecture

```
Agent (reads SKILL.md)
  → Local scripts (scripts/*.py)
    → ToseaAI HTTP API (/api/mcp/v1)
      → Backend: auth, billing, OCR, LLM rendering, storage, exports
```

Scripts are the default execution layer. An MCP server is an optional alternative transport when the host already provides one.

## Reliability

- Use `--idempotency-key` on all create, edit, render, and export operations to prevent duplicate billing.
- Upload source files through the three-step flow (`upload_files.py`) so the backend records reusable `file_ids`.
- Poll with `wait_for_job.py` rather than streaming. When `data.job` exists in the response, use `data.job.status` as the completion signal.
- HTTP 409 means another workflow is already running for the same presentation — do not treat it as success.

## Security

- API keys start with `sk_` and must not be echoed back to the user.
- Treat local file paths as sensitive input; mention them only when operationally necessary.
- On Windows, prefer `--manifest` or an ASCII-only staging directory for source file paths.
