# Example: Staged Workflow

1. Upload and parse with a fresh request key:

```bash
python scripts/upload_files.py --file ./source.pdf --file ./source.docx
python scripts/upload_files.py --manifest ./sources.json  # Windows/OpenClaw alternative
python scripts/make_idempotency_key.py --prefix parse
python scripts/parse_pdf.py --file ./source.pdf --file ./source.docx --instruction "Create a 6-slide operating review." --render-model gemini-3.1-pro-preview --idempotency-key <idempotency_key>
python scripts/parse_pdf.py --manifest ./sources.json --instruction "Create a 6-slide operating review." --render-model gemini-3.1-pro-preview --idempotency-key <idempotency_key>  # Windows/OpenClaw alternative
python scripts/wait_for_job.py --presentation-id <presentation_id>
```

2. Generate and revise outline:

```bash
python scripts/generate_outline.py --presentation-id <presentation_id> --instruction "Emphasize executive summary, risks, and owners."
python scripts/wait_for_job.py --presentation-id <presentation_id>
python scripts/make_idempotency_key.py --prefix outline-edit
python scripts/edit_outline_page.py --presentation-id <presentation_id> --page-number 2 --action modify --instruction "Make this page a sharper executive summary." --idempotency-key <idempotency_key>
```

3. Render and revise slides:

```bash
python scripts/render_slides.py --presentation-id <presentation_id> --render-model gemini-3.1-pro-preview --force
python scripts/wait_for_job.py --presentation-id <presentation_id>
python scripts/make_idempotency_key.py --prefix slide-edit
python scripts/edit_slide_page.py --presentation-id <presentation_id> --page-number 2 --action modify --instruction "Use a stronger title and fewer bullets." --edit-mode layout_only --idempotency-key <idempotency_key>
```

4. Export:

```bash
python scripts/make_idempotency_key.py --prefix xp
python scripts/export_presentation.py --presentation-id <presentation_id> --output-format pptx --export-filename staged_review_final.pptx --idempotency-key <idempotency_key>
python scripts/wait_for_job.py --presentation-id <presentation_id> --download-to ./staged_review_final.pptx
```

Use this path when the user asks for outline changes, inserted slides, or iteration after review.

For the export step, use nested `data.job.status` from the jobs payload when present. If the file will be relayed through OpenClaw, WeChat, email, or another chat surface, preserve filename, extension, and MIME metadata.
