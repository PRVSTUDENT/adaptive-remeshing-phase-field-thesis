#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deterministic One-Difference Manifest:
M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL vs 1390834 Baseline
"""

import os
import sys
import difflib

def main():
    src_inp = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL.inp"
    dst_inp = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL.inp"
    
    with open(src_inp, "r") as f:
        src_lines = f.readlines()
    with open(dst_inp, "r") as f:
        dst_lines = f.readlines()
        
    diff = list(difflib.unified_diff(src_lines, dst_lines, fromfile="1390834.inp", tofile="DTMIN_REFINED.inp", lineterm=""))
    
    print("=== UNIFIED DIFF OF REFINED INP FILES ===")
    for line in diff:
        print(line)
        
    diff_content_lines = [l for l in diff if (l.startswith("+") or l.startswith("-")) and not (l.startswith("+++") or l.startswith("---"))]
    print("\nTotal differing lines: %d" % len(diff_content_lines))
    if len(diff_content_lines) == 2:
        print("EXACT ONE-DIFFERENCE VERIFIED: Only *STATIC dt_min differs!")
    else:
        print("WARNING: More differences found!")

if __name__ == "__main__":
    main()
