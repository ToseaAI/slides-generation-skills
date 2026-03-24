# `slides-generation-skills`

Official ToseaAI skill package for scripts-first document-to-presentation workflows.

This repository is intentionally separate from both the product backend and the optional MCP server:

- the backend remains the system of record for auth, billing, quota, storage, and exports
- this repo provides `SKILL.md` plus local scripts that call `/api/mcp/v1`
- the `mcp-ToseaAI` repository remains an optional transport for hosts that already support MCP well

## What this repo contains

- `SKILL.md`: workflow policy for the agent
- `scripts/`: thin Python entrypoints that call the public `/api/mcp/v1` HTTP contract
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

## Typical use

Health check:

```bash
python scripts/health.py
python scripts/get_permissions_summary.py
python scripts/get_quota_status.py
```

One-shot:

```bash
python scripts/make_idempotency_key.py --prefix one-shot
python scripts/pdf_to_presentation.py --file ./deck-source.pdf --instruction "Create a crisp 6-slide investor update." --output-format pptx --render-model gemini-3.1-pro-preview --idempotency-key <value>
python scripts/wait_for_job.py --presentation-id <presentation_id> --download-to ./output.pptx
```

Staged:

```bash
python scripts/make_idempotency_key.py --prefix parse
python scripts/parse_pdf.py --file ./deck-source.pdf --instruction "Create a 6-slide operating review." --render-model gemini-3.1-pro-preview --idempotency-key <value>
python scripts/wait_for_job.py --presentation-id <presentation_id>
python scripts/generate_outline.py --presentation-id <presentation_id> --instruction "Emphasize risks, mitigations, and owners."
python scripts/edit_outline_page.py --presentation-id <presentation_id> --page-number 2 --action modify --instruction "Make this page a sharper executive summary." --idempotency-key <value>
python scripts/render_slides.py --presentation-id <presentation_id> --render-model gemini-3.1-pro-preview --force
python scripts/edit_slide_page.py --presentation-id <presentation_id> --page-number 2 --action modify --instruction "Use fewer bullets and a stronger title." --edit-mode layout_only --idempotency-key <value>
python scripts/export_presentation.py --presentation-id <presentation_id> --output-format pptx --idempotency-key <value>
python scripts/wait_for_job.py --presentation-id <presentation_id> --download-to ./staged-output.pptx
```

## Optional MCP pairing

If the host already has a configured `tosea` MCP server, the same workflow can be mirrored through MCP tools. That is optional. The local scripts remain the default execution layer for Claude-style skills.

## Validate and package

```bash
python scripts/validate_skill.py
python scripts/package_skill.py --version 0.1.0
```
