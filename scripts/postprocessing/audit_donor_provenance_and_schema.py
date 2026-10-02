#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deterministic Audit of Donor Lineage (1390533 vs 1390552 vs 1390876 vs 1391301 vs 1391302),
UEL/PROPS Schema Reconciliation, and Combined Pair Candidate Manifest Preparation
"""

import os
import sys
import hashlib
import json
import difflib
from odbAccess import openOdb

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def extract_canonical_trajectory(odb_path):
    odb = openOdb(odb_path, readOnly=True)
    step_name = list(odb.steps.keys())[0]
    step = odb.steps[step_name]
    num_frames = len(step.frames)
    
    frames_data = []
    for f_idx, frame in enumerate(step.frames):
        rp_u1 = 0.0
        rp_rf1 = 0.0
        if 'U' in frame.fieldOutputs:
            for v in frame.fieldOutputs['U'].values:
                if v.nodeLabel == 99999:
                    rp_u1 = float(v.data[0])
                    break
        if 'RF' in frame.fieldOutputs:
            for v in frame.fieldOutputs['RF'].values:
                if v.nodeLabel == 99999:
                    rp_rf1 = float(v.data[0])
                    break
                    
        d_vals = []
        if 'U' in frame.fieldOutputs:
            for v in frame.fieldOutputs['U'].values:
                if v.nodeLabel != 99999 and len(v.data) >= 3:
                    d_vals.append(float(v.data[2]))
                    
        max_d = max(d_vals) if d_vals else 0.0
        min_d = min(d_vals) if d_vals else 0.0
        
        frames_data.append({
            "frame_idx": f_idx,
            "frame_value": float(frame.frameValue),
            "rp_u1_mm": rp_u1,
            "rp_rf1_kN": rp_rf1,
            "min_d": min_d,
            "max_d": max_d
        })
        
    odb.close()
    
    peak_rf1 = -1e9
    peak_frame = None
    peak_u1 = None
    for f in frames_data:
        if f["rp_rf1_kN"] > peak_rf1:
            peak_rf1 = f["rp_rf1_kN"]
            peak_frame = f["frame_idx"]
            peak_u1 = f["rp_u1_mm"]
            
    f17 = frames_data[17] if len(frames_data) > 17 else None
    flast = frames_data[-1]
    
    return {
        "step_name": step_name,
        "num_frames": num_frames,
        "num_increments": num_frames - 1,
        "terminal_u1_mm": flast["rp_u1_mm"],
        "terminal_rf1_kN": flast["rp_rf1_kN"],
        "peak_rf1_kN": peak_rf1,
        "peak_frame": peak_frame,
        "peak_u1_mm": peak_u1,
        "handoff_u1_mm": f17["rp_u1_mm"] if f17 else None,
        "handoff_rf1_kN": f17["rp_rf1_kN"] if f17 else None,
        "handoff_d_max": f17["max_d"] if f17 else None,
        "all_frames": frames_data
    }

def audit_inp_props_and_layers(inp_path):
    with open(inp_path, "r") as f:
        lines = f.readlines()
        
    nodes = set()
    mech_uels = set()
    phase_uels = set()
    props_values = None
    static_val = None
    controls_val = None
    
    in_nodes = False
    in_u1 = False
    in_u2 = False
    
    for i, line in enumerate(lines):
        line_s = line.strip()
        if line_s.startswith("*NODE"):
            in_nodes = True
            in_u1 = False
            in_u2 = False
            continue
        elif line_s.startswith("*ELEMENT, TYPE=U1"):
            in_nodes = False
            in_u1 = True
            in_u2 = False
            continue
        elif line_s.startswith("*ELEMENT, TYPE=U2"):
            in_nodes = False
            in_u1 = False
            in_u2 = True
            continue
        elif line_s.startswith("*"):
            in_nodes = False
            in_u1 = False
            in_u2 = False
            
        if in_nodes and line_s and not line_s.startswith("**"):
            try:
                nid = int(line_s.split(",")[0].strip())
                if nid != 99999: nodes.add(nid)
            except: pass
            
        if in_u1 and line_s and not line_s.startswith("**"):
            try:
                eid = int(line_s.split(",")[0].strip())
                mech_uels.add(eid)
            except: pass
            
        if in_u2 and line_s and not line_s.startswith("**"):
            try:
                eid = int(line_s.split(",")[0].strip())
                phase_uels.add(eid)
            except: pass
            
        if "*UEL PROPERTY" in line_s:
            props_values = lines[i+1].strip()
        if "*STATIC" in line_s:
            static_val = lines[i+1].strip()
        if "*CONTROLS, PARAMETERS=TIME INCREMENTATION" in line_s:
            controls_val = lines[i+1].strip()
            
    return {
        "physical_nodes": len(nodes),
        "physical_quads": len(mech_uels),
        "mech_uel_count": len(mech_uels),
        "phase_uel_count": len(phase_uels),
        "total_uel_count": len(mech_uels) + len(phase_uels),
        "props_string": props_values,
        "static_card": static_val,
        "controls_card": controls_val
    }

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    
    # 1. Inspect 1390533 and 1390552
    job_1390533_path = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_CONTROL_VAL/M2CORR_STAGE_E_DONOR_CONTROL_VAL.odb")
    job_1390447_path = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL.odb")
    job_1390876_path = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL.odb")
    job_1391301_path = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL/M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL.odb")
    job_1391302_path = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL/M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL.odb")
    
    traj_533 = extract_canonical_trajectory(job_1390533_path)
    traj_447 = extract_canonical_trajectory(job_1390447_path)
    traj_876 = extract_canonical_trajectory(job_1390876_path)
    traj_301 = extract_canonical_trajectory(job_1391301_path)
    traj_302 = extract_canonical_trajectory(job_1391302_path)
    
    print("================================================================================")
    print("1. RESOLUTION OF 1390533 VS 1390552 DISCREPANCY:")
    print("================================================================================")
    print("Job 1390533 (M2CORR_STAGE_E_DONOR_CONTROL_VAL):")
    print("  Frames: %d | Increments: %d | Peak RF1: %9.6f kN at Frame %d (U1=%9.6f mm) | Term RF1: %9.6f kN" % (
        traj_533["num_frames"], traj_533["num_increments"], traj_533["peak_rf1_kN"], traj_533["peak_frame"],
        traj_533["peak_u1_mm"], traj_533["terminal_rf1_kN"]
    ))
    print("Job 1390876 (M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL):")
    print("  Frames: %d | Increments: %d | Peak RF1: %9.6f kN at Frame %d (U1=%9.6f mm) | Term RF1: %9.6f kN" % (
        traj_876["num_frames"], traj_876["num_increments"], traj_876["peak_rf1_kN"], traj_876["peak_frame"],
        traj_876["peak_u1_mm"], traj_876["terminal_rf1_kN"]
    ))
    
    # Check first divergence of 1390533 vs 1390447
    div_frame = None
    for f1, f2 in zip(traj_533["all_frames"], traj_447["all_frames"]):
        if abs(f1["rp_rf1_kN"] - f2["rp_rf1_kN"]) > 1.0e-5:
            div_frame = f1["frame_idx"]
            print("  First Divergence of 1390533 vs 1390447 at Frame %d: 1390533 RF1=%9.6f kN, 1390447 RF1=%9.6f kN" % (
                div_frame, f1["rp_rf1_kN"], f2["rp_rf1_kN"]
            ))
            break
            
    # 2. UEL / PROPS Schema Audit
    inp_876 = audit_inp_props_and_layers(os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL.inp"))
    inp_301 = audit_inp_props_and_layers(os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL/M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL.inp"))
    inp_302 = audit_inp_props_and_layers(os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL/M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL.inp"))
    
    print("\n================================================================================")
    print("2. UEL / PROPS SCHEMA & ELEMENT COUNT AUDIT:")
    print("================================================================================")
    for name, d in [("1390876", inp_876), ("1391301", inp_301), ("1391302", inp_302)]:
        print("Package %s:" % name)
        print("  Physical Geometric Quads: %d" % d["physical_quads"])
        print("  Mechanical UELs (Layer 1): %d | Phase UELs (Layer 2): %d | Total UELs: %d" % (
            d["mech_uel_count"], d["phase_uel_count"], d["total_uel_count"]
        ))
        print("  Physical Nodes (excl RP): %d" % d["physical_nodes"])
        print("  PROPS(1..7) string: %s" % d["props_string"])
        print("  *STATIC:   %s" % d["static_card"])
        print("  *CONTROLS: %s" % d["controls_card"])
        
    # 3. Bit-for-bit Parity of 1391301 & 1391302 vs 1390876
    print("\n================================================================================")
    print("3. EXACT 440-FRAME BIT-FOR-BIT PARITY CHECK VS 1390876:")
    print("================================================================================")
    base_f = traj_876["all_frames"]
    for label, traj in [("1391301 (IA13)", traj_301), ("1391302 (DTMIN5E12)", traj_302)]:
        comp_f = traj["all_frames"]
        max_d_rf = max(abs(f1["rp_rf1_kN"] - f2["rp_rf1_kN"]) for f1, f2 in zip(base_f, comp_f))
        max_d_u = max(abs(f1["rp_u1_mm"] - f2["rp_u1_mm"]) for f1, f2 in zip(base_f, comp_f))
        max_d_d = max(abs(f1["max_d"] - f2["max_d"]) for f1, f2 in zip(base_f, comp_f))
        print("%s vs 1390876 across %d frames:" % (label, len(comp_f)))
        print("  Max Delta RF1: %12.5e kN | Max Delta U1: %12.5e mm | Max Delta d: %12.5e" % (
            max_d_rf, max_d_u, max_d_d
        ))
        
    # 4. Prepare Candidate Combined Minimal Pair Manifest
    combined_pkg_name = "M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL"
    combined_dir = os.path.join(base_dir, combined_pkg_name)
    if not os.path.exists(combined_dir):
        os.makedirs(combined_dir)
        
    # Build candidate INP
    src_inp_path = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL.inp")
    with open(src_inp_path, "r") as f:
        src_inp_text = f.read()
        
    comb_inp_text = src_inp_text.replace(
        "** JOB NAME: M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL",
        "** JOB NAME: " + combined_pkg_name
    ).replace(
        "0.001, 1.0, 1.0e-11, 0.02",
        "0.001, 1.0, 5.0e-12, 0.02"
    ).replace(
        "4, 8, 9, 16, 10, 4, 50, 12",
        "4, 8, 9, 16, 10, 4, 50, 13"
    )
    
    comb_inp_path = os.path.join(combined_dir, combined_pkg_name + ".inp")
    with open(comb_inp_path, "w") as f:
        f.write(comb_inp_text)
    with open(comb_inp_path, "rb") as f:
        c = f.read().replace(b"\r\n", b"\n")
    with open(comb_inp_path, "wb") as f:
        f.write(c)
        
    comb_for_path = os.path.join(combined_dir, "f44_mixed_uel_restart_stateinit.for")
    shutil_src = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL/f44_mixed_uel_restart_stateinit.for")
    with open(shutil_src, "rb") as f:
        c_for = f.read().replace(b"\r\n", b"\n")
    with open(comb_for_path, "wb") as f:
        f.write(c_for)
        
    comb_inp_sha = sha256_file(comb_inp_path)
    comb_for_sha = sha256_file(comb_for_path)
    
    # Unified diff
    with open(src_inp_path, "r") as f1, open(comb_inp_path, "r") as f2:
        udiff = list(difflib.unified_diff(f1.readlines(), f2.readlines(), fromfile="1390876_donor", tofile=combined_pkg_name))
        
    manifest_comb = {
        "package_name": combined_pkg_name,
        "base_job": "1390876.mmaster02",
        "base_package": "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL",
        "intended_controls": {
            "I_A": 13,
            "dt_min": "5.0e-12",
            "I_0": 4, "I_R": 8, "I_P": 9, "I_C": 16, "I_L": 10, "I_G": 4, "I_S": 50
        },
        "hashes": {
            "inp_sha256": comb_inp_sha,
            "for_sha256": comb_for_sha
        },
        "unified_diff": [l.rstrip() for l in udiff],
        "submission_authorized": False
    }
    
    comb_manifest_path = os.path.join(base_dir, "candidate_combined_donor_manifest.json")
    with open(comb_manifest_path, "w") as fp:
        json.dump(manifest_comb, fp, indent=2)
        
    print("\nSaved Combined Candidate Manifest to: %s" % comb_manifest_path)
    print("UNIFIED DIFF FOR COMBINED PAIR:")
    for l in udiff:
        print("  " + l.rstrip())

if __name__ == "__main__":
    main()
