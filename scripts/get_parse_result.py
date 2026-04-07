#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from _shared import add_common_auth_args, request_json, resolve_api_key, run_cli


def main():
    parser = argparse.ArgumentParser(
        description="Fetch the final Markdown and per-file parse payload for a document parse job."
    )
    add_common_auth_args(parser)
    parser.add_argument("--document-parse-id", required=True, help="Document parse UUID.")
    parser.add_argument(
        "--save-markdown-to",
        default=None,
        help="Optional local path to write the combined markdown_content.",
    )
    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    response = request_json(
        "GET",
        f"/document-parses/{args.document_parse_id}/result",
        api_key=api_key,
        base_url=args.base_url,
    )

    payload = {
        "ok": True,
        "document_parse_id": args.document_parse_id,
        "response": response,
    }

    if args.save_markdown_to:
        markdown = (
            ((response.get("data") or {}).get("markdown_content"))
            if isinstance(response, dict)
            else None
        ) or ""
        destination = Path(args.save_markdown_to)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(markdown, encoding="utf-8")
        payload["saved_markdown_to"] = str(destination.resolve())

    return payload


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
