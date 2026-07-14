#!/usr/bin/env python3
"""Starter Abaqus input-deck integrity checker.

This checker is intentionally conservative and dependency-free. It can run
without a deck to verify the tool path, and it performs simple keyword/set
checks once an input deck is supplied.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_KEYWORDS = [
    "*User Element",
    "*UEL Property",
]

REQUIRED_OUTPUT_TOKENS = [
    "MISESERI",
    "MISESAVG",
    "S",
    "EVOL",
    "U",
    "RF",
    "SDV",
]

REQUIRED_SET_TOKENS = [
    "All_elem",
    "umatelem",
]


def check_text(text: str, require_remeshing_outputs: bool) -> list[str]:
    errors: list[str] = []
    lower_text = text.lower()

    for keyword in REQUIRED_KEYWORDS:
        if keyword.lower() not in lower_text:
            errors.append(f"missing keyword: {keyword}")

    for token in REQUIRED_SET_TOKENS:
        if token.lower() not in lower_text:
            errors.append(f"missing required set/token: {token}")

    if require_remeshing_outputs:
        for token in REQUIRED_OUTPUT_TOKENS:
            if token.lower() not in lower_text:
                errors.append(f"missing requested output token: {token}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck", nargs="?", type=Path, help="Abaqus .inp deck to inspect")
    parser.add_argument("--require-remeshing-outputs", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Check only; never writes files")
    args = parser.parse_args()

    if args.deck is None:
        print("No deck supplied; placeholder integrity check passed (no files written).")
        return 0

    if not args.deck.exists():
        print(f"Deck not found: {args.deck}", file=sys.stderr)
        return 2

    text = args.deck.read_text(encoding="utf-8", errors="ignore")
    errors = check_text(text, args.require_remeshing_outputs)
    if errors:
        print("Deck integrity check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    mode = "dry-run " if args.dry_run else ""
    print(f"Deck integrity check passed ({mode}no files written): {args.deck}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
