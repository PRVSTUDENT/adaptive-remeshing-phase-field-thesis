#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Audit Per-Step Numerical Protocols in Submitted Batch E2 INP Decks:
1. M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL.inp (1391281.mmaster02)
2. M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL.inp (1391282.mmaster02)
"""

import os
import sys
import re
import json

def parse_step_controls(inp_path):
    with open(inp_path, "r") as f:
        lines = f.readlines()
        
    steps = []
    curr_step = None
    
    for i, line in enumerate(lines):
        line_s = line.strip()
        if line_s.upper().startswith("*STEP"):
            curr_step = {"line_start": i + 1, "raw_step_header": line_s, "step_name": "UNKNOWN", "static_params": None, "controls_params": None}
            # extract step name
            m = re.search(r"NAME\s*=\s*([A-Za-z0-9_]+)", line_s, re.IGNORECASE)
            if m: curr_step["step_name"] = m.group(1)
        elif curr_step is not None:
            if line_s.upper().startswith("*STATIC"):
                # next non-comment line is static params
                for j in range(i + 1, min(i + 5, len(lines))):
                    pj = lines[j].strip()
                    if not pj.startswith("**") and not pj.startswith("*"):
                        curr_step["static_params"] = [p.strip() for p in pj.split(",")]
                        break
            elif line_s.upper().startswith("*CONTROLS"):
                for j in range(i + 1, min(i + 5, len(lines))):
                    pj = lines[j].strip()
                    if not pj.startswith("**") and not pj.startswith("*"):
                        curr_step["controls_params"] = [p.strip() for p in pj.split(",")]
                        break
            elif line_s.upper().startswith("*END STEP"):
                steps.append(curr_step)
                curr_step = None
                
    return steps

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    inp_ref = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL.inp")
    inp_coarse = os.path.join(base_dir, "M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL/M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL.inp")
    
    res_ref = parse_step_controls(inp_ref)
    res_coarse = parse_step_controls(inp_coarse)
    
    print("================================================================================")
    print("AUDITING NUMERICAL PROTOCOLS IN SUBMITTED BATCH E2 INP DECKS:")
    print("================================================================================")
    
    for name, s_list in [("Refined Transfer (1391281.mmaster02)", res_ref),
                         ("Coarsened Transfer (1391282.mmaster02)", res_coarse)]:
        print("\n--- %s ---" % name)
        for s in s_list:
            print("  Step: %s" % s["step_name"])
            print("    *STATIC Params   : %s" % s["static_params"])
            print("    *CONTROLS Params : %s" % s["controls_params"])
            
    out_json = os.path.join(base_dir, "batch_e2_numerical_protocol_audit.json")
    with open(out_json, "w") as fp:
        json.dump({"refined_1391281": res_ref, "coarsened_1391282": res_coarse}, fp, indent=2)
    print("\nSaved Protocol Audit JSON to: %s" % out_json)

if __name__ == "__main__":
    main()
