#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import (
    add_common_auth_args,
    emit_error,
    maybe_base64_from_path,
    mutation_envelope,
    new_idempotency_key,
    request_json,
    resolve_api_key,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AI slide edit on one slide.")
    add_common_auth_args(parser)
    parser.add_argument("--presentation-id", required=True, help="Presentation UUID.")
    parser.add_argument("--page-number", required=True, type=int, help="Slide page number.")
    parser.add_argument("--action", required=True, choices=["modify", "insert"])
    parser.add_argument("--instruction", required=True)
    parser.add_argument("--edit-mode", default="outline_layout", choices=["outline_layout", "layout_only"])
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--image-model", default=None)
    parser.add_argument("--after-slide", type=int, default=None)
    parser.add_argument("--screenshot-path", default=None, help="Optional local screenshot file. Encoded as base64.")
    parser.add_argument("--screenshot-base64", default=None, help="Optional screenshot base64 string.")
    parser.add_argument("--idempotency-key", default=None)
    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    idempotency_key = args.idempotency_key or new_idempotency_key("slide-edit")
    screenshot_base64 = args.screenshot_base64 or maybe_base64_from_path(args.screenshot_path)
    request_payload = {
        "action": args.action,
        "instruction": args.instruction,
        "edit_mode": args.edit_mode,
        "model_name": args.model_name,
        "image_model": args.image_model,
        "after_slide": args.after_slide,
        "screenshot_base64": screenshot_base64,
    }
    try:
        response = request_json(
            "POST",
            f"/presentations/{args.presentation_id}/slides/{args.page_number}/ai-edit",
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
            path=f"/presentations/{args.presentation_id}/slides/{args.page_number}/ai-edit",
            idempotency_key=idempotency_key,
            response=response,
            request_payload={
                **request_payload,
                "screenshot_base64": "<provided>" if screenshot_base64 else None,
            },
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
