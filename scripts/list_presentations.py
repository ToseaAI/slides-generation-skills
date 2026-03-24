#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import add_common_auth_args, request_json, resolve_api_key, run_cli


def main():
    parser = argparse.ArgumentParser(description="List presentations available to the API key.")
    add_common_auth_args(parser)
    parser.add_argument("--page", type=int, default=1, help="1-based page index.")
    parser.add_argument("--per-page", type=int, default=20, help="Items per page.")
    parser.add_argument("--status", default=None, help="Optional presentation status filter.")
    parser.add_argument("--search", default=None, help="Optional search string.")
    args = parser.parse_args()
    api_key = resolve_api_key(args.api_key)
    return request_json(
        "GET",
        "/presentations",
        api_key=api_key,
        base_url=args.base_url,
        query={
            "page": args.page,
            "per_page": args.per_page,
            "status": args.status,
            "search": args.search,
        },
    )


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
