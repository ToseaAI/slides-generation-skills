---
name: tosea-slides
description: Generate, revise, export, and recover presentations through ToseaAI by running the local scripts bundled in this skill. Use when an agent should turn local PDF files into PPTX or PDF decks, run staged outline or slide edits, poll background jobs, inspect permissions or quota, or re-download prior exports. Prefer this skill in Claude-style environments that can execute local scripts; use an existing tosea MCP server only as an optional transport alternative.
---

# ToseaAI Slides

Run the scripts in `scripts/` directly. Do not assume an MCP server is installed.

## Runtime setup

- Set `TOSEA_API_KEY` to a valid `sk_` key before any authenticated call.
- Set `TOSEA_API_BASE_URL` to the ToseaAI backend root, for example `https://your-tosea-backend.example.com`.
- If the base URL already contains `/api`, `/api/v1`, or `/api/mcp/v1`, the scripts normalize it back to the root domain.
- Run `python scripts/health.py` before expensive work if backend reachability is unknown.
- Run `python scripts/get_permissions_summary.py` or `python scripts/get_quota_status.py` when the user may be blocked by tier or quota.
- On Windows/OpenClaw, do not rely on raw non-ASCII file paths in CLI arguments. Prefer `--manifest <utf8-json>` or copy the files to an ASCII-only staging directory such as `C:\tosea-inputs\`.
- When the user cares about the final attachment name, pass `--export-filename "<name>.pptx|pdf|zip"` on one-shot or export commands.
- If an exported file will be relayed through OpenClaw, WeChat, email, or another chat surface, preserve filename, extension, and `Content-Type`. Do not repack it as an anonymous binary attachment.

## Required mutation discipline

- Generate a fresh request key before each new create, edit, render, or export mutation:

```bash
python scripts/make_idempotency_key.py --prefix parse
```

- Pass that value back with `--idempotency-key`.
- Reuse the same `idempotency_key` only when retrying the same logical request after a transport failure.
- Preserve `presentation_id` after the first successful create or parse call.
- For one-shot and export polling, treat nested `data.job.status` as authoritative when it exists.
- Keep export request keys short. Prefer bare UUIDs or short prefixes such as `xp` or `pdf`; avoid long prefixes like `export-pptx`.

Read `references/operating-model.md` only if you need the transport, billing, or retry boundaries.

## Workflow choice

Choose one-shot when:

- the user wants the fastest path from local files to a final deck
- no intermediate outline or slide edits are needed

Choose staged when:

- the user asks to review or change outline pages
- the user asks to revise or insert slides after render
- the deck is high-stakes and needs controlled checkpoints

Read `references/mcp-tools.md` only if you need the full script-to-endpoint map.

## Image-mode decision rule

- Keep `--slide-mode html` unless the user explicitly asks for image-mode rendering, image-first composition, template-driven image generation, or image-only visual consistency.
- If you use `--slide-mode image`, pass `--image-model` when the user cares about image quality or consistent image regeneration.
- `--slide-mode image` does not automatically imply `--output-format pptx_image`.
- In image mode, choose export format by delivery expectation:
  - use `--output-format pdf` for review, approval, or read-only handoff
  - use `--output-format pptx_image` when the user wants a PPTX deliverable that should preserve the generated visuals as-is
  - use `--output-format pptx` only when the user explicitly wants an editable PPTX or plans to keep editing in PowerPoint/Keynote
- If the user asks for a "PPTX" in image mode but does not say it must remain editable, prefer `--output-format pptx_image`.
- Do not use `--output-format html_zip` for image-mode decks.

## Asset file_id rule

- `--logo-file-id` is the confirmed uploaded `file_id` for a logo asset. It is not a local path.
- `--template-file-id` is the confirmed uploaded `file_id` for a PPTX/PDF custom-template asset. It is not a source document path.
- Only use `--template-file-id` with `--slide-mode image`.
- Do not put the template PPTX/PDF into `--file`; upload it separately and pass its `file_id`.
- When `--template-file-id` is present, the backend treats the request as `custom_template` automatically.

## Upload constraints

- `--page-count-range` must be one of `4-8`, `8-12`, `12-16`, `16-20`, `20-30`, `30-40`, `40-50`, or `50-100`.
- Source-file count and total source-page limits are enforced by backend tier policy.
- The current default/free backend policy is `1` source file and `60` total source pages unless server-side policy overrides it.

## One-shot workflow

1. Generate a request key with `python scripts/make_idempotency_key.py --prefix oneshot`.
2. First upload through the product upload system with `python scripts/upload_files.py --file <path> [--file <path>]` if you need explicit upload records or reusable `file_ids`.
   On Windows/OpenClaw, prefer `python scripts/upload_files.py --manifest ./sources.json`.
3. Upload logo or template assets separately when needed, then keep their returned `file_id` values for `--logo-file-id` or `--template-file-id`.
4. Call `python scripts/pdf_to_presentation.py --file <path> [--file <path>] --instruction "<text>" --output-format pptx --idempotency-key <key>`.
   Add `--export-filename "<name>.pptx"` when the user cares about the final attachment name.
   Only add `--slide-mode image [--image-model <model>]` when the user explicitly wants image mode.
   In image mode, use `--output-format pptx_image` unless the user clearly asks for an editable PPTX; use `--output-format pdf` for review handoff.
   Add `--logo-file-id <id>` when a confirmed uploaded logo asset should be applied.
   Add `--template-file-id <id>` only for image-mode custom-template runs.
5. Save `presentation_id` from `response.data.presentation_id`.
6. Poll with `python scripts/wait_for_job.py --presentation-id <id>`.
7. If the job completes and exposes `download_url`, save it with an explicit file path when the final filename matters, for example `--download-to ./board_update_final.pptx`.
8. If the user also needs PDF, generate a new key and call `python scripts/export_presentation.py --presentation-id <id> --output-format pdf --idempotency-key <key> [--export-filename "<name>.pdf"]`, then poll again.
9. Optionally inspect exports with `python scripts/list_export_files.py --presentation-id <id>`.

## Staged workflow

1. Generate a request key with `python scripts/make_idempotency_key.py --prefix parse`.
2. First upload through the product upload system with `python scripts/upload_files.py --file <path> [--file <path>]` if you need explicit upload records or reusable `file_ids`.
   On Windows/OpenClaw, prefer `python scripts/upload_files.py --manifest ./sources.json`.
3. Upload logo or template assets separately when needed, then keep their returned `file_id` values for `--logo-file-id` or `--template-file-id`.
4. Call `python scripts/parse_pdf.py --file <path> [--file <path>] --instruction "<text>" --idempotency-key <key>`.
   Add `--logo-file-id <id>` when a confirmed uploaded logo asset should be applied.
   Add `--template-file-id <id>` only for image-mode custom-template runs.
5. Poll with `python scripts/wait_for_job.py --presentation-id <id>`.
6. Call `python scripts/generate_outline.py --presentation-id <id> --instruction "<text>"`.
7. Poll again.
8. For outline revisions, generate a new key and call `python scripts/edit_outline_page.py --presentation-id <id> --page-number <n> --action modify|insert --instruction "<text>" --idempotency-key <key> [--after-slide <n>]`.
9. Render with `python scripts/render_slides.py --presentation-id <id> [--render-model gemini-3.1-pro-preview] [--image-model <model>] [--force]`.
10. Poll again.
11. For slide revisions, generate a new key and call `python scripts/edit_slide_page.py --presentation-id <id> --page-number <n> --action modify|insert --instruction "<text>" --edit-mode outline_layout|layout_only --idempotency-key <key> [--after-slide <n>] [--image-model <model>] [--screenshot-path <path>] [--screenshot-base64 <value>]`.
12. Export with `python scripts/export_presentation.py --presentation-id <id> --output-format pptx --idempotency-key <key> [--export-filename "<name>.pptx"]`, then poll and optionally export PDF the same way.
13. Use `python scripts/get_full_data.py --presentation-id <id>` whenever you need the current outline, slides, or speaker notes context.

## Script defaults

- Prefer `--render-model gemini-3.1-pro-preview` for quality-sensitive decks.
- Prefer `--slide-mode html` unless the user explicitly wants image mode.
- Use `--output-format pptx` for editable decks and `--output-format pdf` for review handoff.
- In image mode, prefer `--output-format pptx_image` for PPTX delivery unless the user explicitly asks for editability.
- Use `--output-format html_zip` only for HTML-mode decks.
- Pass `--image-model` only when the user explicitly asks for image quality or image-mode consistency.
- When a downstream chat client or relay layer cares about the visible attachment name, pass `--export-filename` and save with an explicit `--download-to` filename.

## Error handling

- `401`: stop and tell the user the API key is invalid, revoked, or expired.
- `402`: stop and report the insufficient credit message.
- `403`: stop and report that the current tier lacks the required feature.
- `404`: verify `presentation_id`, `page_number`, `export_type`, and `filename`.
- `409`: another active workflow is already running for the same presentation. Wait for it or let the user decide.
- `429`: back off and retry later. Do not fan out repeated expensive requests.
- Background job `failed`: report the job error text and keep the `presentation_id`.
- Background job `cancelled`: treat it as non-success and keep the `presentation_id`.

## Optional MCP mode

If the host already exposes a healthy `tosea` MCP server and the user explicitly wants tool routing instead of local scripts, mirror the same workflow through MCP. Do not make MCP a prerequisite for this skill.
Treat MCP as an optional MCP transport, not as the default runtime.

## Windows path safety

Preferred manifest shape:

```json
{
  "files": [
    "C:\\tosea-inputs\\source.pdf",
    "C:\\tosea-inputs\\source.docx"
  ]
}
```

Reference file: `examples/source-manifest.example.json`

If a Windows shell or host mangles a Unicode path before Python receives it, the scripts will fail fast with a local path error and tell the agent to use `--manifest` or an ASCII-only staging path.

## Final answer expectations

Always include:

- which workflow was used
- the `presentation_id`
- the terminal job outcome, using nested `data.job.status` when present
- export filenames and download URLs when available
- when relaying to OpenClaw, WeChat, email, or another chat surface, a reminder to preserve filename, extension, and MIME metadata
- any quota, billing, or retry blockers
