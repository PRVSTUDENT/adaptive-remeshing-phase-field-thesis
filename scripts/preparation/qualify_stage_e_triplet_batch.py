#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deterministic Semantic & Mesh Qualification for Stage-E Triplet Continuous Baselines
1. M2CORR_STAGE_E_DONOR_CONTROL_VAL (8,836 quads)
2. M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL (33,600 quads)
3. M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL (8,200 quads)
"""

import os
import sys
import json

def qualify_triplet():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    
    packages = [
        ("M2CORR_STAGE_E_DONOR_CONTROL_VAL", 9074, 8836, 0.003750),
        ("M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL", 34028, 33600, 0.002000),
        ("M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL", 8417, 8200, 0.005000)
    ]
    
    results = {}
    
    for pkg_name, exp_nodes, exp_quads, exp_htip in packages:
        pkg_dir = os.path.join(base_dir, pkg_name)
        inp_file = os.path.join(pkg_dir, "%s.inp" % pkg_name)
        pbs_file = os.path.join(pkg_dir, "submit_job.pbs")
        
        with open(inp_file, "r") as fp:
            inp_lines = fp.readlines()
            
        has_u1 = any("TYPE=U1, NODES=4, COORDINATES=2" in l for l in inp_lines)
        has_u2 = any("TYPE=U2, NODES=4, COORDINATES=2" in l for l in inp_lines)
        has_phase_set = any("*ELEMENT, TYPE=U1, ELSET=E_QUAD_PHASE" in l for l in inp_lines)
        has_mech_set = any("*ELEMENT, TYPE=U2, ELSET=E_QUAD_MECH" in l for l in inp_lines)
        
        props_phase_line = ""
        props_mech_line = ""
        for i, l in enumerate(inp_lines):
            if "*UEL PROPERTY, ELSET=E_QUAD_PHASE" in l:
                props_phase_line = inp_lines[i+1].strip()
            if "*UEL PROPERTY, ELSET=E_QUAD_MECH" in l:
                props_mech_line = inp_lines[i+1].strip()
                
        expected_props = "0.015, 0.0027, 210.0, 0.3, 1e-07, %d.0, 0.0" % exp_quads
        props_phase_ok = (props_phase_line == expected_props)
        props_mech_ok = (props_mech_line == expected_props)
        
        has_dof2_coupling = any("99999, 2" in l and "*EQUATION" not in l for l in inp_lines)
        has_static = any("0.001, 1.0, 1.0e-10, 0.02" in l for l in inp_lines)
        has_controls_line1 = any("8, 10, 9, 20, 10, 4, 50, 12" in l for l in inp_lines)
        has_controls_line2 = any("0.25, 0.50, 0.75, 0.25, 0.25, 1.5, 1.5, 1.25" in l for l in inp_lines)
        
        with open(pbs_file, "r") as fp:
            pbs_content = fp.read()
        has_exit_propagation = "ABAQUS_RC=$?" in pbs_content and "exit ${ABAQUS_RC}" in pbs_content
        has_entry_queue = "#PBS -q entry_imfdfkmq" in pbs_content
        
        pkg_res = {
            "has_u1_phase_header": has_u1,
            "has_u2_mech_header": has_u2,
            "has_phase_elset": has_phase_set,
            "has_mech_elset": has_mech_set,
            "props_phase_valid": props_phase_ok,
            "props_mech_valid": props_mech_ok,
            "props_exact": props_phase_line,
            "shear_dof1_only": not has_dof2_coupling,
            "static_step_valid": has_static,
            "continuation_controls_line1": has_controls_line1,
            "continuation_controls_line2": has_controls_line2,
            "pbs_exit_propagation": has_exit_propagation,
            "pbs_entry_queue": has_entry_queue
        }
        
        all_ok = all([
            has_u1, has_u2, has_phase_set, has_mech_set,
            props_phase_ok, props_mech_ok, not has_dof2_coupling,
            has_static, has_controls_line1, has_controls_line2,
            has_exit_propagation, has_entry_queue
        ])
        
        pkg_res["overall_status"] = "QUALIFIED" if all_ok else "DISCREPANCY_FOUND"
        results[pkg_name] = pkg_res
        
        print("Package: %s" % pkg_name)
        print("  Status: %s" % pkg_res["overall_status"])
        print("  Properties: %s (Match: %s)" % (props_phase_line, props_phase_ok))
        print("  Continuation Controls: (Line 1: %s, Line 2: %s)" % (has_controls_line1, has_controls_line2))
        print("  PBS Exit Propagation: %s, Entry Queue: %s" % (has_exit_propagation, has_entry_queue))
        
    out_json = os.path.join(base_dir, "triplet_qualification_summary.json")
    with open(out_json, "w") as fp:
        json.dump(results, fp, indent=2)
    print("\nSaved triplet qualification summary to %s" % out_json)

if __name__ == "__main__":
    qualify_triplet()
