#!/usr/bin/env python3
"""
Comprehensive Validation and Quality Preflight Script for Refined-Tip Diagnostic Candidate:
`M2CORR_PK10R3_REFINED_TIP`
"""

import os
import sys
import json
import math
import hashlib
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP"
INP_PATH = OUT_DIR / "M2CORR_PK10R3_REFINED_TIP.inp"
UEL_PATH = OUT_DIR / "f42_mixed_uel.for"
PBS_PATH = OUT_DIR / "submit_job.pbs"
NOTIF_PATH = OUT_DIR / "job_notifications.sh"
MANIFEST_PATH = OUT_DIR / "manifest.json"
GEN_SCRIPT = ROOT / "scripts/model_generation/build_pk10r3_refined_tip_candidate.py"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def audit_inp_deck(inp_path):
    nodes = {}
    phase_elems = {}
    disp_elems = {}
    vis_elems = {}
    equations = []
    
    current_section = None
    with open(inp_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue
            if line_str.startswith("*"):
                header = line_str.upper()
                if header.startswith("*NODE") and "OUTPUT" not in header and "PRINT" not in header:
                    current_section = "NODE"
                elif header.startswith("*ELEMENT"):
                    if "PHASE_QUAD" in header or "TYPE=U1" in header:
                        current_section = "PHASE_ELEM"
                    elif "DISP_QUAD" in header or "TYPE=U2" in header:
                        current_section = "DISP_ELEM"
                    elif "VIS_QUAD" in header or "TYPE=CPE4" in header:
                        current_section = "VIS_ELEM"
                    else:
                        current_section = "OTHER_ELEM"
                elif header.startswith("*EQUATION"):
                    current_section = "EQUATION"
                else:
                    current_section = None
                continue
                
            if current_section == "NODE":
                parts = [p.strip() for p in line_str.split(",")]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        pass
            elif current_section == "PHASE_ELEM":
                parts = [p.strip() for p in line_str.split(",")]
                if len(parts) >= 5:
                    eid = int(parts[0])
                    phase_elems[eid] = [int(p) for p in parts[1:5]]
            elif current_section == "DISP_ELEM":
                parts = [p.strip() for p in line_str.split(",")]
                if len(parts) >= 5:
                    eid = int(parts[0])
                    disp_elems[eid] = [int(p) for p in parts[1:5]]
            elif current_section == "VIS_ELEM":
                parts = [p.strip() for p in line_str.split(",")]
                if len(parts) >= 5:
                    eid = int(parts[0])
                    vis_elems[eid] = [int(p) for p in parts[1:5]]
            elif current_section == "EQUATION":
                if "," in line_str:
                    equations.append(line_str)
                    
    # Quality & Connectivity Audits
    n_phys = len(phase_elems)
    assert len(disp_elems) == n_phys, f"Disp elem count {len(disp_elems)} != {n_phys}"
    assert len(vis_elems) == n_phys, f"Vis elem count {len(vis_elems)} != {n_phys}"
    
    # Check 1-to-1 connectivity mapping
    for i in range(1, n_phys + 1):
        p_conn = phase_elems[i]
        d_conn = disp_elems[n_phys + i]
        v_conn = vis_elems[2 * n_phys + i]
        assert p_conn == d_conn == v_conn, f"Mismatch in element {i} connectivity: {p_conn} vs {d_conn} vs {v_conn}"
        
    # Check equations: each top node tied exactly once to RP (99999)
    top_nodes = set([nid for nid, (x, y) in nodes.items() if abs(y - 0.5) < 1e-9 and nid != 99999])
    eq_nodes = set()
    for eq in equations:
        parts = [p.strip() for p in eq.split(",")]
        if len(parts) >= 6:
            tied_nid = int(parts[0])
            rp_nid = int(parts[3])
            assert rp_nid == 99999, f"Invalid RP node in equation: {rp_nid}"
            assert tied_nid not in eq_nodes, f"Duplicate equation for node {tied_nid}"
            eq_nodes.add(tied_nid)
            
    assert top_nodes == eq_nodes, f"Top nodes mismatch with equations: {len(top_nodes)} top nodes vs {len(eq_nodes)} tied nodes"
    
    # Slit connectivity
    slit_nodes = [nid for nid, (x, y) in nodes.items() if abs(y) < 1e-9 and -0.5 <= x < 0.0]
    notch_tip_nodes = [nid for nid, (x, y) in nodes.items() if abs(x) < 1e-9 and abs(y) < 1e-9]
    assert len(notch_tip_nodes) == 1, f"Expected exactly 1 shared notch tip node at (0,0), found {len(notch_tip_nodes)}"
    
    # Nearest Gauss point to tip (0,0)
    # Find element with notch tip node (0,0)
    tip_nid = notch_tip_nodes[0]
    tip_elems = [eid for eid, conn in phase_elems.items() if tip_nid in conn]
    g_local = [-0.577350269189626, 0.577350269189626]
    nearest_gp_dist = 1e9
    nearest_gp_coords = None
    min_h = 1e9
    max_h = 0.0
    
    for eid, conn in phase_elems.items():
        coords = [nodes[n] for n in conn]
        dx = math.hypot(coords[1][0]-coords[0][0], coords[1][1]-coords[0][1])
        dy = math.hypot(coords[3][0]-coords[0][0], coords[3][1]-coords[0][1])
        h_elem = min(dx, dy)
        min_h = min(min_h, h_elem)
        max_h = max(max_h, max(dx, dy))
        
        if tip_nid in conn:
            for eta in g_local:
                for xi in g_local:
                    N = [
                        0.25 * (1.0 - xi) * (1.0 - eta),
                        0.25 * (1.0 + xi) * (1.0 - eta),
                        0.25 * (1.0 + xi) * (1.0 + eta),
                        0.25 * (1.0 - xi) * (1.0 + eta)
                    ]
                    gx = sum([N[k] * coords[k][0] for k in range(4)])
                    gy = sum([N[k] * coords[k][1] for k in range(4)])
                    g_dist = math.hypot(gx, gy)
                    if g_dist < nearest_gp_dist:
                        nearest_gp_dist = g_dist
                        nearest_gp_coords = (gx, gy)

    return {
        "node_count": len(nodes),
        "physical_quad_count": n_phys,
        "total_elements": 3 * n_phys,
        "tied_top_equations": len(equations),
        "slit_split_node_count": len(slit_nodes),
        "slit_flank_pairs": len(slit_nodes) // 2,
        "min_h": min_h,
        "max_h": max_h,
        "h_over_l0_min": min_h / 0.015,
        "nearest_gp_dist_to_tip": nearest_gp_dist,
        "nearest_gp_coords": nearest_gp_coords
    }

def main():
    print("================================================================================")
    print("M2CORR_PK10R3_REFINED_TIP PACKAGE PREFLIGHT & INTEGRITY AUDIT")
    print("================================================================================")
    
    audit = audit_inp_deck(INP_PATH)
    print("INP Audit Results:")
    print(f"  Physical Node Count:        {audit['node_count']}")
    print(f"  Physical Quad Count:        {audit['physical_quad_count']}")
    print(f"  Total Elements (3 Layers):  {audit['total_elements']}")
    print(f"  Tied Top Nodes (Equations): {audit['tied_top_equations']}")
    print(f"  Slit Flank Node Pairs:      {audit['slit_flank_pairs']} ({audit['slit_split_node_count']} nodes along slit)")
    print(f"  Element Size min (h_min):   {audit['min_h']:.6f} mm")
    print(f"  Element Size max (h_max):   {audit['max_h']:.6f} mm")
    print(f"  Regularization Ratio h/l0:  {audit['h_over_l0_min']:.4f} (Target <= 0.15)")
    print(f"  Nearest GP Distance to Tip: {audit['nearest_gp_dist_to_tip']:.6f} mm ({audit['nearest_gp_dist_to_tip']*1e3:.3f} um)")
    print(f"  Nearest GP Coordinates:     ({audit['nearest_gp_coords'][0]:.6f}, {audit['nearest_gp_coords'][1]:.6f}) mm")
    
    hashes = {
        "inp_sha256": sha256_file(INP_PATH),
        "uel_sha256": sha256_file(UEL_PATH),
        "pbs_sha256": sha256_file(PBS_PATH),
        "notif_sha256": sha256_file(NOTIF_PATH),
        "manifest_sha256": sha256_file(MANIFEST_PATH),
        "gen_script_sha256": sha256_file(GEN_SCRIPT)
    }
    
    print("\nPackage Cryptographic SHA-256 Hashes:")
    for k, v in hashes.items():
        print(f"  {k}: {v}")
        
    print("================================================================================")
    return {
        "audit": audit,
        "hashes": hashes
    }

if __name__ == "__main__":
    main()
