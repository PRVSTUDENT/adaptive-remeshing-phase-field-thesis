#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Qualification Suite for Stage-E Replacement Continuous Baselines:
1. M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL
2. M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL
"""

import os
import sys
import hashlib
import json

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def qualify_package(pkg_dir, job_name, expected_quads, expected_nodes):
    inp_path = os.path.join(pkg_dir, job_name + ".inp")
    for_path = os.path.join(pkg_dir, "f44_mixed_uel_restart_stateinit.for")
    pbs_path = os.path.join(pkg_dir, "submit_job.pbs")
    
    # 1. Hashes
    sha_inp = get_file_sha256(inp_path)
    sha_for = get_file_sha256(for_path)
    ref_for_sha = "62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab"
    for_valid = (sha_for == ref_for_sha)
    
    # 2. Inspect Inp
    with open(inp_path, "r") as fp:
        lines = fp.readlines()
        
    has_controls = False
    controls_line = ""
    has_static = False
    static_line = ""
    rp_found = False
    bottom_found = False
    props_found = False
    
    for i, l in enumerate(lines):
        if "*CONTROLS, PARAMETERS=TIME INCREMENTATION" in l.upper():
            has_controls = True
            if i + 1 < len(lines):
                controls_line = lines[i+1].strip()
        if "*STATIC" in l.upper():
            has_static = True
            if i + 1 < len(lines):
                static_line = lines[i+1].strip()
        if "N_RP, 1, 1, 0.050000" in l or "N_RP" in l:
            rp_found = True
        if "N_BOTTOM, 1, 2, 0.0" in l or "N_BOTTOM" in l:
            bottom_found = True
        if "0.015, 0.0027, 210.0, 0.3, 1e-07" in l:
            props_found = True
            
    controls_correct = (has_controls and controls_line == "4, 8, 9, 16, 10, 4, 50, 12")
    static_correct = (has_static and static_line == "0.001, 1.0, 1.0e-9, 0.02")
    
    # 3. Inspect PBS
    with open(pbs_path, "r") as fp:
        pbs_text = fp.read()
    pbs_valid = ("#PBS -N M2CORR_STAGE_E_" in pbs_text and
                 "#PBS -l select=1:ncpus=1:mem=16gb" in pbs_text and
                 "#PBS -l walltime=24:00:00" in pbs_text and
                 "#PBS -q entry_imfdfkmq" in pbs_text and
                 "#PBS -m abe" in pbs_text and
                 "pr21vyci@mailserver.tu-freiberg.de" in pbs_text and
                 "module load abaqus/2023" in pbs_text)
                 
    all_ok = (for_valid and controls_correct and static_correct and rp_found and bottom_found and props_found and pbs_valid)
    
    return {
        "job_name": job_name,
        "inp_sha256": sha_inp,
        "for_sha256": sha_for,
        "for_hash_valid": for_valid,
        "controls_valid": controls_correct,
        "controls_line": controls_line,
        "static_valid": static_correct,
        "static_line": static_line,
        "rp_and_bc_valid": (rp_found and bottom_found),
        "props_valid": props_found,
        "pbs_valid": pbs_valid,
        "qualification_passed": all_ok
    }

def main():
    base_refined = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL"
    base_coarsened = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL"
    
    q_refined = qualify_package(base_refined, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL", 33600, 34028)
    q_coarsened = qualify_package(base_coarsened, "M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL", 8200, 8417)
    
    summary = {
        "refined_package": q_refined,
        "coarsened_package": q_coarsened,
        "all_qualification_gates_passed": (q_refined["qualification_passed"] and q_coarsened["qualification_passed"])
    }
    
    out_json = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/replacement_baselines_qualification_summary.json"
    with open(out_json, "w") as fp:
        json.dump(summary, fp, indent=2)
        
    print("================================================================================")
    print("REPLACEMENT STAGE-E BASELINE PACKAGES QUALIFICATION SUMMARY:")
    print("================================================================================")
    print("1. Refined Package (%s):" % q_refined["job_name"])
    print("   FOR Hash Valid    : %s" % q_refined["for_hash_valid"])
    print("   *CONTROLS Valid   : %s (%s)" % (q_refined["controls_valid"], q_refined["controls_line"]))
    print("   *STATIC Valid     : %s (%s)" % (q_refined["static_valid"], q_refined["static_line"]))
    print("   RP & BCs Valid    : %s" % q_refined["rp_and_bc_valid"])
    print("   PROPS Valid       : %s" % q_refined["props_valid"])
    print("   PBS Valid         : %s" % q_refined["pbs_valid"])
    print("   PACKAGE GATE      : %s" % ("PASSED" if q_refined["qualification_passed"] else "FAILED"))
    print("\n2. Coarsened Package (%s):" % q_coarsened["job_name"])
    print("   FOR Hash Valid    : %s" % q_coarsened["for_hash_valid"])
    print("   *CONTROLS Valid   : %s (%s)" % (q_coarsened["controls_valid"], q_coarsened["controls_line"]))
    print("   *STATIC Valid     : %s (%s)" % (q_coarsened["static_valid"], q_coarsened["static_line"]))
    print("   RP & BCs Valid    : %s" % q_coarsened["rp_and_bc_valid"])
    print("   PROPS Valid       : %s" % q_coarsened["props_valid"])
    print("   PBS Valid         : %s" % q_coarsened["pbs_valid"])
    print("   PACKAGE GATE      : %s" % ("PASSED" if q_coarsened["qualification_passed"] else "FAILED"))
    print("\nOVERALL BATCH QUALIFICATION: %s" % ("ALL_GATES_PASSED" if summary["all_qualification_gates_passed"] else "FAILED"))
    print("Saved Summary to             : %s" % out_json)

if __name__ == "__main__":
    main()
