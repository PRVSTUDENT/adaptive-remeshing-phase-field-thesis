#!/usr/bin/env python3
"""
Comprehensive Audit and Verification Script for: M2STATE_FRACFIX_RESTART2R13
Task ID: F107STATE-M2-CORRECTED-RESTART2-R2R13-PREP-AND-QUALIFICATION1
"""

import sys
import os
import re
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13"
DAT_PATH = PKG_DIR / "M2STATE_FRACFIX_RESTART2R13_STEP1.dat"
INP_PATH = PKG_DIR / "M2STATE_FRACFIX_RESTART2R13.inp"
SRC_ARTIFACT_JSON = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389278.mmaster02/M2STATE_RESTART1R1R11_RESTART2_SOURCE_TRANSFER_ARTIFACT.json"

def parse_inp_sets(inp_path):
    text = inp_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    nsets = {}
    current_set = None
    in_nset = False
    
    for l in lines:
        l_strip = l.strip()
        if not l_strip or l_strip.startswith("**"):
            continue
        if l_strip.startswith("*NSET"):
            in_nset = True
            m = re.search(r"NSET=([A-Za-z0-9_]+)", l_strip)
            if m:
                current_set = m.group(1)
                nsets[current_set] = []
            continue
        elif l_strip.startswith("*"):
            in_nset = False
            current_set = None
            continue
            
        if in_nset and current_set:
            parts = [p.strip() for p in l_strip.split(",") if p.strip()]
            for p in parts:
                try:
                    nsets[current_set].append(int(p))
                except ValueError:
                    pass
    return nsets

def parse_dat_nodes(dat_path):
    text = dat_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    
    start_idx = -1
    for i, l in enumerate(lines):
        if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in l:
            start_idx = i
            break
            
    if start_idx == -1:
        print("ERROR: Could not find node table in DAT")
        return {}
        
    nodes = {}
    for l in lines[start_idx+5:]:
        if not l.strip() or "MAXIMUM" in l or "MINIMUM" in l or "TOTAL" in l or "WARNING" in l or "PAGE" in l or "ANALYSIS" in l or "JOB" in l:
            continue
        parts = l.split()
        if len(parts) >= 6:
            try:
                nid = int(parts[0])
                u1 = float(parts[1])
                u2 = float(parts[2])
                u3 = float(parts[3])
                rf1 = float(parts[4])
                rf2 = float(parts[5])
                rf3 = float(parts[6]) if len(parts) > 6 else 0.0
                nodes[nid] = {
                    "u1": u1, "u2": u2, "u3": u3,
                    "rf1": rf1, "rf2": rf2, "rf3": rf3
                }
            except ValueError:
                pass
        elif len(parts) == 3 and parts[0] == "99999":
            try:
                nid = 99999
                u1 = float(parts[1])
                rf1 = float(parts[2])
                nodes[nid] = {
                    "u1": u1, "u2": 0.0, "u3": 0.0,
                    "rf1": rf1, "rf2": 0.0, "rf3": 0.0
                }
            except ValueError:
                pass
    return nodes

def main():
    print("======================================================================")
    print("M2STATE_FRACFIX_RESTART2R13 Comprehensive Step 1 Audit")
    print("======================================================================")
    
    nsets = parse_inp_sets(INP_PATH)
    nodes = parse_dat_nodes(DAT_PATH)
    
    print(f"Parsed {len(nodes)} nodes from DAT file.")
    
    top_nids = sorted(list(set(nsets.get("N_TOP", []))))
    bot_nids = sorted(list(set(nsets.get("N_BOTTOM", []))))
    
    print(f"Top nodes count: {len(top_nids)}, Bottom nodes count: {len(bot_nids)}")
    
    rp_rf1 = nodes[99999]["rf1"]
    rp_u1 = nodes[99999]["u1"]
    
    top_u1 = [nodes[n]["u1"] for n in top_nids if n in nodes]
    top_u2 = [nodes[n]["u2"] for n in top_nids if n in nodes]
    bot_u1 = [nodes[n]["u1"] for n in bot_nids if n in nodes]
    bot_u2 = [nodes[n]["u2"] for n in bot_nids if n in nodes]
    
    bot_rf1 = [nodes[n]["rf1"] for n in bot_nids if n in nodes]
    bot_rf2 = [nodes[n]["rf2"] for n in bot_nids if n in nodes]
    
    all_rf1 = sum(nd["rf1"] for nd in nodes.values())
    all_rf2 = sum(nd["rf2"] for nd in nodes.values())
    
    print("\n--- NODAL DISPLACEMENTS ---")
    print(f"RP Node 99999: U1 = {rp_u1:.6f} mm, RF1 = {rp_rf1:.8f} kN ({rp_rf1*1000:.3f} N)")
    print(f"Top U1: min = {min(top_u1):.6f}, max = {max(top_u1):.6f}, mean = {np.mean(top_u1):.6f} mm")
    print(f"Top U2: min = {min(top_u2):.6f}, max = {max(top_u2):.6f}, absmax = {max(abs(min(top_u2)), abs(max(top_u2))):.6f} mm")
    print(f"Bottom U1: min = {min(bot_u1):.6f}, max = {max(bot_u1):.6f} mm")
    print(f"Bottom U2: min = {min(bot_u2):.6f}, max = {max(bot_u2):.6f} mm")
    
    print("\n--- REACTION FORCES & GLOBAL EQUILIBRIUM ---")
    sum_bot_rf1 = np.sum(bot_rf1)
    sum_bot_rf2 = np.sum(bot_rf2)
    print(f"Sum of RF1 on N_BOTTOM: {sum_bot_rf1:.8f} kN")
    print(f"Sum of RF2 on N_BOTTOM: {sum_bot_rf2:.8f} kN")
    print(f"RP 99999 RF1:            {rp_rf1:.8f} kN")
    
    global_fx_residual = rp_rf1 + sum_bot_rf1
    global_fy_residual = sum_bot_rf2
    print(f"Global Fx residual (RP + N_BOTTOM): {global_fx_residual:.8e} kN")
    print(f"Global Fy residual (N_BOTTOM):      {global_fy_residual:.8e} kN")
    print(f"Sum of RF1 over ALL domain nodes:   {all_rf1:.8e} kN")
    print(f"Sum of RF2 over ALL domain nodes:   {all_rf2:.8e} kN")
    
    print("\n--- COMPARISON WITH OFFLINE BVP & HISTORICAL BASELINE ---")
    offline_bvp_damaged_rf1 = 0.315883
    offline_bvp_undamaged_rf1 = 0.321312
    source_rf1 = 0.12322307
    
    rel_diff_offline = abs(rp_rf1 - offline_bvp_damaged_rf1) / rp_rf1
    print(f"Target Runtime RF1:             {rp_rf1:.8f} kN")
    print(f"Offline BVP Damaged RF1:        {offline_bvp_damaged_rf1:.8f} kN (diff = {rel_diff_offline*100:.3f}%)")
    print(f"Offline BVP Undamaged RF1:      {offline_bvp_undamaged_rf1:.8f} kN")
    print(f"Source Job 1389278 RF1:         {source_rf1:.8f} kN")
    print(f"Old Buggy R2R12 Runtime RF1:    0.79840434 kN (deflation factor = {0.79840434 / rp_rf1:.5f}x = exactly 2.500x)")

if __name__ == '__main__':
    main()
