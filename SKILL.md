---
name: tosea-slides
description: Turn PDF, Word, Markdown, and other documents into polished PPTX or PDF presentations through ToseaAI. Supports one-shot generation and staged editing with outline control, 17 professional templates, and AI image-mode slides.
---

# ToseaAI Slides

ToseaAI is an AI presentation service that converts documents into professional slide decks. It uses GPU-accelerated OCR to faithfully extract text, images, tables, and mathematical formulas from source files, then generates structured outlines and renders polished slides — no content hallucination, no lost figures.

This skill runs the local Python scripts in `scripts/`. No MCP server is needed.

## Supported inputs

**Source documents** (the content to turn into slides):

| Type | Extensions | Notes |
|------|-----------|-------|
| PDF | `.pdf` | Full structural extraction: text, images, tables, formulas |
| Word | `.doc`, `.docx` | Text and basic structure |
| Text | `.txt`, `.md` | Plain text and Markdown |
| Images | `.png`, `.jpg`, `.jpeg` | Used as reference material |

Multiple source files can be combined in a single presentation (subject to tier limits).

**Other uploadable assets:**

| Asset | Extensions | Mode | Passed via |
|-------|-----------|------|------------|
| Custom template | `.pptx`, `.ppt`, `.pdf` | Image mode only | `--template-file-id` |
| Logo | `.png`, `.jpg`, `.jpeg`, `.svg` | Any mode | `--logo-file-id` |

These are NOT source documents. Upload each separately with `upload_files.py`, then pass the returned `file_id`. Using a custom template requires image mode (`--slide-mode image`). See "Custom logo" and "Custom template workflow" below.

## Quick start

```bash
# 1. Check connectivity
python scripts/health.py

# 2. Generate a one-shot deck from a PDF
python scripts/make_idempotency_key.py --prefix oneshot
python scripts/upload_files.py --file ./report.pdf
python scripts/pdf_to_presentation.py \
  --file ./report.pdf \
  --instruction "Create a 10-slide summary of this research paper." \
  --output-format pptx \
  --idempotency-key <key-from-step-above>

# 3. Wait for completion and download
python scripts/wait_for_job.py --presentation-id <id> --download-to ./output.pptx
```

That's it. The sections below cover templates, models, staged editing, and advanced options.

## Getting an API key

Set your key before running any script:

```bash
export TOSEA_API_KEY="sk_..."
```

If the user does not have an API key yet:

1. Visit **https://tosea.ai** and create an account
2. Go to **Settings → Developers** to generate an API key
3. API keys start with `sk_` and are shown only once — save it immediately

**Pricing overview:**

| Plan | Monthly credits | API access | Templates |
|------|----------------|------------|-----------|
| Free | 200 | Web only | 7 free templates |
| Pro | 1,500 + 300 | Full API + MCP | All 17 templates |
| Max | 7,000 | Full API + MCP | All 17 templates |

When the agent encounters HTTP 402 (insufficient credits) or 403 (tier restriction), inform the user about their current plan and suggest upgrading at https://tosea.ai.

## Optional: custom API base URL

By default, scripts connect to `https://tosea.ai`. Override only for testing or self-hosted instances:

```bash
export TOSEA_API_BASE_URL="https://your-test-server.example.com"
```

## Templates

ToseaAI offers 17 built-in templates in two categories. Pick one that fits the user's context.

### Academic templates

| Key | Name | Best for |
|-----|------|----------|
| `beamer_classic` | Classic Beamer | LaTeX-style technical talks, CS, math |
| `academic_blue_amber` | Academic Blue & Amber | Formal academic presentations |
| `oxford_classic` | Oxford Classic | Humanities, history, law |
| `tender` | Tender | Warm-toned humanities and business crossover |
| `minimal_dark` | Minimal Dark | Design, architecture, minimal aesthetic |
| `lucent` ★ | Lucent | Elegant scholarly minimalism |
| `cambridge_blue` ★ | Cambridge Blue | Social sciences, literature |
| `mit_tech` ★ | MIT Tech | Engineering, CS, data-heavy |
| `paper_editorial` ★ | Paper Editorial | Journal-style research content |
| `stanford_cardinal` ★ | Stanford Cardinal | Academic-business crossover |
| `nature_science` ★ | Nature Science | Biology, chemistry, physics |

### Business templates

| Key | Name | Best for |
|-----|------|----------|
| `executive_platinum` | Executive Platinum | C-suite, investor relations, strategy |
| `spotlight` | Spotlight | TED-style keynotes, bold storytelling |
| `strategy_navy` ★ | Strategy Navy | Consulting, board decks, due diligence |
| `venture_green` ★ | Venture Green | Growth strategy, ESG, portfolio review |
| `impact_red` ★ | Impact Red | Transformation results, value narratives |
| `material_bright` ★ | Material Bright | Product updates, team communication |

★ = Pro/Max plan only. Unmarked = available on all plans.

**Recommendations:**
- Research paper → `beamer_classic` or `nature_science`
- Business report → `executive_platinum` or `strategy_navy`
- Lecture slides → `oxford_classic` or `academic_blue_amber`
- Startup pitch → `spotlight` or `venture_green`
- Not sure → `tender` (versatile default)

Pass the key as `--template-name`, for example `--template-name strategy_navy`.

### Custom logo

A logo can be added to any presentation in any mode (HTML or image). Upload the logo image first, then pass its `file_id`:

```bash
python scripts/upload_files.py --file ./company-logo.png
# The JSON output contains "file_id" — extract and save it

python scripts/pdf_to_presentation.py \
  --file ./source.pdf \
  --logo-file-id <file-id-from-upload> \
  --instruction "..." \
  --output-format pptx \
  --idempotency-key <key>
```

The logo appears on each slide. Supported formats: `.png`, `.jpg`, `.jpeg`, `.svg` (max 2 MB).

## Render models

The render model controls the LLM that generates slide content.

| Model | Tier | Recommended for |
|-------|------|----------------|
| `deepseek-chat-v3.1` | Free | Good default, fast |
| `gemini-3-flash-preview` | Free | Google quality, fast |
| `glm-5` | Free | Chinese-language content |
| `gemini-3.1-pro-preview` | Pro | Best overall quality |
| `claude-sonnet-4.6` | Pro | Nuanced writing, long documents |

Pass as `--render-model`, for example `--render-model gemini-3.1-pro-preview`.

## Slide domains

Tell ToseaAI the subject area for better slide structure:

`computer_science` · `engineering_stem` · `natural_sciences` · `theoretical_sciences` · `quant_socsci` · `business` · `humanities` · `general`

Pass as `--slide-domain`. Default is `general`.

## Choosing a workflow

**One-shot** — fastest path from file to finished deck:
- The user wants a complete presentation without editing intermediate steps
- Suitable for straightforward "turn this PDF into slides" requests

**Staged** — full control with checkpoints:
- The user wants to review or revise the outline before rendering
- The user wants to edit individual slides after rendering
- High-stakes decks that need iterative refinement

**Custom template** — when the user provides their own PPTX/PDF template:
- Automatically uses image mode (Nano Banana) — do not use HTML mode with custom templates
- The template file must be uploaded separately from source documents
- See "Custom template workflow" below

## One-shot workflow

Before choosing a command, separate two parse-related intents:

- Use `parse_pdf.py` when the user is starting the staged presentation workflow and will continue with outline generation or slide rendering.
- Use `create_document_parse.py` when the user wants Markdown, extracted image URLs, or parse metadata without entering the presentation workflow.
- The standalone document-parse flow still consumes parse credits and still respects the same upload and plan limits.

```bash
python scripts/make_idempotency_key.py --prefix oneshot
python scripts/upload_files.py --file ./source.pdf
python scripts/pdf_to_presentation.py \
  --file ./source.pdf \
  --instruction "Create a 10-slide investor update." \
  --output-format pptx \
  --template-name executive_platinum \
  --slide-domain business \
  --idempotency-key <key>
python scripts/wait_for_job.py --presentation-id <id> --download-to ./investor_update.pptx
```

To also export PDF: generate a new key, then:

```bash
python scripts/export_presentation.py \
  --presentation-id <id> --output-format pdf --idempotency-key <new-key>
python scripts/wait_for_job.py --presentation-id <id> --download-to ./investor_update.pdf
```

## Staged workflow

```bash
# 1. Parse the source document
python scripts/make_idempotency_key.py --prefix parse
python scripts/upload_files.py --file ./source.pdf
python scripts/parse_pdf.py \
  --file ./source.pdf \
  --instruction "Create a 12-slide research presentation." \
  --template-name nature_science \
  --idempotency-key <key>
python scripts/wait_for_job.py --presentation-id <id>

# 2. Generate and optionally edit the outline
python scripts/generate_outline.py --presentation-id <id> --instruction "Emphasize methodology and results."
python scripts/wait_for_job.py --presentation-id <id>

# Edit a specific outline page if needed:
python scripts/make_idempotency_key.py --prefix outline
python scripts/edit_outline_page.py \
  --presentation-id <id> --page-number 3 --action modify \
  --instruction "Make this page focus on experimental setup." \
  --idempotency-key <key>

# 3. Render slides
python scripts/render_slides.py --presentation-id <id>
python scripts/wait_for_job.py --presentation-id <id>

# Switch the template after generation if needed:
python scripts/switch_template.py \
  --presentation-id <id> --template-name executive_platinum
python scripts/wait_for_job.py --presentation-id <new-id>

# Edit a specific slide if needed:
python scripts/make_idempotency_key.py --prefix slide
python scripts/edit_slide_page.py \
  --presentation-id <id> --page-number 3 --action modify \
  --instruction "Use fewer bullets and a stronger title." \
  --edit-mode layout_only --idempotency-key <key>

# 4. Export
python scripts/make_idempotency_key.py --prefix xp
python scripts/export_presentation.py \
  --presentation-id <id> --output-format pptx --idempotency-key <key>
python scripts/wait_for_job.py --presentation-id <id> --download-to ./final.pptx
```

Use `python scripts/get_full_data.py --presentation-id <id>` at any point to inspect the current outline, slides, and speaker notes.
For template switching, provide exactly one of `--template-name`, `--user-template-id`, or `--system-template-key`.

## Standalone document parse workflow

Use this when the user wants a reusable Markdown extraction result instead of a presentation workflow.

```bash
python scripts/make_idempotency_key.py --prefix docparse
python scripts/upload_files.py --file ./source.pdf
python scripts/create_document_parse.py \
  --file ./source.pdf \
  --instruction "Extract faithful Markdown and keep figure references." \
  --idempotency-key <key>
python scripts/wait_for_job.py --document-parse-id <id>
python scripts/get_parse_result.py \
  --document-parse-id <id> \
  --save-markdown-to ./parsed.md
```

This flow returns `document_parse_id`, combined `markdown_content`, per-file parse payloads, and extracted image URLs. Treat it as a document-analysis resource, not as a `presentation_id`.

## Custom template workflow

When the user provides their own PPTX, PPT, or PDF file as a design template, the presentation must be generated in **image mode**. This is not optional — the backend requires `--slide-mode image` for custom templates.

**How to recognize this scenario:** the user uploads or mentions a `.pptx` / `.ppt` / `.pdf` file that is clearly a *design template* (not a source document to extract content from). Clues include:
- "use this as my template" / "apply this design" / "match this style"
- The file is a short branded deck with placeholder content
- The user mentions "custom template" or "brand template"

**Step-by-step:**

```bash
# 1. Upload the SOURCE document(s) — the content to turn into slides
python scripts/upload_files.py --file ./quarterly-report.pdf

# 2. Upload the TEMPLATE file separately — this is the design, not source content
python scripts/upload_files.py --file ./brand-template.pptx
# The JSON output contains "file_id" — extract and save it for step 3

# 3. Generate the presentation in image mode with the custom template
#    Replace <template-file-id> with the file_id from step 2
python scripts/make_idempotency_key.py --prefix oneshot
python scripts/pdf_to_presentation.py \
  --file ./quarterly-report.pdf \
  --instruction "Create a 10-slide board update matching our brand style." \
  --slide-mode image \
  --image-model nano-banana-2 \
  --template-file-id <template-file-id> \
  --output-format pptx_image \
  --idempotency-key <key>

# 4. Wait and download
python scripts/wait_for_job.py --presentation-id <id> --download-to ./board_update.pptx
```

A logo can also be added (see "Custom logo" above) — just include `--logo-file-id <id>` in the command.

**Key rules:**
- The template file goes through `upload_files.py` first, then its `file_id` is passed via `--template-file-id`. Never pass the template as `--file` (that's for source documents).
- `--slide-mode image` is mandatory when using `--template-file-id`.
- Prefer `--output-format pptx_image` to preserve the generated visuals. Use `pdf` for review sharing.

## Image mode (Nano Banana)

Image mode uses Google's generative AI to create visually rich, image-based slides instead of HTML. The results look like professionally designed slides with custom graphics.

**When to use:**
- The user explicitly asks for image-style slides, visual-heavy design, or mentions "Nano Banana"
- The user provides a custom PPTX/PDF template (see Custom template workflow above)

| Image model | Tier | Quality |
|-------------|------|---------|
| `nano-banana-2` | Free | Fast, good for most cases |
| `nano-banana-pro` | Pro | Higher visual fidelity |

To add image mode to any standard workflow, include these flags:

```bash
--slide-mode image --image-model nano-banana-2
```

In image mode, export format matters:
- `--output-format pptx_image` — PPTX with images as-is (recommended for delivery)
- `--output-format pdf` — for review or read-only sharing
- `--output-format pptx` — only if the user explicitly needs editable slides

## Idempotency

Generate a fresh key before each create, edit, render, or export operation:

```bash
python scripts/make_idempotency_key.py --prefix parse
```

Reuse the same key only when retrying the exact same request after a transport failure. This prevents duplicate work and billing.

## Page count

Control the target slide count with `--page-count-range`. Valid values:

`4-8` · `8-12` · `12-16` · `16-20` · `20-30` · `30-40` · `40-50` · `50-100`

Default is `8-12`.

## Error handling

| Code | Meaning | What to do |
|------|---------|------------|
| `401` | Invalid or expired API key | Ask user to check or regenerate their key at https://tosea.ai |
| `402` | Insufficient credits | Report remaining credits; suggest purchasing more |
| `403` | Feature requires higher tier | Inform user which plan is needed |
| `404` | Resource not found | Verify `presentation_id` or `page_number` |
| `409` | Another workflow is already running | Wait for the active job or ask the user |
| `429` | Rate limited | Back off and retry after a delay |

For background jobs: `failed` status means the job error text should be reported to the user. `cancelled` is not success. Always keep the `presentation_id` for recovery.

## Export formats

| Format | Use case |
|--------|----------|
| `pptx` | Editable PowerPoint deck (default) |
| `pdf` | Read-only sharing or review |
| `pptx_image` | Image-mode PPTX preserving generated visuals |
| `html_zip` | HTML-mode decks only; not for image mode |

## Windows path handling

If source file paths contain non-ASCII characters (e.g., Chinese filenames), use a JSON manifest instead of passing paths directly:

```bash
python scripts/upload_files.py --manifest ./sources.json
```

Where `sources.json` contains:

```json
{
  "files": ["C:\\tosea-inputs\\report.pdf"]
}
```

See `examples/source-manifest.example.json` for reference.

## Optional MCP transport

If the host already provides a running `tosea` MCP server, the same workflows can be routed through MCP tools instead of local scripts. This is an optional MCP path — local scripts are the default and preferred runtime.

## Final answer format

After completing a workflow, always report:

- Which workflow was used (one-shot or staged)
- The `presentation_id`
- The terminal job outcome — use `data.job.status` when the response contains a nested job object
- Export filenames and download URLs when available
- Any quota or billing issues encountered
