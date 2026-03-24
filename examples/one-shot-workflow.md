# Example: One-shot Workflow

1. Generate a request key:

```bash
python scripts/make_idempotency_key.py --prefix oneshot
```

2. Upload the source files through the product upload flow:

```bash
python scripts/upload_files.py \
  --file ./source.pdf \
  --file ./source.docx
```

Windows/OpenClaw alternative:

```bash
python scripts/upload_files.py --manifest ./sources.json
```

3. Create the deck:

```bash
python scripts/pdf_to_presentation.py \
  --file ./source.pdf \
  --file ./source.docx \
  --instruction "Create a crisp 6-slide executive deck." \
  --output-format pptx \
  --export-filename executive_deck_final.pptx \
  --render-model gemini-3.1-pro-preview \
  --idempotency-key <idempotency_key>
```

Windows/OpenClaw alternative:

```bash
python scripts/pdf_to_presentation.py \
  --manifest ./sources.json \
  --instruction "Create a crisp 6-slide executive deck." \
  --output-format pptx \
  --export-filename executive_deck_final.pptx \
  --render-model gemini-3.1-pro-preview \
  --idempotency-key <idempotency_key>
```

4. Poll completion:

```bash
python scripts/wait_for_job.py --presentation-id <presentation_id> --download-to ./executive_deck_final.pptx
```

5. Optional PDF export:

```bash
python scripts/make_idempotency_key.py --prefix pdf
python scripts/export_presentation.py --presentation-id <presentation_id> --output-format pdf --export-filename executive_deck_final.pdf --idempotency-key <idempotency_key>
python scripts/wait_for_job.py --presentation-id <presentation_id> --download-to ./executive_deck_final.pdf
```

Report back:

- `presentation_id`
- final status, using nested `data.job.status` when present
- produced filename
- download URL
- relay warning if OpenClaw, WeChat, email, or another downstream client must preserve filename, extension, and MIME
