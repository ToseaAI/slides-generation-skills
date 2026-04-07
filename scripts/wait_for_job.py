#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from _shared import (
    add_common_auth_args,
    extract_terminal_status,
    request_download,
    request_json,
    resolve_api_key,
    run_cli,
    wait_for_job,
)


def _resolve_download_target(
    download_to: str, download_url: str, job_filename: str | None = None
) -> Path:
    target = Path(download_to)
    if download_to.endswith(("\\", "/")) or target.is_dir():
        parsed_url = urlparse(download_url)
        query = parse_qs(parsed_url.query)
        filename = (
            job_filename
            or (query.get("download") or [None])[0]
            or Path(parsed_url.path).name
            or "download.bin"
        )
        return target / filename
    return target


def main():
    parser = argparse.ArgumentParser(description="Poll a background job until it reaches a terminal state.")
    add_common_auth_args(parser)
    parser.add_argument("--presentation-id", default=None, help="Presentation UUID.")
    parser.add_argument("--document-parse-id", default=None, help="Document parse UUID.")
    parser.add_argument("--interval", type=int, default=3, help="Polling interval in seconds.")
    parser.add_argument("--timeout", type=int, default=900, help="Timeout in seconds.")
    parser.add_argument(
        "--download-to",
        default=None,
        help="Optional local file or directory path. If set, download the final job artifact.",
    )
    args = parser.parse_args()
    if bool(args.presentation_id) == bool(args.document_parse_id):
        raise SystemExit("Pass exactly one of --presentation-id or --document-parse-id.")
    api_key = resolve_api_key(args.api_key)
    if args.document_parse_id:
        import time

        deadline = time.monotonic() + args.timeout
        response = None
        while time.monotonic() <= deadline:
            response = request_json(
                "GET",
                f"/document-parses/{args.document_parse_id}",
                api_key=api_key,
                base_url=args.base_url,
            )
            if extract_terminal_status(response) in {"completed", "failed", "cancelled"}:
                break
            time.sleep(args.interval)
        if response is None or extract_terminal_status(response) not in {"completed", "failed", "cancelled"}:
            raise SystemExit("Timed out waiting for document parse completion.")
    else:
        response = wait_for_job(
            presentation_id=args.presentation_id,
            api_key=api_key,
            base_url=args.base_url,
            interval_seconds=args.interval,
            timeout_seconds=args.timeout,
        )
    payload = {
        "ok": True,
        "terminal_status": extract_terminal_status(response),
        "response": response,
    }
    data = response.get("data") or {}
    job = data.get("job") or {}
    download_url = job.get("download_url") if isinstance(job, dict) else None
    job_filename = job.get("filename") if isinstance(job, dict) else None
    if args.download_to and download_url:
        target = _resolve_download_target(args.download_to, download_url, job_filename)
        saved_path = request_download(download_url, target)
        payload["saved_to"] = str(saved_path.resolve())
    return payload


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
