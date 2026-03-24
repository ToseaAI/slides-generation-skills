#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import add_common_auth_args, request_json, resolve_api_key, run_cli


def main():
    parser = argparse.ArgumentParser(description="Check whether a quota operation is allowed.")
    add_common_auth_args(parser)
    parser.add_argument("--feature-key", required=True, help="Quota feature key to check.")
    parser.add_argument("--amount", type=int, default=1, help="Requested amount. Default: 1.")
    args = parser.parse_args()
    api_key = resolve_api_key(args.api_key)
    return request_json(
        "GET",
        f"/permissions/quotas/{args.feature_key}/check",
        api_key=api_key,
        base_url=args.base_url,
        query={"amount": args.amount},
    )


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
