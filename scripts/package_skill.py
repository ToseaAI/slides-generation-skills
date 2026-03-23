from __future__ import annotations

import argparse
from pathlib import Path
import zipfile


INCLUDE_PATHS = [
    "SKILL.md",
    "README.md",
    "LICENSE",
    "agents",
    "references",
    "examples",
]


def add_path(bundle: zipfile.ZipFile, root: Path, relative: str) -> None:
    target = root / relative
    if target.is_dir():
        for child in sorted(target.rglob("*")):
            if child.is_file():
                bundle.write(child, child.relative_to(root))
    elif target.is_file():
        bundle.write(target, target.relative_to(root))


def main() -> int:
    parser = argparse.ArgumentParser(description="Package the ToseaAI skill for release.")
    parser.add_argument("--version", required=True, help="Release version, for example 0.1.0")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    dist = root / "dist"
    dist.mkdir(exist_ok=True)
    zip_path = dist / f"tosea-slides-skill-v{args.version}.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for relative in INCLUDE_PATHS:
            add_path(bundle, root, relative)

    print(zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
