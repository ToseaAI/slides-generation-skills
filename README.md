# `slides-generation-skills`

Official ToseaAI skill package for turning documents into polished presentations.

This repository teaches AI agents how to use ToseaAI's document-to-presentation pipeline through local Python scripts. It is intentionally separate from both the [product backend](https://tosea.ai) and the optional [MCP server](https://github.com/ToseaAI/mcp-ToseaAI).

## What's in this repo

| Path | Purpose |
|------|---------|
| `SKILL.md` | Agent-facing workflow guide — the only file agents need to read |
| `scripts/` | Thin Python CLI wrappers calling the ToseaAI `/api/mcp/v1` HTTP API |
| `references/` | Endpoint mapping and operating model notes |
| `examples/` | Copy-paste workflow examples and manifest samples |
| `agents/openai.yaml` | OpenAI-compatible skill metadata |

## Setup

### 1. Environment variables

```bash
export TOSEA_API_KEY="sk_..."
```

Get your API key at **https://tosea.ai** → Settings → Developers.

To point at a non-production server (for testing):

```bash
export TOSEA_API_BASE_URL="https://your-test-server.example.com"
```

When unset, scripts default to `https://tosea.ai`.

### 2. Verify

```bash
python scripts/health.py
python scripts/get_permissions_summary.py
```

No external dependencies — scripts use only the Python standard library.

## Install as a skill

**Codex:**

```bash
git clone git@github.com:ToseaAI/slides-generation-skills.git ~/.codex/skills/tosea-slides
```

**Claude Code / Cursor:**

Clone the repo alongside your project and reference `SKILL.md` from your project instructions or MCP config.

**Manual / standalone:**

The scripts work without any agent framework. Just set the env vars and run them directly.

## Quick example

```bash
python scripts/make_idempotency_key.py --prefix oneshot
python scripts/upload_files.py --file ./report.pdf
python scripts/pdf_to_presentation.py \
  --file ./report.pdf \
  --instruction "Create a 10-slide summary." \
  --output-format pptx \
  --idempotency-key <key>
python scripts/wait_for_job.py --presentation-id <id> --download-to ./output.pptx
```

For staged workflows with outline editing, see `examples/staged-workflow.md`.

For post-generation template switching on an existing presentation, use
`python scripts/switch_template.py --presentation-id <id> --template-name beamer_classic`
or swap in `--user-template-id` / `--system-template-key`.

For standalone Markdown extraction, use the document-parse flow:

```bash
python scripts/make_idempotency_key.py --prefix docparse
python scripts/upload_files.py --file ./report.pdf
python scripts/create_document_parse.py \
  --file ./report.pdf \
  --instruction "Extract faithful Markdown and keep image references." \
  --idempotency-key <key>
python scripts/wait_for_job.py --document-parse-id <id>
python scripts/get_parse_result.py --document-parse-id <id> --save-markdown-to ./report.md
```

This standalone flow still uses the backend's existing billing, quota, and access checks. It returns a `document_parse_id` facade while the backend reuses the internal presentation pipeline.

## Validate and package

Before publishing a new skill release:

```bash
python scripts/validate_skill.py
python scripts/package_skill.py --version 0.1.0
```

The packager creates a zip in `dist/` containing `SKILL.md`, scripts, references, examples, and metadata.

## Repository separation

- **This repo** — workflow policy + scripts (what agents read and run)
- **mcp-ToseaAI** — optional stdio MCP transport (for hosts that prefer MCP over direct scripts)
- **ToseaAI backend** — the system of record for auth, billing, quota, storage, and exports

## License

MIT — see [LICENSE](LICENSE).
