#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Abaqus Input Deck & Preprocessor Output Preflight Validator
===========================================================
Validates input decks (.inp) and preprocessor listing files (.dat) against:
1. Maximum 16 items per data line in *NSET and *ELSET (Abaqus free-format limit).
2. Detection of truncated line or deleted item preprocessor warnings.
3. Node set and element set completeness and cardinality.
"""

import os
import sys
import argparse
import re

def audit_inp_deck(inp_path, max_items_per_line=16):
    print("=== AUDITING INPUT DECK: %s ===" % inp_path)
    if not os.path.exists(inp_path):
        print("[FAIL] Input deck not found: %s" % inp_path)
        return False, {}

    violations = []
    sets_cardinality = {}
    current_set_type = None
    current_set_name = None
    
    with open(inp_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            line_s = line.strip()
            if line_s.startswith("**") or not line_s:
                continue
            
            if line_s.startswith("*"):
                # Keyword line
                line_u = line_s.upper()
                if line_u.startswith("*NSET"):
                    current_set_type = "NSET"
                    m = re.search(r"NSET\s*=\s*([A-Za-z0-9_\-]+)", line_s, re.I)
                    current_set_name = m.group(1) if m else "UNKNOWN_NSET"
                    if current_set_name not in sets_cardinality:
                        sets_cardinality[current_set_name] = 0
                elif line_u.startswith("*ELSET"):
                    current_set_type = "ELSET"
                    m = re.search(r"ELSET\s*=\s*([A-Za-z0-9_\-]+)", line_s, re.I)
                    current_set_name = m.group(1) if m else "UNKNOWN_ELSET"
                    if current_set_name not in sets_cardinality:
                        sets_cardinality[current_set_name] = 0
                else:
                    current_set_type = None
                    current_set_name = None
            else:
                # Data line
                if current_set_type in ["NSET", "ELSET"]:
                    items = [p.strip() for p in line_s.split(",") if p.strip()]
                    if len(items) > max_items_per_line:
                        violations.append({
                            'line_num': line_num,
                            'set_type': current_set_type,
                            'set_name': current_set_name,
                            'item_count': len(items),
                            'snippet': line_s[:100]
                        })
                    sets_cardinality[current_set_name] += len(items)

    passed = len(violations) == 0
    if passed:
        print("[PASS] Zero line-length violations found across all *NSET and *ELSET cards.")
    else:
        print("[FAIL] Found %d lines exceeding the %d-item limit:" % (len(violations), max_items_per_line))
        for v in violations:
            print("  Line %6d [%s: %s]: %d items (> %d)" % (
                v['line_num'], v['set_type'], v['set_name'], v['item_count'], max_items_per_line
            ))
            print("    Snippet: %s..." % v['snippet'])

    print("\nParsed Set Cardinalities:")
    for s_name, count in sorted(sets_cardinality.items()):
        print("  %-25s: %d entries" % (s_name, count))

    return passed, sets_cardinality

def audit_dat_file(dat_path):
    print("\n=== AUDITING PREPROCESSOR DAT FILE: %s ===" % dat_path)
    if not os.path.exists(dat_path):
        print("[SKIP] .dat file not provided or not found.")
        return True, []

    warnings = []
    pre_errors = []
    truncated_lines = []
    deleted_items = []

    with open(dat_path, 'r', encoding='utf-8', errors='ignore') as f:
        in_preprocessor = True
        for line_num, line in enumerate(f, 1):
            line_l = line.lower()
            if 'end processing part, instance, and assembly information' in line_l or 'abaqus/standard datacheck' in line_l:
                in_preprocessor = False
            
            if '***warning' in line_l:
                warnings.append((line_num, line.strip()))
                if 'truncated' in line_l:
                    truncated_lines.append((line_num, line.strip()))
                if 'deleted' in line_l:
                    deleted_items.append((line_num, line.strip()))
            if '***error' in line_l:
                pre_errors.append((line_num, line.strip()))

    print("Summary:")
    print("  Total Warnings: %d" % len(warnings))
    print("  Pre Errors:     %d" % len(pre_errors))
    print("  Truncated Line Warnings: %d" % len(truncated_lines))
    print("  Deleted Item Warnings:   %d" % len(deleted_items))

    if truncated_lines or deleted_items or pre_errors:
        print("[FAIL] Severe preprocessor defects detected in .dat file!")
        for ln, msg in truncated_lines:
            print("  DAT L%5d (Truncation): %s" % (ln, msg))
        for ln, msg in deleted_items:
            print("  DAT L%5d (Deletion):   %s" % (ln, msg))
        for ln, msg in pre_errors:
            print("  DAT L%5d (Error):      %s" % (ln, msg))
        return False, warnings
    else:
        print("[PASS] Zero preprocessor truncation, deletion, or keyword errors found.")
        return True, warnings

def main():
    parser = argparse.ArgumentParser(description="Abaqus Input & Preprocessor Preflight Validator")
    parser.add_argument("inp_file", help="Path to .inp deck")
    parser.add_argument("--dat_file", help="Path to .dat output listing file (optional)", default=None)
    args = parser.parse_args()

    inp_pass, sets = audit_inp_deck(args.inp_file)
    dat_pass = True
    if args.dat_file:
        dat_pass, _ = audit_dat_file(args.dat_file)

    if inp_pass and dat_pass:
        print("\n[SUCCESS] Preflight validation PASSED.")
        sys.exit(0)
    else:
        print("\n[ERROR] Preflight validation FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
