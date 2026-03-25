# `slides-generation-skills`

Official ToseaAI skill package for scripts-first document-to-presentation workflows.

This repository is intentionally separate from both the product backend and the optional MCP server:

- the backend remains the system of record for auth, billing, quota, storage, and exports
- this repo provides `SKILL.md` plus local scripts that call `/api/mcp/v1`
- the `mcp-ToseaAI` repository remains an optional transport for hosts that already support MCP well

## What this repo contains

- `SKILL.md`: workflow policy for the agent
- `scripts/`: thin Python entrypoints that call the public `/api/mcp/v1` HTTP contract, including the three-step upload flow used by the web app
- `references/`: compact notes on transport, billing, and endpoint mapping
- `examples/`: one-shot and staged command examples
- `agents/openai.yaml`: metadata for OpenAI-compatible skill packaging

## Default runtime

This skill is scripts-first. It does not require MCP.

Required environment variables:

```bash
export TOSEA_API_KEY="sk_..."
export TOSEA_API_BASE_URL="https://your-tosea-backend.example.com"
```

Windows PowerShell:

```powershell
$env:TOSEA_API_KEY="sk_..."
$env:TOSEA_API_BASE_URL="https://your-tosea-backend.example.com"
```

## Windows and OpenClaw path safety

On Windows hosts, especially OpenClaw-style shell execution, raw non-ASCII file paths can be mangled before Python receives them. To avoid that:

- prefer a UTF-8 manifest file via `--manifest`
- or copy source files to an ASCII-only staging directory such as `C:\tosea-inputs\`

Manifest example:

```json
{
  "files": [
    "C:\\tosea-inputs\\source.pdf",
    "C:\\tosea-inputs\\source.docx"
  ]
}
```

Reference file: [examples/source-manifest.example.json](examples/source-manifest.example.json)

## Attachment delivery safety

If the generated deck will be re-uploaded through OpenClaw, WeChat, email, or another relay layer:

- pass `--export-filename` when the user cares about the final visible attachment name
- preserve filename, extension, and `Content-Type` when relaying the downloaded file
- do not repackage the file as an anonymous binary attachment, or downstream clients may show only a generic attachment label

## Asset file_id inputs

- `--logo-file-id` is the confirmed uploaded `file_id` for a logo asset. It is not a local path.
- `--template-file-id` is the confirmed uploaded `file_id` for a PPTX/PDF custom-template asset. It is not a source document path.
- `--template-file-id` is valid only with `--slide-mode image`.
- When `--template-file-id` is present, the backend treats the request as `custom_template` automatically.
- Do not upload a template PPTX/PDF through `--file` for generation. Upload it separately and pass the returned `file_id`.

## Upload constraints

- `--page-count-range` must be one of `4-8`, `8-12`, `12-16`, `16-20`, `20-30`, `30-40`, `40-50`, or `50-100`.
- Source-file count and total source-page limits are enforced by backend tier policy.
- The current default/free backend policy is `1` source file and `60` total source pages unless server-side policy overrides it.

## Image mode decision rule

- keep `--slide-mode html` by default
- use `--slide-mode image` only when the user explicitly wants image-mode rendering or image-first slide composition
- when using image mode, pass `--image-model` if the user cares about image quality or regeneration consistency
- use `--output-format pptx_image` when the user wants a pure image-based PPTX export
- use `--output-format pdf` for image-mode review handoff
- do not use `--output-format html_zip` for image-mode decks

Then call:

```bash
python scripts/upload_files.py --manifest ./sources.json
python scripts/pdf_to_presentation.py --manifest ./sources.json --instruction "Create a crisp 6-slide investor update." --output-format pptx --render-model gemini-3.1-pro-preview --idempotency-key <value>
```

Custom-template image mode:

```bash
python scripts/upload_files.py --file ./brand-logo.png
python scripts/upload_files.py --file ./custom-template.pptx
python scripts/pdf_to_presentation.py --manifest ./sources.json --instruction "Create an 8-slide research deck." --slide-mode image --template-file-id <template_file_id> --logo-file-id <logo_file_id> --output-format pptx_image --export-filename research_deck_image.pptx --idempotency-key <value>
```

## Typical use

Health check:

```bash
python scripts/health.py
python scripts/get_permissions_summary.py
python scripts/get_quota_status.py
```

One-shot:

```bash
python scripts/upload_files.py --file ./deck-source.pdf --file ./deck-source.docx
# Windows/OpenClaw alternative:
# python scripts/upload_files.py --manifest ./sources.json
python scripts/make_idempotency_key.py --prefix one-shot
python scripts/pdf_to_presentation.py --file ./deck-source.pdf --file ./deck-source.docx --instruction "Create a crisp 6-slide investor update." --output-format pptx --export-filename investor_update_final.pptx --render-model gemini-3.1-pro-preview --idempotency-key <value>
# Windows/OpenClaw alternative:
# python scripts/pdf_to_presentation.py --manifest ./sources.json --instruction "Create a crisp 6-slide investor update." --output-format pptx --export-filename investor_update_final.pptx --render-model gemini-3.1-pro-preview --idempotency-key <value>
python scripts/wait_for_job.py --presentation-id <presentation_id> --download-to ./investor_update_final.pptx
```

Staged:

```bash
python scripts/upload_files.py --file ./deck-source.pdf --file ./deck-source.docx
# Windows/OpenClaw alternative:
# python scripts/upload_files.py --manifest ./sources.json
python scripts/make_idempotency_key.py --prefix parse
python scripts/parse_pdf.py --file ./deck-source.pdf --file ./deck-source.docx --instruction "Create a 6-slide operating review." --render-model gemini-3.1-pro-preview --idempotency-key <value>
# Windows/OpenClaw alternative:
# python scripts/parse_pdf.py --manifest ./sources.json --instruction "Create a 6-slide operating review." --render-model gemini-3.1-pro-preview --idempotency-key <value>
python scripts/wait_for_job.py --presentation-id <presentation_id>
python scripts/generate_outline.py --presentation-id <presentation_id> --instruction "Emphasize risks, mitigations, and owners."
python scripts/edit_outline_page.py --presentation-id <presentation_id> --page-number 2 --action modify --instruction "Make this page a sharper executive summary." --idempotency-key <value>
python scripts/render_slides.py --presentation-id <presentation_id> --render-model gemini-3.1-pro-preview --force
python scripts/edit_slide_page.py --presentation-id <presentation_id> --page-number 2 --action modify --instruction "Use fewer bullets and a stronger title." --edit-mode layout_only --idempotency-key <value>
python scripts/export_presentation.py --presentation-id <presentation_id> --output-format pptx --export-filename staged_review_final.pptx --idempotency-key <value>
python scripts/wait_for_job.py --presentation-id <presentation_id> --download-to ./staged_review_final.pptx
```

## Optional MCP pairing

If the host already has a configured `tosea` MCP server, the same workflow can be mirrored through MCP tools. That is optional. The local scripts remain the default execution layer for Claude-style skills.

## Validate and package

```bash
python scripts/validate_skill.py
python scripts/package_skill.py --version 0.1.0
```
