#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import add_common_auth_args, emit_error, emit_json, resolve_api_key, resolve_source_file_ids


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Upload one or more local files through the three-step Tosea upload flow and return file_ids."
    )
    add_common_auth_args(parser)
    parser.add_argument(
        "--file",
        dest="files",
        action="append",
        default=[],
        help="Local file path. Repeat for multiple files.",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="UTF-8 JSON manifest containing files and optional file_ids.",
    )
    args = parser.parse_args()

    try:
        api_key = resolve_api_key(args.api_key)
        file_ids, upload_results = resolve_source_file_ids(
            api_key=api_key,
            base_url=args.base_url,
            local_files=args.files,
            existing_file_ids=[],
            manifest_path=args.manifest,
        )
    except Exception as exc:
        return emit_error(exc)
    emit_json(
        {
            "ok": True,
            "file_ids": file_ids,
            "uploads": upload_results,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
