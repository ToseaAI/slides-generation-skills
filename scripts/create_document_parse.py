#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import (
    add_common_auth_args,
    emit_error,
    mutation_envelope,
    new_idempotency_key,
    request_json,
    resolve_source_file_ids,
    resolve_api_key,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload source files and queue a standalone document parse job.")
    add_common_auth_args(parser)
    parser.add_argument("--file", dest="files", action="append", default=[], help="Local source file path. Repeat for multiple files.")
    parser.add_argument("--file-id", dest="file_ids", action="append", default=[], help="Confirmed uploaded file_id. Repeat for multiple files.")
    parser.add_argument("--manifest", default=None, help="UTF-8 JSON manifest containing files and optional file_ids.")
    parser.add_argument("--instruction", default="", help="User instruction for parse and extraction scope.")
    parser.add_argument("--render-provider", default="default")
    parser.add_argument("--render-model", default="gemini-3.1-pro-preview")
    parser.add_argument("--slide-domain", default="general")
    parser.add_argument("--page-count-range", default="8-12")
    parser.add_argument("--template-name", default="beamer_classic")
    parser.add_argument(
        "--logo-file-id",
        default=None,
        help="Confirmed uploaded logo file_id. Do not pass a local path.",
    )
    parser.add_argument(
        "--template-file-id",
        default=None,
        help="Confirmed uploaded PPTX/PDF custom-template file_id. Requires --slide-mode image.",
    )
    parser.add_argument("--slide-mode", default="html", help="html or image.")
    parser.add_argument("--image-model", default=None)
    parser.add_argument("--idempotency-key", default=None)
    args = parser.parse_args()

    idempotency_key = args.idempotency_key or new_idempotency_key("docparse")
    try:
        api_key = resolve_api_key(args.api_key)
        file_ids, upload_results = resolve_source_file_ids(
            api_key=api_key,
            base_url=args.base_url,
            local_files=args.files,
            existing_file_ids=args.file_ids,
            manifest_path=args.manifest,
        )
    except Exception as exc:
        return emit_error(exc, idempotency_key=idempotency_key)
    request_payload = {
        "file_ids": file_ids,
        "instruction": args.instruction,
        "render_provider": args.render_provider,
        "render_model": args.render_model,
        "slide_domain": args.slide_domain,
        "page_count_range": args.page_count_range,
        "template_name": args.template_name,
        "logo_file_id": args.logo_file_id,
        "template_file_id": args.template_file_id,
        "slide_mode": args.slide_mode,
        "image_model": args.image_model,
    }
    try:
        response = request_json(
            "POST",
            "/document-parses/from-file-ids",
            api_key=api_key,
            base_url=args.base_url,
            idempotency_key=idempotency_key,
            json_body={k: v for k, v in request_payload.items() if v not in (None, "", [])},
        )
    except Exception as exc:
        return emit_error(exc, idempotency_key=idempotency_key)

    from _shared import emit_json
    payload = mutation_envelope(
        path="/document-parses/from-file-ids",
        idempotency_key=idempotency_key,
        response=response,
        request_payload=request_payload,
    )
    if upload_results:
        payload["uploads"] = upload_results
    emit_json(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
