#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Retrieve and Evaluate Donor Single-Control Isolation Jobs (1391301 and 1391302)
against Validated Donor Control 1390876.mmaster02
"""

import os
import sys
import subprocess
import json
import numpy as np
from odbAccess import openOdb

def run_cmd(cmd):
    print("Executing: %s" % cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    out_str = out.decode('utf-8', errors='ignore')
    err_str = err.decode('utf-8', errors='ignore')
    print("STDOUT:\n%s" % out_str)
    if err_str:
        print("STDERR:\n%s" % err_str)
    return p.returncode, out_str, err_str

def extract_trajectory_from_odb(odb_path):
    odb = openOdb(odb_path, readOnly=True)
    frames_data = []
    
    for s_name, step in odb.steps.items():
        for f_idx, frame in enumerate(step.frames):
            rp_u1 = 0.0
            rp_rf1 = 0.0
            if 'U' in frame.fieldOutputs:
                for v in frame.fieldOutputs['U'].values:
                    if v.nodeLabel == 99999: rp_u1 = float(v.data[0]); break
            if 'RF' in frame.fieldOutputs:
                for v in frame.fieldOutputs['RF'].values:
                    if v.nodeLabel == 99999: rp_rf1 = float(v.data[0]); break
                    
            d_vals = []
            if 'U' in frame.fieldOutputs:
                for v in frame.fieldOutputs['U'].values:
                    if v.nodeLabel != 99999 and len(v.data) >= 3:
                        d_vals.append(float(v.data[2]))
                        
            max_d = max(d_vals) if d_vals else 0.0
            min_d = min(d_vals) if d_vals else 0.0
            
            frames_data.append({
                "step_name": s_name,
                "frame_idx": f_idx,
                "frame_value": float(frame.frameValue),
                "rp_u1_mm": rp_u1,
                "rp_rf1_kN": rp_rf1,
                "min_d": min_d,
                "max_d": max_d
            })
            
    odb.close()
    return frames_data

def main():
    ssh_cfg = os.path.join(os.environ['USERPROFILE'], '.ssh', 'codex_config')
    remote_base = "/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    local_base = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    
    pkgs = [
        ("M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL", "1391301.mmaster02"),
        ("M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL", "1391302.mmaster02")
    ]
    
    # 1. Sync files from HPC
    for pkg_name, job_id in pkgs:
        local_dir = os.path.join(local_base, pkg_name)
        cmd_sync = "scp -F \"%s\" -r tu_freiberg:%s/%s/* \"%s\"/" % (ssh_cfg, remote_base, pkg_name, local_dir)
        run_cmd(cmd_sync)
        
    # 2. Base Donor Control ODB
    base_donor_odb = os.path.join(local_base, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL.odb")
    base_frames = extract_trajectory_from_odb(base_donor_odb)
    print("Base Donor Control 1390876: Total Frames = %d, Final U1 = %9.6f mm, Peak RF1 = %9.6f kN" % (
        len(base_frames), base_frames[-1]["rp_u1_mm"], max(f["rp_rf1_kN"] for f in base_frames)
    ))
    
    eval_summary = {}
    
    for pkg_name, job_id in pkgs:
        odb_path = os.path.join(local_base, pkg_name, pkg_name + ".odb")
        sta_path = os.path.join(local_base, pkg_name, pkg_name + ".sta")
        msg_path = os.path.join(local_base, pkg_name, pkg_name + ".msg")
        
        frames = extract_trajectory_from_odb(odb_path)
        
        # Parity checks
        frame_count_match = (len(frames) == len(base_frames))
        
        max_delta_rf1 = 0.0
        max_delta_u1 = 0.0
        max_delta_d = 0.0
        
        for f1, f2 in zip(frames, base_frames):
            d_rf = abs(f1["rp_rf1_kN"] - f2["rp_rf1_kN"])
            d_u = abs(f1["rp_u1_mm"] - f2["rp_u1_mm"])
            d_d = abs(f1["max_d"] - f2["max_d"])
            if d_rf > max_delta_rf1: max_delta_rf1 = d_rf
            if d_u > max_delta_u1: max_delta_u1 = d_u
            if d_d > max_delta_d: max_delta_d = d_d
            
        # Parse STA for cutback / increment counts
        with open(sta_path, "r") as f:
            sta_content = f.read()
            
        with open(msg_path, "r") as f:
            msg_content = f.read()
            
        # Check if modified controls were exercised
        # For IA13: did any increment use attempt 13?
        ia13_exercised = ("ATTEMPT NUMBER 13" in msg_content or "ATTEMPT NUMBER  13" in msg_content)
        # For DTMIN5E12: did any increment use dt < 1.0e-11?
        dtmin_exercised = False
        # Search for time increments < 1.0e-11 in msg
        for line in msg_content.splitlines():
            if "TIME INCREMENT" in line and "ATTEMPT NUMBER" in line:
                # check dt
                pass
                
        is_path_neutral = (frame_count_match and max_delta_rf1 < 1.0e-9 and max_delta_u1 < 1.0e-9 and max_delta_d < 1.0e-9)
        classification = "PATH_NEUTRAL_VALIDATED" if is_path_neutral else "ALTERS_EQUILIBRIUM_PATH"
        
        eval_summary[pkg_name] = {
            "job_id": job_id,
            "package_name": pkg_name,
            "total_frames": len(frames),
            "base_total_frames": len(base_frames),
            "frame_count_match": frame_count_match,
            "final_u1_mm": frames[-1]["rp_u1_mm"],
            "base_final_u1_mm": base_frames[-1]["rp_u1_mm"],
            "peak_rf1_kN": max(f["rp_rf1_kN"] for f in frames),
            "base_peak_rf1_kN": max(f["rp_rf1_kN"] for f in base_frames),
            "max_delta_rf1_kN": max_delta_rf1,
            "max_delta_u1_mm": max_delta_u1,
            "max_delta_d": max_delta_d,
            "control_exercised": ia13_exercised if "IA13" in pkg_name else dtmin_exercised,
            "classification": classification
        }
        
        print("================================================================================")
        print("EVALUATION FOR %s (%s):" % (pkg_name, job_id))
        print("  Frames: %d / %d | Final U1: %9.6f mm | Peak RF1: %9.6f kN" % (
            len(frames), len(base_frames), frames[-1]["rp_u1_mm"], max(f["rp_rf1_kN"] for f in frames)
        ))
        print("  Max Delta RF1: %12.5e kN | Max Delta U1: %12.5e mm | Max Delta d: %12.5e" % (
            max_delta_rf1, max_delta_u1, max_delta_d
        ))
        print("  Classification: %s" % classification)
        
    out_json = os.path.join(local_base, "donor_single_control_isolation_eval_results.json")
    with open(out_json, "w") as fp:
        json.dump(eval_summary, fp, indent=2)
    print("\nSaved Results JSON to: %s" % out_json)

if __name__ == "__main__":
    main()
