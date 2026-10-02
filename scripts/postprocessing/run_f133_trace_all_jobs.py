#!/usr/bin/env python3
"""
F133DIAG Mechanical BC Lineage & Generator Tracing Script
Task ID: F133DIAG-M2-INTENDED-BC-AND-CORRECTED-BASELINE-DEFINITION-RECONCILIATION1
"""

import sys
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def find_all_inp_and_py():
    inp_files = list(ROOT.glob("**/*.inp"))
    py_files = list(ROOT.glob("**/*.py"))
    return inp_files, py_files

def audit_file(p):
    content = p.read_text(encoding="utf-8", errors="ignore")
    has_top_u2_fixed = False
    if "top_nodes, 2, 2" in content or "top_nodes, 2" in content or "N_TOP, 2, 2" in content:
        has_top_u2_fixed = True
    return has_top_u2_fixed

def main():
    inp_files, py_files = find_all_inp_and_py()
    print("================================================================================")
    print("F133DIAG LINEAGE TRACE FOR TOP U2 CONSTRAINT")
    print("================================================================================")

    print("\n--- INP Files with top_nodes, 2, 2 ---")
    for p in inp_files:
        if audit_file(p):
            rel = p.relative_to(ROOT)
            print(f"  [INP] {rel}")

    print("\n--- Python Generator Scripts mentioning top_nodes or N_TOP ---")
    for p in py_files:
        content = p.read_text(encoding="utf-8", errors="ignore")
        if "top_nodes" in content or "N_TOP" in content or "top_nodes, 2" in content:
            rel = p.relative_to(ROOT)
            has_fixed = "top_nodes, 2" in content or "top_nodes, 2, 2" in content
            print(f"  [PY] {rel} (fixed_top_u2={has_fixed})")

if __name__ == "__main__":
    main()
