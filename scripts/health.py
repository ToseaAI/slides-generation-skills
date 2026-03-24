#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import add_common_auth_args, request_json, run_cli


def main():
    parser = argparse.ArgumentParser(description="Check ToseaAI MCP HTTP health.")
    add_common_auth_args(parser)
    args = parser.parse_args()
    return request_json("GET", "/health", api_key=None, base_url=args.base_url)


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
