#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import (
    add_common_auth_args,
    emit_error,
    mutation_envelope,
    new_idempotency_key,
    request_json,
    resolve_api_key,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Queue an export job for a presentation.")
    add_common_auth_args(parser)
    parser.add_argument("--presentation-id", required=True, help="Presentation UUID.")
    parser.add_argument("--output-format", required=True, help="pptx, pptx_image, pdf, or html_zip.")
    parser.add_argument("--idempotency-key", default=None)
    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    idempotency_key = args.idempotency_key or new_idempotency_key("export")
    request_payload = {
        "presentation_id": args.presentation_id,
        "output_format": args.output_format,
    }
    try:
        response = request_json(
            "POST",
            "/export",
            api_key=api_key,
            base_url=args.base_url,
            idempotency_key=idempotency_key,
            json_body=request_payload,
        )
    except Exception as exc:
        return emit_error(exc, idempotency_key=idempotency_key)

    from _shared import emit_json

    emit_json(
        mutation_envelope(
            path="/export",
            idempotency_key=idempotency_key,
            response=response,
            request_payload=request_payload,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
