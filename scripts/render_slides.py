#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import (
    add_common_auth_args,
    mutation_envelope,
    parse_int_list,
    request_json,
    resolve_api_key,
    run_cli,
)


def main():
    parser = argparse.ArgumentParser(description="Queue slide rendering for a presentation.")
    add_common_auth_args(parser)
    parser.add_argument("--presentation-id", required=True, help="Presentation UUID.")
    parser.add_argument("--render-provider", default=None)
    parser.add_argument("--render-model", default=None)
    parser.add_argument("--image-model", default=None)
    parser.add_argument("--slides-to-generate", default=None, help="Comma-separated page numbers.")
    parser.add_argument("--force", action="store_true", help="Force re-render.")
    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    request_payload = {
        "presentation_id": args.presentation_id,
        "render_provider": args.render_provider,
        "render_model": args.render_model,
        "image_model": args.image_model,
        "force": args.force,
        "slides_to_generate": parse_int_list(args.slides_to_generate),
    }
    response = request_json(
        "POST",
        "/slides-render",
        api_key=api_key,
        base_url=args.base_url,
        json_body={k: v for k, v in request_payload.items() if v is not None},
    )
    return mutation_envelope(
        path="/slides-render",
        idempotency_key=None,
        response=response,
        request_payload=request_payload,
    )


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
