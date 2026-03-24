#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import add_common_auth_args, request_json, resolve_api_key, run_cli


def main():
    parser = argparse.ArgumentParser(description="List presentations that have exports.")
    add_common_auth_args(parser)
    args = parser.parse_args()
    api_key = resolve_api_key(args.api_key)
    return request_json("GET", "/exports", api_key=api_key, base_url=args.base_url)


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
