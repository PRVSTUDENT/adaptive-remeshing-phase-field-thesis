#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Forensic Analysis of Final Target Baselines:
1391277.mmaster02 (Refined) & 1391279.mmaster02 (Coarsened)
"""

import os
import sys
import json

def parse_msg_terminal(msg_path):
    with open(msg_path, "r") as f:
        lines = f.readlines()
        
    tail_lines = lines[-150:]
    error_lines = [l.strip() for l in lines if "***ERROR" in l or "***WARNING" in l or "TIME INCREMENT REQUIRED IS LESS" in l or "TOO MANY ATTEMPTS" in l]
    
    return {
        "tail": "".join(tail_lines),
        "errors": error_lines
    }

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    
    msg_ref = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL.msg")
    msg_coarse = os.path.join(base_dir, "M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL.msg")
    
    res_ref = parse_msg_terminal(msg_ref)
    res_coarse = parse_msg_terminal(msg_coarse)
    
    print("================================================================================")
    print("REFINED 1391277 TERMINAL FORENSIC:")
    print("================================================================================")
    print("Errors found in .msg:")
    for e in res_ref["errors"]:
        print("  - %s" % e)
    print("\nTail of .msg:\n%s" % res_ref["tail"])
    
    print("\n================================================================================")
    print("COARSENED 1391279 TERMINAL FORENSIC:")
    print("================================================================================")
    print("Errors found in .msg:")
    for e in res_coarse["errors"]:
        print("  - %s" % e)
    print("\nTail of .msg:\n%s" % res_coarse["tail"])

if __name__ == "__main__":
    main()
