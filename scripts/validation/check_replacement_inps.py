#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Detailed Inp Checker for Replacement Stage-E Packages
"""

import os
import sys

def check_inp(inp_path):
    with open(inp_path, "r") as fp:
        lines = fp.readlines()
    props = []
    bcs = []
    equations = []
    for i, l in enumerate(lines):
        if "*UEL PROPERTY" in l.upper():
            props.append((i+1, l.strip(), lines[i+1].strip() if i+1 < len(lines) else ""))
        if "*BOUNDARY" in l.upper():
            bcs.append((i+1, l.strip(), lines[i+1].strip() if i+1 < len(lines) else ""))
        if "*EQUATION" in l.upper():
            equations.append(i+1)
    print("File: %s" % inp_path)
    print("  Props found: %s" % props)
    print("  BCs found  : %s" % bcs)
    print("  Total equations: %d" % len(equations))

def main():
    check_inp("models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL.inp")
    check_inp("models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL.inp")

if __name__ == "__main__":
    main()
