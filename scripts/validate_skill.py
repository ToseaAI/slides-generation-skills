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
    if "tosea_pdf_to_presentation" not in skill_text:
        print("SKILL.md must mention tosea_pdf_to_presentation", file=sys.stderr)
        return 1
    if "tosea_wait_for_job" not in skill_text:
        print("SKILL.md must mention tosea_wait_for_job", file=sys.stderr)
        return 1

    metadata = (root / "agents/openai.yaml").read_text(encoding="utf-8")
    if "required_mcp_servers:" not in metadata or "- tosea" not in metadata:
        print("agents/openai.yaml must declare the tosea MCP server", file=sys.stderr)
        return 1

    print("skill validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

