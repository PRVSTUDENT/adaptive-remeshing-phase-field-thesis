#!/usr/bin/env python3
"""Validate PBS email notification settings before qsub.

Tracked PBS scripts must request begin/end/abort notifications with
``#PBS -m abe`` while the private recipient is supplied at submission time
with ``qsub -M``. This checker validates the private address format, rejects
tracked ``#PBS -M`` placeholders, and confirms the required mail points.
"""

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


def parse_directives(path: Path) -> Tuple[List[str], List[str]]:
    recipients = []  # type: List[str]
    modes = []  # type: List[str]
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("#PBS -M "):
            recipients.append(line.split(None, 2)[2].strip())
        elif line.startswith("#PBS -m "):
            modes.append(line.split(None, 2)[2].strip())
    return recipients, modes


def validate_file(path: Path) -> List[str]:
    errors = []  # type: List[str]
    recipients, modes = parse_directives(path)
    if recipients:
        errors.append(f"tracked script must not contain #PBS -M; pass the private recipient with qsub -M instead; found {recipients!r}")

    if not modes:
        errors.append("missing #PBS -m directive")
    elif modes != ["abe"]:
        errors.append(f"#PBS -m must be exactly 'abe'; found {modes!r}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, help="Private HPC notification recipient to pass with qsub -M")
    parser.add_argument("pbs_files", nargs="+", type=Path, help="PBS scripts to validate")
    args = parser.parse_args()

    email = args.email.strip()
    if email in PLACEHOLDERS or not EMAIL_RE.fullmatch(email):
        print(f"ERROR: invalid or placeholder email address: {email!r}", file=sys.stderr)
        return 2

    failed = False
    for path in args.pbs_files:
        if not path.exists():
            print(f"ERROR: {path}: file does not exist", file=sys.stderr)
            failed = True
            continue
        errors = validate_file(path)
        if errors:
            failed = True
            for error in errors:
                print(f"ERROR: {path}: {error}", file=sys.stderr)
        else:
            print(f"OK: {path}; submit with qsub -M {email!r} -m abe ...")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
