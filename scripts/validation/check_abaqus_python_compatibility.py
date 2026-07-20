#!/usr/bin/env python3
"""Static scan for Abaqus-Python-incompatible syntax in CAE/postprocess scripts.

This checker runs under system Python. Final compile proof must use:
  abaqus python -c "import py_compile; py_compile.compile(...)"
"""

import argparse
import os
import re
import sys

DEFAULT_PATHS = [
    "scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py",
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


def scan_file(path):
    fh = open(path, "r")
    try:
        text = fh.read()
    finally:
        fh.close()
    issues = []
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for pattern, name in BANNED:
            if re.search(pattern, line):
                if name == "type annotation risk" and "variable_selection" in line:
                    continue
                if name == "type annotation risk" and re.search(r"['\"].*:", line):
                    continue
                issues.append("{0}:{1}: {2}: {3}".format(path, i, name, stripped))
    if re.search(r"""\bf["']""", text):
        if not any("f-string" in x for x in issues):
            issues.append("{0}: f-string pattern detected".format(path))
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=DEFAULT_PATHS)
    args = parser.parse_args()
    all_issues = []
    for p in args.paths:
        try:
            fh = open(p, "r")
            fh.close()
        except Exception:
            sys.stderr.write("MISSING {0}\n".format(p))
            return 2
        all_issues.extend(scan_file(p))
    # Require env-var I/O contract on the main case postprocessor.
    case_script = "scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py"
    if os.path.isfile(case_script):
        fh = open(case_script, "r")
        try:
            case_text = fh.read()
        finally:
            fh.close()
        for token in (
            "MOLNAR_CASE_ID",
            "MOLNAR_ODB_PATH",
            "MOLNAR_OUTPUT_DIR",
            "Missing MOLNAR_CASE_ID",
        ):
            if token not in case_text:
                all_issues.append(
                    "{0}: missing env-var I/O contract token {1}".format(
                        case_script, token
                    )
                )
        # Disallow positional argv path extraction patterns.
        if "args[0], args[1], args[2]" in case_text:
            all_issues.append(
                "{0}: still uses positional argv path triple".format(case_script)
            )
        if "sys.argv.index(\"--\")" in case_text or "sys.argv.index('--')" in case_text:
            all_issues.append(
                "{0}: still parses paths from argv after --".format(case_script)
            )

    if all_issues:
        print("ABAQUS_PYTHON_COMPATIBILITY_FAIL")
        for issue in all_issues:
            print(issue)
        return 2
    print("ABAQUS_PYTHON_COMPATIBILITY_PASS")
    for p in args.paths:
        print("ok {0}".format(p))
    print("env_var_io_contract=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
