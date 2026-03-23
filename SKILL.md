# ToseaAI Slides Skill

Use this skill when the user wants to generate, revise, export, or re-download a presentation through ToseaAI.

## Preconditions

- The `tosea` MCP server must be configured.
- If server state is unknown, call `tosea_health` once before expensive actions.
- If the user is likely to hit tier or quota limits, call `tosea_get_permissions_summary` or `tosea_get_quota_status` before generation.

## Workflow choice

Choose `one-shot` when:

- the user wants the fastest path from local files to a final `pptx` or `pdf`
- the user is not asking for intermediate edits

Choose `staged` when:

- the user wants outline or slide revisions
- the user wants to inspect progress between parse, outline, render, and export
- the deck is high-stakes and requires controlled iteration

## One-shot workflow

1. Call `tosea_pdf_to_presentation` with local `file_paths`, user instruction, output format, and model choices.
2. Save `presentation_id` from the response immediately.
3. Call `tosea_wait_for_job` until the job is `completed` or `failed`.
4. If completed, report the final export details from the job payload.
5. If the user needs another format, call `tosea_export_presentation` and then `tosea_wait_for_job`.

## Staged workflow

1. Call `tosea_parse_pdf`.
2. Wait for parse completion with `tosea_wait_for_job`.
3. Call `tosea_generate_outline`.
4. Wait again.
5. For outline changes, call `tosea_edit_outline_page`.
6. Call `tosea_render_slides`.
7. Wait again.
8. For slide changes, call `tosea_edit_slide_page`.
9. Export with `tosea_export_presentation`.
10. Wait for export completion, then optionally call `tosea_list_export_files` or `tosea_redownload_export`.

## Mutation guardrails

- Use a fresh `idempotency_key` for each new outline edit, slide edit, or export.
- Reuse the same `idempotency_key` only when retrying the same mutation after a transport failure.
- Do not re-run `tosea_pdf_to_presentation` or `tosea_parse_pdf` blindly after a timeout; first inspect `presentation_id`, `tosea_list_presentations`, or existing export history.
- For `slide_mode=image`, pass `image_model` when the user explicitly asks for image generation quality or consistency.
- For multimodal slide edits, prefer `screenshot_path` when a local slide screenshot is available.

## Error handling

- `401`: API key invalid, revoked, or expired. Stop and tell the user to refresh the key.
- `402`: insufficient credits. Stop and report the friendly credit message.
- `403`: feature not available on the current tier. Report the missing entitlement.
- `404`: presentation or export file not found. Verify `presentation_id` and `filename`.
- `429`: back off and retry later. Do not fan out repeated expensive requests.
- Background job `failed`: report the job error text and preserve the `presentation_id`.

## Final answer expectations

Always include:

- which workflow was used
- the `presentation_id`
- job outcome
- export filenames and download URLs when available
- any known limits, failures, or quota blockers

