#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import add_common_auth_args, request_json, resolve_api_key, run_cli


def main():
    parser = argparse.ArgumentParser(
        description="Fetch quota status for all features or one feature key."
    )
    add_common_auth_args(parser)
    parser.add_argument(
        "--feature-key",
        default=None,
        help="Optional feature key. Omit to fetch all quotas.",
    )
    args = parser.parse_args()
    api_key = resolve_api_key(args.api_key)
    path = (
        f"/permissions/quotas/{args.feature_key}/status"
        if args.feature_key
        else "/permissions/quotas/status"
    )
    return request_json("GET", path, api_key=api_key, base_url=args.base_url)


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
