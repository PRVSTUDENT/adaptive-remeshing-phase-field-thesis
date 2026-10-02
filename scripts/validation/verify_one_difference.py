#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verify One-Difference Line-by-Line for Refined Replacement Package
"""

import os
import difflib

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    f1 = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL.inp")
    f2 = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL.inp")
    
    with open(f1, "r") as fp1:
        lines1 = fp1.readlines()
    with open(f2, "r") as fp2:
        lines2 = fp2.readlines()
        
    diff = list(difflib.unified_diff(lines1, lines2, fromfile="1391281_original", tofile="refined_r1_replacement"))
    
    print("================================================================================")
    print("UNIFIED DIFF OF INP DECKS (1391281 vs REFINED_R1):")
    print("================================================================================")
    for line in diff:
        print(line.rstrip())
        
if __name__ == "__main__":
    main()
