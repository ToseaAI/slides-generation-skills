#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import (
    ApiError,
    add_common_auth_args,
    mutation_envelope,
    request_json,
    resolve_api_key,
    run_cli,
)


def main():
    parser = argparse.ArgumentParser(
        description="Fork a presentation into a new presentation using a different template."
    )
    add_common_auth_args(parser)
    parser.add_argument("--presentation-id", required=True, help="Presentation UUID.")
    parser.add_argument(
        "--template-name",
        default=None,
        help="Built-in template key such as beamer_classic or strategy_navy.",
    )
    parser.add_argument(
        "--user-template-id",
        default=None,
        help="User template UUID for image-mode custom template switching.",
    )
    parser.add_argument(
        "--system-template-key",
        default=None,
        help="System template key for image-mode template switching.",
    )
    parser.add_argument("--render-model", default=None)
    parser.add_argument("--logo-file-id", default=None)
    args = parser.parse_args()

    source_count = sum(
        1
        for value in (args.template_name, args.user_template_id, args.system_template_key)
        if isinstance(value, str) and value.strip()
    )
    if source_count != 1:
        raise ApiError(
            message="Exactly one of --template-name, --user-template-id, or --system-template-key must be provided.",
            detail={
                "error": "invalid_template_source_count",
                "template_name": args.template_name,
                "user_template_id": args.user_template_id,
                "system_template_key": args.system_template_key,
            },
            path=f"/presentations/{args.presentation_id}/switch-template",
        )

    api_key = resolve_api_key(args.api_key)
    request_payload = {
        "template_name": args.template_name,
        "user_template_id": args.user_template_id,
        "system_template_key": args.system_template_key,
        "render_model": args.render_model,
        "logo_file_id": args.logo_file_id,
    }
    path = f"/presentations/{args.presentation_id}/switch-template"
    response = request_json(
        "POST",
        path,
        api_key=api_key,
        base_url=args.base_url,
        json_body={k: v for k, v in request_payload.items() if v is not None},
    )
    return mutation_envelope(
        path=path,
        idempotency_key=None,
        response=response,
        request_payload=request_payload,
    )


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
