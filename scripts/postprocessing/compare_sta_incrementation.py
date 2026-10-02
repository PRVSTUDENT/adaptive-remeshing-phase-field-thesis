#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deep Incrementation and Convergence Comparison: 1390447 vs 1390533
"""

import os
import sys

def main():
    sta1_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.sta"
    sta2_path = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_CONTROL_VAL/M2CORR_STAGE_E_DONOR_CONTROL_VAL.sta"
    
    with open(sta1_path, "r") as fp:
        lines1 = [l.strip() for l in fp if l.strip().startswith("1")]
    with open(sta2_path, "r") as fp:
        lines2 = [l.strip() for l in fp if l.strip().startswith("1")]
        
    print("================================================================================")
    print("HISTORICAL 1390447 INCREMENTS 18-35 (DEFAULT CONTROLS):")
    print("================================================================================")
    for l in lines1[17:35]:
        print("  ", l)
        
    print("\n================================================================================")
    print("REVISED 1390533 INCREMENTS 18-35 (CONTINUATION CONTROLS):")
    print("================================================================================")
    for l in lines2[17:35]:
        print("  ", l)

if __name__ == "__main__":
    main()
