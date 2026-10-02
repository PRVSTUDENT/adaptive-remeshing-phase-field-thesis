#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verify One-Difference for Final Stage-E Target Baselines:
1. Refined vs 1390527
2. Coarsened vs 1390528
"""

import os
import sys
import difflib

def check_diff(src_inp, dst_inp, label):
    with open(src_inp, "r") as f:
        src_lines = f.readlines()
    with open(dst_inp, "r") as f:
        dst_lines = f.readlines()
        
    diff = list(difflib.unified_diff(src_lines, dst_lines, fromfile="BASELINE.inp", tofile="TARGET_DTMIN.inp", lineterm=""))
    print("\n================================================================================")
    print("UNIFIED DIFF FOR %s:" % label)
    print("================================================================================")
    for line in diff:
        print(line)
        
    diff_lines = [l for l in diff if (l.startswith("+") or l.startswith("-")) and not (l.startswith("+++") or l.startswith("---"))]
    print("Total differing lines: %d" % len(diff_lines))

def main():
    # 1. Refined
    src_ref = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL/M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL.inp"
    dst_ref = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL.inp"
    check_diff(src_ref, dst_ref, "REFINED TARGET BASELINE")
    
    # 2. Coarsened
    src_coarse = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL/M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL.inp"
    dst_coarse = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL.inp"
    check_diff(src_coarse, dst_coarse, "COARSENED TARGET BASELINE")

if __name__ == "__main__":
    main()
