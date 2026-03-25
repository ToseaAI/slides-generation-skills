# Example: Staged Workflow

Full control over outline and slides with edit checkpoints.

## 1. Parse the source document

```bash
python scripts/make_idempotency_key.py --prefix parse
python scripts/upload_files.py --file ./quarterly-report.pdf

python scripts/parse_pdf.py \
  --file ./quarterly-report.pdf \
  --instruction "Create a 12-slide board presentation." \
  --template-name strategy_navy \
  --slide-domain business \
  --idempotency-key <key>

python scripts/wait_for_job.py --presentation-id <id>
```

On Windows with non-ASCII paths, use `--manifest ./sources.json` instead of `--file`.

## 2. Generate outline

```bash
python scripts/generate_outline.py \
  --presentation-id <id> \
  --instruction "Emphasize revenue growth, risks, and next quarter priorities."

python scripts/wait_for_job.py --presentation-id <id>
```

## 3. Edit outline (optional)

```bash
python scripts/make_idempotency_key.py --prefix outline
python scripts/edit_outline_page.py \
  --presentation-id <id> \
  --page-number 2 \
  --action modify \
  --instruction "Sharpen this into a crisp executive summary." \
  --idempotency-key <key>
```

## 4. Render slides

```bash
python scripts/render_slides.py --presentation-id <id>
python scripts/wait_for_job.py --presentation-id <id>
```

## 5. Edit slides (optional)

```bash
python scripts/make_idempotency_key.py --prefix slide
python scripts/edit_slide_page.py \
  --presentation-id <id> \
  --page-number 4 \
  --action modify \
  --instruction "Replace the bullet list with a comparison table." \
  --edit-mode layout_only \
  --idempotency-key <key>
```

## 6. Export

```bash
python scripts/make_idempotency_key.py --prefix xp
python scripts/export_presentation.py \
  --presentation-id <id> \
  --output-format pptx \
  --idempotency-key <key>

python scripts/wait_for_job.py \
  --presentation-id <id> \
  --download-to ./board_presentation.pptx
```

## Inspect at any point

```bash
python scripts/get_full_data.py --presentation-id <id>
```

Returns the current outline, slide content, and speaker notes.

## What to report back

- `presentation_id`
- Final job status (check `data.job.status` when present)
- Filename and download URL
