# Script → Endpoint Map

All endpoints are under `/api/mcp/v1`. Scripts default to `https://tosea.ai` when `TOSEA_API_BASE_URL` is unset.

Scripts that accept local file paths also support `--manifest <utf8-json>` for Windows/OpenClaw-safe path handling.

## Read-only

| Script | Endpoint |
|--------|----------|
| `health.py` | `GET /health` |
| `get_permissions_summary.py` | `GET /permissions/features/summary` |
| `get_quota_status.py` | `GET /permissions/quotas/status` |
| `check_quota.py` | `GET /permissions/quotas/{feature_key}/check` |
| `list_presentations.py` | `GET /presentations` |
| `get_full_data.py` | `GET /presentations/{id}/full-data` |
| `wait_for_job.py` | `GET /jobs/{id}` |
| `wait_for_job.py --document-parse-id` | `GET /document-parses/{id}` |
| `get_parse_result.py` | `GET /document-parses/{id}/result` |

## Upload

| Script | Endpoint |
|--------|----------|
| `upload_files.py` | `POST /files/upload-credentials` → signed URL `PUT` → `POST /files/confirm` |
| `list_uploaded_files.py` | `GET /files` |

## Create and mutate

| Script | Endpoint | Needs idempotency key |
|--------|----------|-----------------------|
| `parse_pdf.py` | `POST /file-ids-parse` | Yes |
| `create_document_parse.py` | `POST /document-parses/from-file-ids` | Yes |
| `pdf_to_presentation.py` | `POST /file-ids-to-presentation` | Yes |
| `generate_outline.py` | `POST /outline-generate` | No |
| `edit_outline_page.py` | `POST /presentations/{id}/outlines/{page}/ai-edit` | Yes |
| `render_slides.py` | `POST /slides-render` | No (use polling) |
| `edit_slide_page.py` | `POST /presentations/{id}/slides/{page}/ai-edit` | Yes |
| `switch_template.py` | `POST /presentations/{id}/switch-template` | No |
| `export_presentation.py` | `POST /export` | Yes |

## Export recovery

| Script | Endpoint |
|--------|----------|
| `list_exports.py` | `GET /exports` |
| `list_export_files.py` | `GET /exports/{id}/files` |
| `redownload_export.py` | `GET /exports/{id}/download/{type}?filename=...` |

## Notes

- `wait_for_job.py` returns the backend jobs payload. When `data.job` exists, use `data.job.status` as the terminal signal.
- `parse_pdf.py` starts the staged presentation workflow. `create_document_parse.py` is the standalone Markdown/asset parse facade.
- Valid export types: `pdf`, `pptx`, `pptx_image`, `html_zip`. Use `html_zip` only for HTML-mode decks.
- Valid page count ranges: `4-8`, `8-12`, `12-16`, `16-20`, `20-30`, `30-40`, `40-50`, `50-100`.
