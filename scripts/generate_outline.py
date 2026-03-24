#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import add_common_auth_args, mutation_envelope, request_json, resolve_api_key, run_cli


def main():
    parser = argparse.ArgumentParser(description="Queue outline generation for a presentation.")
    add_common_auth_args(parser)
    parser.add_argument("--presentation-id", required=True, help="Presentation UUID.")
    parser.add_argument("--instruction", default="", help="Outline generation instruction.")
    parser.add_argument("--render-provider", default=None)
    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    response = request_json(
        "POST",
        "/outline-generate",
        api_key=api_key,
        base_url=args.base_url,
        json_body={
            "presentation_id": args.presentation_id,
            "instruction": args.instruction,
            "render_provider": args.render_provider,
        },
    )
    return mutation_envelope(
        path="/outline-generate",
        idempotency_key=None,
        response=response,
        request_payload={
            "presentation_id": args.presentation_id,
            "instruction": args.instruction,
            "render_provider": args.render_provider,
        },
    )


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
