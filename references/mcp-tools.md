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

- `python scripts/upload_files.py` -> `POST /api/mcp/v1/files/upload-credentials` + signed URL `PUT` + `POST /api/mcp/v1/files/confirm`
- `python scripts/list_uploaded_files.py` -> `GET /api/mcp/v1/files`
- `python scripts/pdf_to_presentation.py` -> `POST /api/mcp/v1/file-ids-to-presentation`
- `python scripts/parse_pdf.py` -> `POST /api/mcp/v1/file-ids-parse`
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
- `output_format`: `pptx_image` when an image-mode deck must be delivered as a PPTX while preserving the generated visuals as-is
- `logo_file_id`: confirmed uploaded logo asset ID when a logo should be applied
- `template_file_id`: confirmed uploaded PPTX/PDF custom-template asset ID; valid only with `slide_mode=image`

Notes:

- `upload_files.py` follows the same three-step upload pattern as the web app and returns reusable `file_ids`.
- `upload_files.py`, `parse_pdf.py`, and `pdf_to_presentation.py` accept `--manifest <utf8-json>` for Windows/OpenClaw-safe path handling.
- `pdf_to_presentation.py` and `export_presentation.py` accept `--export-filename` when the user cares about the visible exported attachment name.
- `logo_file_id` and `template_file_id` are asset IDs, not source-document paths.
- Do not pass the template PPTX/PDF as a source file for generation; upload it separately and pass `template_file_id`.
- `pdf_to_presentation.py`, `parse_pdf.py`, `edit_outline_page.py`, `edit_slide_page.py`, and `export_presentation.py` should receive explicit `idempotency_key` values.
- `render_slides.py` is asynchronous but does not currently take `idempotency_key`; use job polling instead of repeated blind retries.
- `wait_for_job.py` returns the backend jobs payload. When `data.job` exists, use `data.job.status` as the terminal signal.
- When `wait_for_job.py --download-to <directory>` is used, it prefers the backend job filename or the signed URL download hint before falling back to the URL path.
- `slide_mode=image` only controls rendering mode. It does not automatically mean `output_format=pptx_image`.
- In image mode, choose `output_format` by delivery expectation:
  - `pdf` for review or read-only handoff
  - `pptx_image` for PPTX delivery when visual fidelity matters more than downstream editing
  - `pptx` only when the user explicitly wants an editable PPTX
- If the user asks for "PPTX" in image mode without specifying editability, prefer `pptx_image`.
- `html_zip` is a valid export format only for HTML-mode decks.
- `page_count_range` must be one of `4-8`, `8-12`, `12-16`, `16-20`, `20-30`, `30-40`, `40-50`, or `50-100`.
- Source-file count and total source-page limits are enforced by backend tier policy; the current default/free fallback is `1` source file and `60` total source pages.
- If the host already has a healthy `tosea` MCP server, the same operations can be mirrored through MCP, but that mode is optional.
