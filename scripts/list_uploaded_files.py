#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import add_common_auth_args, request_json, resolve_api_key, run_cli


def main():
    parser = argparse.ArgumentParser(description="List uploaded files visible to the current API key.")
    add_common_auth_args(parser)
    parser.add_argument("--status", default=None, help="Optional status filter: pending, uploaded, confirmed, failed.")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    response = request_json(
        "GET",
        "/files",
        api_key=api_key,
        base_url=args.base_url,
        query={
            "status_filter": args.status,
            "limit": args.limit,
            "offset": args.offset,
        },
    )
    return {
        "ok": True,
        "response": response,
    }


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
