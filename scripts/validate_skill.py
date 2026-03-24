from __future__ import annotations

from pathlib import Path
import sys


REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "LICENSE",
    "agents/openai.yaml",
    "references/mcp-tools.md",
    "references/operating-model.md",
    "examples/one-shot-workflow.md",
    "examples/staged-workflow.md",
    "examples/source-manifest.example.json",
    "scripts/_shared.py",
    "scripts/make_idempotency_key.py",
    "scripts/health.py",
    "scripts/get_permissions_summary.py",
    "scripts/get_quota_status.py",
    "scripts/check_quota.py",
    "scripts/upload_files.py",
    "scripts/list_uploaded_files.py",
    "scripts/pdf_to_presentation.py",
    "scripts/parse_pdf.py",
    "scripts/generate_outline.py",
    "scripts/edit_outline_page.py",
    "scripts/render_slides.py",
    "scripts/edit_slide_page.py",
    "scripts/export_presentation.py",
    "scripts/wait_for_job.py",
    "scripts/list_presentations.py",
    "scripts/get_full_data.py",
    "scripts/list_exports.py",
    "scripts/list_export_files.py",
    "scripts/redownload_export.py",
]


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    missing = [relative for relative in REQUIRED_FILES if not (root / relative).exists()]
    if missing:
        for relative in missing:
            print(f"missing: {relative}", file=sys.stderr)
        return 1

    skill_text = (root / "SKILL.md").read_text(encoding="utf-8")
    required_skill_markers = [
        "python scripts/pdf_to_presentation.py",
        "python scripts/parse_pdf.py",
        "python scripts/upload_files.py",
        "--manifest",
        "python scripts/wait_for_job.py",
        "python scripts/edit_outline_page.py",
        "python scripts/edit_slide_page.py",
        "idempotency_key",
        "data.job.status",
        "`401`",
        "`402`",
        "`403`",
        "`404`",
        "`409`",
        "`429`",
        "optional MCP",
    ]
    for marker in required_skill_markers:
        if marker not in skill_text:
            print(f"SKILL.md must mention {marker}", file=sys.stderr)
            return 1

    examples = {
        "examples/one-shot-workflow.md": [
            "python scripts/pdf_to_presentation.py",
            "python scripts/upload_files.py",
            "--manifest",
            "idempotency_key",
            "data.job.status",
        ],
        "examples/staged-workflow.md": [
            "python scripts/parse_pdf.py",
            "python scripts/upload_files.py",
            "--manifest",
            "python scripts/edit_slide_page.py",
            "idempotency_key",
            "data.job.status",
        ],
        "references/mcp-tools.md": ["pdf_to_presentation.py", "upload_files.py", "--manifest", "html_zip", "data.job.status"],
        "references/operating-model.md": ["scripts-first", "idempotency", "optional", "--manifest"],
    }
    for relative, markers in examples.items():
        text = (root / relative).read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                print(f"{relative} must mention {marker}", file=sys.stderr)
                return 1

    metadata = (root / "agents/openai.yaml").read_text(encoding="utf-8")
    if "instructions_file: ../SKILL.md" not in metadata:
        print("agents/openai.yaml must point at SKILL.md", file=sys.stderr)
        return 1
    if "required_mcp_servers:" in metadata:
        print("agents/openai.yaml must not require MCP for scripts-first mode", file=sys.stderr)
        return 1

    print("skill validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
