#!/usr/bin/env python3
"""Static scan for Abaqus-Python-incompatible syntax in CAE/postprocess scripts.

This checker runs under system Python. Final compile proof must use:
  abaqus python -c "import py_compile; py_compile.compile(...)"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_PATHS = [
    "scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py",
    "scripts/abaqus_cae/postprocess_molnar_h_convergence_combined.py",
]

# Patterns that failed or are high-risk under older Abaqus Python interpreters.
BANNED = [
    (r"\bf['\"]", "f-string"),
    (r"from __future__ import annotations", "future annotations"),
    (r"\bpathlib\b", "pathlib"),
    (r"\bdataclasses\b", "dataclasses"),
    (r"exist_ok\s*=", "os.makedirs exist_ok"),
    (r"subprocess\.run\b", "subprocess.run"),
    (r"open\([^)]*encoding\s*=", "open(..., encoding=...)"),
    (r"^\s*def\s+\w+\([^)]*\)\s*->", "function return annotation"),
    (r":\s*(list|dict|tuple|str|int|float|bool|Path|Optional|None)\b", "type annotation risk"),
]


def scan_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    issues = []
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        # Skip pure comments
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for pattern, name in BANNED:
            if re.search(pattern, line):
                # Allow dict literal "None" false positives carefully
                if name == "type annotation risk" and "variable_selection" in line:
                    continue
                if name == "type annotation risk" and re.search(r"['\"].*:", line):
                    continue
                issues.append(f"{path}:{i}: {name}: {stripped}")
    # Extra f-string check for multi-token forms
    if re.search(r"""\bf["']""", text):
        if not any("f-string" in x for x in issues):
            issues.append(f"{path}: f-string pattern detected")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=DEFAULT_PATHS)
    args = parser.parse_args()
    all_issues = []
    for p in args.paths:
        path = Path(p)
        if not path.exists():
            print(f"MISSING {path}", file=sys.stderr)
            return 2
        all_issues.extend(scan_file(path))
    if all_issues:
        print("ABAQUS_PYTHON_COMPATIBILITY_FAIL")
        for issue in all_issues:
            print(issue)
        return 2
    print("ABAQUS_PYTHON_COMPATIBILITY_PASS")
    for p in args.paths:
        print(f"ok {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
