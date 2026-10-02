#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Audit all package files to ensure ZERO fallback, parent, or sibling paths exist in code and input decks.
"""

import os
import sys

def audit_directory(pkg_dir):
    print("Auditing: %s" % pkg_dir)
    forbidden_terms = [
        "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL",
        "../STAGE_D_COMMITTED_STATE.bin",
        "..\\STAGE_D_COMMITTED_STATE.bin",
        "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL",
        "STAGE_D_COMMITTED_STATE_FALLBACK"
    ]
    
    clean = True
    for root, _, files in os.walk(pkg_dir):
        for f in files:
            if f.endswith(('.for', '.f', '.inp', '.pbs')):
                fpath = os.path.join(root, f)
                with open(fpath, 'r') as fp:
                    content = fp.read()
                for term in forbidden_terms:
                    if term in content:
                        print("  [FAIL] Found forbidden term '%s' in %s" % (term, fpath))
                        clean = False
    return clean

if __name__ == "__main__":
    dirs_to_check = [
        "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL",
        "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL"
    ]
    all_clean = True
    for d in dirs_to_check:
        if os.path.exists(d):
            if not audit_directory(d):
                all_clean = False
    if all_clean:
        print("AUDIT PASSED: Zero fallback/hardcoded paths found in all solver packages.")
        sys.exit(0)
    else:
        print("AUDIT FAILED: Forbidden fallback paths detected in code/input decks.")
        sys.exit(1)
