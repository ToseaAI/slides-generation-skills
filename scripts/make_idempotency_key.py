#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _shared import emit_json, new_idempotency_key


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a fresh idempotency key.")
    parser.add_argument("--prefix", default=None, help="Optional short prefix for readability.")
    args = parser.parse_args()
    emit_json({"ok": True, "idempotency_key": new_idempotency_key(args.prefix)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
