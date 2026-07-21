#!/usr/bin/env python3
"""Validate PBS email notification settings before qsub.

Requirements:
  - ``#PBS -m abe`` (begin, end, abort)
  - A real recipient via either:
      * ``#PBS -M user@domain`` in the script, and/or
      * ``qsub -M user@domain`` at submission (checked via --email)
  - Placeholders rejected
  - Multiple comma-separated recipients allowed
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PLACEHOLDERS = {
    "your.email@domain.com",
    "user@example.com",
    "example@example.com",
    "replace@example.com",
}


def split_emails(value: str) -> List[str]:
    return [p.strip() for p in value.split(",") if p.strip()]


def parse_directives(path: Path) -> Tuple[List[str], List[str]]:
    recipients: List[str] = []
    modes: List[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("#PBS -M "):
            recipients.extend(split_emails(line.split(None, 2)[2].strip()))
        elif line.startswith("#PBS -m "):
            modes.append(line.split(None, 2)[2].strip())
    return recipients, modes


def valid_email(addr: str) -> bool:
    return addr not in PLACEHOLDERS and bool(EMAIL_RE.fullmatch(addr))


def validate_file(path: Path, submit_emails: List[str]) -> List[str]:
    errors: List[str] = []
    recipients, modes = parse_directives(path)

    if not modes:
        errors.append("missing #PBS -m directive")
    elif modes != ["abe"]:
        errors.append(f"#PBS -m must be exactly 'abe'; found {modes!r}")

    bad_tracked = [r for r in recipients if not valid_email(r)]
    if bad_tracked:
        errors.append(f"invalid/placeholder #PBS -M address(es): {bad_tracked!r}")

    # Must have recipients either in script or at qsub time
    if not recipients and not submit_emails:
        errors.append(
            "no mail recipient: add #PBS -M user@domain and/or pass --email for qsub -M"
        )

    for e in submit_emails:
        if not valid_email(e):
            errors.append(f"invalid --email recipient: {e!r}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--email",
        required=True,
        help="Private HPC notification recipient(s) for qsub -M (comma-separated ok)",
    )
    parser.add_argument("pbs_files", nargs="+", type=Path, help="PBS scripts to validate")
    args = parser.parse_args()

    submit_emails = split_emails(args.email.strip())
    if not submit_emails:
        print("ERROR: empty --email", file=sys.stderr)
        return 2

    failed = False
    for path in args.pbs_files:
        if not path.exists():
            print(f"ERROR: {path}: file does not exist", file=sys.stderr)
            failed = True
            continue
        errors = validate_file(path, submit_emails)
        if errors:
            failed = True
            for error in errors:
                print(f"ERROR: {path}: {error}", file=sys.stderr)
        else:
            tracked_m = parse_directives(path)[0]
            print(
                f"OK: {path}; #PBS -m abe"
                + (f"; #PBS -M {tracked_m}" if tracked_m else "")
                + f"; also submit with qsub -M {args.email!r} -m abe"
                + " and optional PBS_NOTIFY_EMAILS for mailx fallback"
            )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
