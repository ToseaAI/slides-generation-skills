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
        "tosea_pdf_to_presentation",
        "tosea_parse_pdf",
        "tosea_wait_for_job",
        "idempotency_key",
        "data.job.status",
        "`401`",
        "`402`",
        "`403`",
        "`404`",
        "`429`",
    ]
    for marker in required_skill_markers:
        if marker not in skill_text:
            print(f"SKILL.md must mention {marker}", file=sys.stderr)
            return 1

    examples = {
        "examples/one-shot-workflow.md": ["idempotency_key", "job.status"],
        "examples/staged-workflow.md": ["idempotency_key", "job.status"],
        "references/mcp-tools.md": ["html_zip", "data.job.status"],
        "references/operating-model.md": ["idempotency", "data.job"],
    }
    for relative, markers in examples.items():
        text = (root / relative).read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                print(f"{relative} must mention {marker}", file=sys.stderr)
                return 1

    metadata = (root / "agents/openai.yaml").read_text(encoding="utf-8")
    if "required_mcp_servers:" not in metadata or "- tosea" not in metadata:
        print("agents/openai.yaml must declare the tosea MCP server", file=sys.stderr)
        return 1

    print("skill validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
