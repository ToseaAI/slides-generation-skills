# Example: One-shot Workflow

Turn a research PDF into a polished PPTX in four steps.

## 1. Generate a request key

```bash
python scripts/make_idempotency_key.py --prefix oneshot
```

## 2. Upload and create the deck

```bash
python scripts/upload_files.py --file ./research-paper.pdf

python scripts/pdf_to_presentation.py \
  --file ./research-paper.pdf \
  --instruction "Create a concise 8-slide summary focusing on key findings." \
  --output-format pptx \
  --template-name nature_science \
  --slide-domain natural_sciences \
  --render-model deepseek-chat-v3.1 \
  --idempotency-key <key>
```

On Windows with non-ASCII paths, use `--manifest`:

```bash
python scripts/upload_files.py --manifest ./sources.json
python scripts/pdf_to_presentation.py \
  --manifest ./sources.json \
  --instruction "Create a concise 8-slide summary." \
  --output-format pptx \
  --idempotency-key <key>
```

## 3. Wait for completion

```bash
python scripts/wait_for_job.py \
  --presentation-id <id> \
  --download-to ./research_summary.pptx
```

## 4. Optional: also export PDF

```bash
python scripts/make_idempotency_key.py --prefix pdf
python scripts/export_presentation.py \
  --presentation-id <id> \
  --output-format pdf \
  --idempotency-key <key>
python scripts/wait_for_job.py \
  --presentation-id <id> \
  --download-to ./research_summary.pdf
```

## What to report back

- `presentation_id`
- Final job status (check `data.job.status` when present)
- Filename and download URL
