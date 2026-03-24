#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import add_common_auth_args, request_json, resolve_api_key, run_cli


def main():
    parser = argparse.ArgumentParser(description="Fetch the full presentation payload.")
    add_common_auth_args(parser)
    parser.add_argument("--presentation-id", required=True, help="Presentation UUID.")
    args = parser.parse_args()
    api_key = resolve_api_key(args.api_key)
    return request_json(
        "GET",
        f"/presentations/{args.presentation_id}/full-data",
        api_key=api_key,
        base_url=args.base_url,
    )


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
