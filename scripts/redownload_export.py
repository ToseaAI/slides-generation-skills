#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import (
    add_common_auth_args,
    request_download,
    request_json,
    resolve_api_key,
    run_cli,
)


def main():
    parser = argparse.ArgumentParser(description="Get a new download URL for an existing export.")
    add_common_auth_args(parser)
    parser.add_argument("--presentation-id", required=True, help="Presentation UUID.")
    parser.add_argument("--export-type", required=True, help="pptx, pptx_image, pdf, or html_zip.")
    parser.add_argument("--filename", required=True, help="Existing export filename.")
    parser.add_argument(
        "--download-to",
        default=None,
        help="Optional local path to save the downloaded file.",
    )
    args = parser.parse_args()
    api_key = resolve_api_key(args.api_key)
    response = request_json(
        "GET",
        f"/exports/{args.presentation_id}/download/{args.export_type}",
        api_key=api_key,
        base_url=args.base_url,
        query={"filename": args.filename},
    )
    payload = {"ok": True, "response": response}
    download_url = ((response.get("data") or {}).get("download_url"))
    if args.download_to and download_url:
        saved_path = request_download(download_url, args.download_to)
        payload["saved_to"] = str(saved_path.resolve())
    return payload


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
