#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Audit of M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.dat file for crack-tip node displacements and UEL variables.
"""

import os
import sys

ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
if not os.path.exists(ROOT):
    ROOT = "D:/Master thesis/Adaptive remeshing"

dat_path = os.path.join(ROOT, "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.dat")

def audit_dat():
    print("Auditing DAT file: %s (Size: %.2f MB)" % (dat_path, os.path.getsize(dat_path)/(1024.0*1024.0)))
    
    # Peak node from sliver-free mesh near crack tip:
    # Let's check node 4371 or center nodes around (0, 0)
    # Search for "NODE OUTPUT" blocks in Step 1, Step 2, Step 3, Step 4
    
    step_count = 0
    with open(dat_path, 'r') as f:
        for i, line in enumerate(f):
            if "STEP" in line and "INCREMENT" in line:
                print("Line %8d: %s" % (i, line.strip()))
                step_count += 1
                if step_count > 15:
                    break

if __name__ == "__main__":
    audit_dat()
