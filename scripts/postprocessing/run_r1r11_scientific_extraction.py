#!/usr/bin/env python3
"""
Scientific Data Extraction & Acceptance Audit for Job 1389278.mmaster02 (M2STATE_FRACFIX_RESTART1R1R11).
Task ID: F97STATE-M2-INSTRUMENTED-RESTART1-R1R11-EVALUATION-AND-VALIDATION1
"""

import os
import sys
import json
import hashlib
import re
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389278.mmaster02"
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R11"
DAT_PATH = EVIDENCE_DIR / "M2STATE_FRACFIX_RESTART1R1R11.dat"
STA_PATH = EVIDENCE_DIR / "M2STATE_FRACFIX_RESTART1R1R11.sta"
MSG_PATH = EVIDENCE_DIR / "M2STATE_FRACFIX_RESTART1R1R11.msg"

def parse_rf_and_u_trajectory():
    text = DAT_PATH.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    
    trajectory = []
    
    current_step = 1
    current_inc = 1
    
    for idx, l in enumerate(lines):
        if "STEP" in l and "STATIC ANALYSIS" in l:
            m = re.search(r"STEP\s+(\d+)", l)
            if m:
                current_step = int(m.group(1))
        elif "INCREMENT" in l and "SUMMARY" in l:
            m = re.search(r"INCREMENT\s+(\d+)", l)
            if m:
                current_inc = int(m.group(1))
                
        if re.match(r"^\s+99999\s+([0-9.E+-]+)\s+([0-9.E+-]+)", l):
            parts = l.split()
            if len(parts) >= 3 and parts[0] == "99999":
                u1 = float(parts[1])
                rf1 = float(parts[-1])
                
                # Sum RF1 for all nodes 1..4998 in this table
                rf1_sum_all = 0.0
                start_table = max(0, idx - 5050)
                for table_line in lines[start_table:idx]:
                    t_parts = table_line.split()
                    if len(t_parts) >= 7:
                        try:
                            nid = int(t_parts[0])
                            if 1 <= nid <= 4998:
                                rf1_node = float(t_parts[4])
                                rf1_sum_all += rf1_node
                        except (ValueError, IndexError):
                            pass
                            
                trajectory.append({
                    "step": current_step,
                    "increment": current_inc,
                    "u1_mm": u1,
                    "rp_rf1_kN": rf1,
                    "nodes_rf1_sum_kN": rf1_sum_all,
                    "balance_error_kN": abs(rf1 + rf1_sum_all)
                })
                
    return trajectory

def parse_element_sdv_tables():
    text = DAT_PATH.read_text(encoding="utf-8", errors="replace")
    sections = text.split("THE FOLLOWING TABLE IS PRINTED AT THE INTEGRATION POINTS FOR ELEMENT TYPE")
    print(f"Found {len(sections) - 1} element printout tables in DAT file.")
    
    # Last two tables correspond to Step 2 Inc 15:
    # sections[-2] is U2 (quads), sections[-1] is U4 (tris)
    quad_sec = sections[-2]
    tri_sec = sections[-1]
    
    element_sdvs = {}
    
    # 1. Parse Quads (U2)
    for l in quad_sec.splitlines():
        parts = l.split()
        if len(parts) >= 5:
            try:
                elem_id = int(parts[0])
                ip_id = int(parts[1])
                sdv14_d = float(parts[2])
                sdv15_g = float(parts[3])
                sdv16_H = float(parts[4])
                
                phys_id = elem_id - 4894
                if phys_id not in element_sdvs:
                    element_sdvs[phys_id] = {}
                element_sdvs[phys_id][ip_id] = {
                    "global_elem_id": elem_id,
                    "elem_type": "QUAD",
                    "SDV14": sdv14_d,
                    "SDV15": sdv15_g,
                    "SDV16": sdv16_H
                }
            except (ValueError, IndexError):
                pass
                
    # 2. Parse Tris (U4)
    for l in tri_sec.splitlines():
        parts = l.split()
        if len(parts) >= 5:
            try:
                elem_id = int(parts[0])
                ip_id = int(parts[1])
                sdv14_d = float(parts[2])
                sdv15_g = float(parts[3])
                sdv16_H = float(parts[4])
                
                phys_id = elem_id - 4894
                if phys_id not in element_sdvs:
                    element_sdvs[phys_id] = {}
                element_sdvs[phys_id][ip_id] = {
                    "global_elem_id": elem_id,
                    "elem_type": "TRI",
                    "SDV14": sdv14_d,
                    "SDV15": sdv15_g,
                    "SDV16": sdv16_H
                }
            except (ValueError, IndexError):
                pass
                
    return element_sdvs

def main():
    print("=== 1. PARSING REACTION FORCES & LOAD-DISPLACEMENT TRAJECTORY ===")
    traj = parse_rf_and_u_trajectory()
    print(f"Parsed {len(traj)} trajectory points.")
    for pt in traj:
        print(f"Step {pt['step']} Inc {pt['increment']:2d}: U1 = {pt['u1_mm']:.6f} mm, RF1 = {pt['rp_rf1_kN']:.6f} kN, Balance Err = {pt['balance_error_kN']:.3e} kN")
        
    step1_pt = traj[0]
    final_pt = traj[-1]
    
    print("\n=== 2. SCIENTIFIC GATES AUDIT ===")
    # Gate 1: Step 1 Force continuity
    ref_rf1 = 0.064100
    r1r11_step1_rf1 = step1_pt["rp_rf1_kN"]
    rel_diff = abs(r1r11_step1_rf1 - ref_rf1) / ref_rf1
    print(f"Step 1 RF1 = {r1r11_step1_rf1:.6f} kN vs MM Ref {ref_rf1:.6f} kN -> Rel Diff = {rel_diff:.6f} ({rel_diff*100:.3f}%)")
    force_cont_pass = rel_diff <= 0.02
    print(f"Force Continuity Gate (<= 2%): {'PASS' if force_cont_pass else 'FAIL'}")
    
    # Gate 2: Global Force Balance
    max_balance_err = max(p["balance_error_kN"] for p in traj)
    print(f"Max Global Force Balance Error across entire trajectory: {max_balance_err:.6e} kN")
    balance_pass = max_balance_err < 1.0e-5
    print(f"Global Force Balance Gate (< 1e-5 kN): {'PASS' if balance_pass else 'FAIL'}")
    
    # Gate 3: Final Displacement
    final_u1 = final_pt["u1_mm"]
    print(f"Final Displacement U1 = {final_u1:.6f} mm (Target: 0.010000 mm)")
    u1_pass = abs(final_u1 - 0.010000) < 1.0e-6
    print(f"Terminal Displacement Gate: {'PASS' if u1_pass else 'FAIL'}")
    
    # Gate 4: Final Reaction Force
    final_rf1 = final_pt["rp_rf1_kN"]
    print(f"Final Reaction Force RF1 = {final_rf1:.6f} kN (Reference 1389241: 0.123223 kN)")
    
    print("\n=== 3. PARSING AUTHORITATIVE INTEGRATION POINT SDV16/H & SDV14/d ===")
    elem_sdvs = parse_element_sdv_tables()
    print(f"Parsed SDV data for {len(elem_sdvs)} physical mechanical elements (Target: 4894 physical elements).")
    assert len(elem_sdvs) == 4894, f"Expected 4894 physical elements, got {len(elem_sdvs)}"
    
    all_d = []
    all_H = []
    all_g = []
    
    quad_count = 0
    tri_count = 0
    
    for phys_id in sorted(elem_sdvs.keys()):
        ips = elem_sdvs[phys_id]
        if len(ips) == 1:
            elem_type = ips[1]["elem_type"]
            if elem_type == "QUAD":
                quad_count += 1
            else:
                tri_count += 1
        for ip_id, vals in sorted(ips.items()):
            all_d.append(vals["SDV14"])
            all_g.append(vals["SDV15"])
            all_H.append(vals["SDV16"])
            
    all_d = np.array(all_d)
    all_g = np.array(all_g)
    all_H = np.array(all_H)
    
    print(f"Physical elements breakdown: {quad_count} quads + {tri_count} tris")
    print(f"Total element output entries: {len(all_d)} (Expected: 4894)")
    assert len(all_d) == 4894, f"Expected 4894 elements, got {len(all_d)}"
    
    d_min, d_max, d_mean = float(np.min(all_d)), float(np.max(all_d)), float(np.mean(all_d))
    H_min, H_max, H_mean = float(np.min(all_H)), float(np.max(all_H)), float(np.mean(all_H))
    g_min, g_max, g_mean = float(np.min(all_g)), float(np.max(all_g)), float(np.mean(all_g))
    
    print(f"Phase d: min = {d_min:.6e}, max = {d_max:.6f}, mean = {d_mean:.6f}")
    print(f"History H: min = {H_min:.6e}, max = {H_max:.6f} kN/mm^2, mean = {H_mean:.6f} kN/mm^2")
    print(f"Degradation g(d): min = {g_min:.6e}, max = {g_max:.6f}, mean = {g_mean:.6f}")
    
    # Verify bounds
    d_bounds_pass = (d_min >= -1.0e-8) and (d_max <= 1.0 + 1.0e-6)
    H_bounds_pass = (H_min >= -1.0e-8) and (H_max > 0.0)
    print(f"Phase Bounds [0, 1]: {'PASS' if d_bounds_pass else 'FAIL'}")
    print(f"History Bounds (H >= 0, H_max > 0): {'PASS' if H_bounds_pass else 'FAIL'}")
    
    print("\n=== 4. GENERATING DURABLE RESTART2 SOURCE TRANSFER ARTIFACT ===")
    artifact_data = {
        "source_job_id": "1389278.mmaster02",
        "source_candidate": "M2STATE_FRACFIX_RESTART1R1R11",
        "source_mesh": "PK5",
        "source_manifest_hash": "c3d0d249988b453a79f0aa204d147d9f6bb3af8969b02cb9323db58ff8030e84",
        "checkpoint_step": 2,
        "checkpoint_increment": 15,
        "checkpoint_frame": "FINAL",
        "checkpoint_u1_mm": final_u1,
        "checkpoint_rf1_kN": final_rf1,
        "physical_element_count": len(elem_sdvs),
        "quad_element_count": quad_count,
        "tri_element_count": tri_count,
        "total_integration_points": len(all_d),
        "statistics": {
            "d_min": d_min,
            "d_max": d_max,
            "d_mean": d_mean,
            "H_min": H_min,
            "H_max": H_max,
            "H_mean": H_mean,
            "g_min": g_min,
            "g_max": g_max,
            "g_mean": g_mean
        },
        "authoritative_runtime_H_recovered": True,
        "sdv_provenance": "Direct extraction from Abaqus .dat file table printouts (*EL PRINT, ELSET=E_MECH_UEL, SDV14, SDV15, SDV16)",
        "elements": {str(k): v for k, v in sorted(elem_sdvs.items())}
    }
    
    artifact_json_path = PKG_DIR / "M2STATE_RESTART1R1R11_RESTART2_SOURCE_TRANSFER_ARTIFACT.json"
    clean_json = json.dumps(artifact_data, indent=2)
    artifact_json_path.write_bytes(clean_json.encode("utf-8"))
    
    evidence_artifact_path = EVIDENCE_DIR / "M2STATE_RESTART1R1R11_RESTART2_SOURCE_TRANSFER_ARTIFACT.json"
    evidence_artifact_path.write_bytes(clean_json.encode("utf-8"))
    
    artifact_sha = hashlib.sha256(clean_json.encode("utf-8")).hexdigest()
    print(f"Saved durable Restart2 source transfer artifact to {artifact_json_path}")
    print(f"Saved copy to {evidence_artifact_path}")
    print(f"Artifact SHA256: {artifact_sha}")

if __name__ == "__main__":
    main()
