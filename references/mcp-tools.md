# ToseaAI Script and Endpoint Map

Default execution layer:

- `python scripts/health.py` -> `GET /api/mcp/v1/health`
- `python scripts/get_permissions_summary.py` -> `GET /api/mcp/v1/permissions/features/summary`
- `python scripts/get_quota_status.py` -> `GET /api/mcp/v1/permissions/quotas/status` or `/permissions/quotas/{feature_key}/status`
- `python scripts/check_quota.py` -> `GET /api/mcp/v1/permissions/quotas/{feature_key}/check`
- `python scripts/list_presentations.py` -> `GET /api/mcp/v1/presentations`
- `python scripts/get_full_data.py` -> `GET /api/mcp/v1/presentations/{presentation_id}/full-data`
- `python scripts/wait_for_job.py` -> `GET /api/mcp/v1/jobs/{presentation_id}`

Create and mutation scripts:

- `python scripts/pdf_to_presentation.py` -> `POST /api/mcp/v1/pdf-to-presentation`
- `python scripts/parse_pdf.py` -> `POST /api/mcp/v1/pdf-parse`
- `python scripts/generate_outline.py` -> `POST /api/mcp/v1/outline-generate`
- `python scripts/edit_outline_page.py` -> `POST /api/mcp/v1/presentations/{presentation_id}/outlines/{page_number}/ai-edit`
- `python scripts/render_slides.py` -> `POST /api/mcp/v1/slides-render`
- `python scripts/edit_slide_page.py` -> `POST /api/mcp/v1/presentations/{presentation_id}/slides/{page_number}/ai-edit`
- `python scripts/export_presentation.py` -> `POST /api/mcp/v1/export`

Export recovery scripts:

- `python scripts/list_exports.py` -> `GET /api/mcp/v1/exports`
- `python scripts/list_export_files.py` -> `GET /api/mcp/v1/exports/{presentation_id}/files`
- `python scripts/redownload_export.py` -> `GET /api/mcp/v1/exports/{presentation_id}/download/{export_type}?filename=...`

Recommended defaults:

- `render_model`: `gemini-3.1-pro-preview` for quality-sensitive work
- `slide_mode`: `html` unless the user explicitly wants image mode
- `output_format`: `pptx` for editable decks, `pdf` for review handoff

Notes:

- `pdf_to_presentation.py`, `parse_pdf.py`, `edit_outline_page.py`, `edit_slide_page.py`, and `export_presentation.py` should receive explicit `idempotency_key` values.
- `render_slides.py` is asynchronous but does not currently take `idempotency_key`; use job polling instead of repeated blind retries.
- `wait_for_job.py` returns the backend jobs payload. When `data.job` exists, use `data.job.status` as the terminal signal.
- `html_zip` is a valid export format only for HTML-mode decks.
- If the host already has a healthy `tosea` MCP server, the same operations can be mirrored through MCP, but that mode is optional.
