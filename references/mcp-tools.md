# ToseaAI MCP Tools

Core workflow tools:

- `tosea_pdf_to_presentation`
- `tosea_parse_pdf`
- `tosea_generate_outline`
- `tosea_edit_outline_page`
- `tosea_render_slides`
- `tosea_edit_slide_page`
- `tosea_export_presentation`
- `tosea_wait_for_job`

Inspection tools:

- `tosea_health`
- `tosea_get_permissions_summary`
- `tosea_get_quota_status`
- `tosea_list_presentations`
- `tosea_get_presentation_full_data`
- `tosea_list_exports`
- `tosea_list_export_files`
- `tosea_redownload_export`

Recommended defaults:

- `render_model`: `gemini-3.1-pro-preview` for quality-sensitive work
- `slide_mode`: `html` unless the user explicitly wants image mode
- `output_format`: `pptx` for editable decks, `pdf` for review handoff

