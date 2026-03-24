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
    parser = argparse.ArgumentParser(description="Run AI outline edit on one page.")
    add_common_auth_args(parser)
    parser.add_argument("--presentation-id", required=True, help="Presentation UUID.")
    parser.add_argument("--page-number", required=True, type=int, help="Outline page number.")
    parser.add_argument("--action", required=True, choices=["modify", "insert"])
    parser.add_argument("--instruction", required=True)
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--after-slide", type=int, default=None)
    parser.add_argument("--idempotency-key", default=None)
    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    idempotency_key = args.idempotency_key or new_idempotency_key("outline-edit")
    request_payload = {
        "action": args.action,
        "instruction": args.instruction,
        "model_name": args.model_name,
        "after_slide": args.after_slide,
    }
    try:
        response = request_json(
            "POST",
            f"/presentations/{args.presentation_id}/outlines/{args.page_number}/ai-edit",
            api_key=api_key,
            base_url=args.base_url,
            idempotency_key=idempotency_key,
            json_body={k: v for k, v in request_payload.items() if v is not None},
        )
    except Exception as exc:
        return emit_error(exc, idempotency_key=idempotency_key)

    from _shared import emit_json

    emit_json(
        mutation_envelope(
            path=f"/presentations/{args.presentation_id}/outlines/{args.page_number}/ai-edit",
            idempotency_key=idempotency_key,
            response=response,
            request_payload=request_payload,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
