#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Audit STA attempts in 1390552.sta vs 1390447.sta
"""

import os
import sys

def audit_sta(sta_path):
    with open(sta_path, 'r') as fp:
        lines = fp.readlines()
    attempts = []
    cutback_count = 0
    for l in lines:
        parts = l.split()
        if len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit():
            att_str = parts[2]
            if 'U' in att_str:
                cutback_count += 1
                att_str = att_str.replace('U', '')
            if att_str.isdigit():
                attempts.append(int(att_str))
    return {
        "total_increments": len(attempts) - cutback_count,
        "total_attempts": len(attempts),
        "total_cutbacks": cutback_count,
        "max_attempt": max(attempts) if attempts else 0,
        "attempts_histogram": {a: attempts.count(a) for a in sorted(set(attempts))},
        "attempts_6_to_12_exercised": any(a >= 6 for a in attempts)
    }

def main():
    sta1 = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.sta"
    sta2 = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL.sta"
    
    a1 = audit_sta(sta1)
    a2 = audit_sta(sta2)
    
    print("================================================================================")
    print("STA ATTEMPTS & CUTBACK COMPARISON:")
    print("================================================================================")
    print("Historical 1390447: Max Attempt = %d, Cutbacks = %d, Attempts >= 6 Exercised = %s" % (
        a1["max_attempt"], a1["total_cutbacks"], a1["attempts_6_to_12_exercised"]))
    print("  Histogram: %s" % a1["attempts_histogram"])
    print("New 1390552       : Max Attempt = %d, Cutbacks = %d, Attempts >= 6 Exercised = %s" % (
        a2["max_attempt"], a2["total_cutbacks"], a2["attempts_6_to_12_exercised"]))
    print("  Histogram: %s" % a2["attempts_histogram"])

if __name__ == "__main__":
    main()
