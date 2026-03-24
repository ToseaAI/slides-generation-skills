#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from _shared import (
    add_common_auth_args,
    emit_error,
    mutation_envelope,
    new_idempotency_key,
    request_json,
    resolve_api_key,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a presentation and queue one-shot generation.")
    add_common_auth_args(parser)
    parser.add_argument("--file", dest="files", action="append", required=True, help="Local source file path. Repeat for multiple files.")
    parser.add_argument("--instruction", default="", help="User instruction for the deck.")
    parser.add_argument("--output-format", default="pptx", help="pptx, pptx_image, pdf, or html_zip.")
    parser.add_argument("--render-provider", default="default")
    parser.add_argument("--render-model", default="gemini-3.1-pro-preview")
    parser.add_argument("--slide-domain", default="general")
    parser.add_argument("--page-count-range", default="8-12")
    parser.add_argument("--template-name", default="beamer_classic")
    parser.add_argument("--slide-mode", default="html", help="html or image.")
    parser.add_argument("--image-model", default=None)
    parser.add_argument("--idempotency-key", default=None)
    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    idempotency_key = args.idempotency_key or new_idempotency_key("one-shot")
    files = [("files", Path(value).resolve()) for value in args.files]
    request_payload = {
        "instruction": args.instruction,
        "output_format": args.output_format,
        "render_provider": args.render_provider,
        "render_model": args.render_model,
        "slide_domain": args.slide_domain,
        "page_count_range": args.page_count_range,
        "template_name": args.template_name,
        "slide_mode": args.slide_mode,
        "image_model": args.image_model,
    }
    try:
        response = request_json(
            "POST",
            "/pdf-to-presentation",
            api_key=api_key,
            base_url=args.base_url,
            idempotency_key=idempotency_key,
            form_fields={k: str(v) for k, v in request_payload.items() if v not in (None, "")},
            file_fields=files,
        )
    except Exception as exc:
        return emit_error(exc, idempotency_key=idempotency_key)

    payload = mutation_envelope(
        path="/pdf-to-presentation",
        idempotency_key=idempotency_key,
        response=response,
        request_payload=request_payload,
    )
    from _shared import emit_json

    emit_json(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
