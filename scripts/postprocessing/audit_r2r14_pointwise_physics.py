#!/usr/bin/env python3
"""
Deep Pointwise Physics Auditor for Item 1 and Item 2 of F114DIAG
"""

import sys
import re
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_R2R14 = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389328.mmaster02"
EVIDENCE_R2R13 = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389325.mmaster02"
DAT_R2R14 = EVIDENCE_R2R14 / "M2STATE_FRACFIX_RESTART2R14.dat"
DAT_R2R13 = EVIDENCE_R2R13 / "M2STATE_FRACFIX_RESTART2R13.dat"

def parse_full_dat(dat_path):
    print(f"Parsing full nodal and element fields from {dat_path.name}...")
    lines = dat_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    
    inc_headers = []
    current_step = 1
    for i, l in enumerate(lines):
        if "STEP    2" in l:
            current_step = 2
        if "INCREMENT" in l and "SUMMARY" in l:
            m = re.search(r"INCREMENT\s+(\d+)\s+SUMMARY", l)
            if m:
                inc_num = int(m.group(1))
                inc_headers.append((i, current_step, inc_num))

    frames = []
    for idx, (line_idx, step_num, inc_num) in enumerate(inc_headers):
        next_line_idx = inc_headers[idx+1][0] if idx+1 < len(inc_headers) else len(lines)
        inc_block = lines[line_idx:next_line_idx]

        nodal_d = {}
        nodal_u1 = {}
        nodal_u2 = {}
        elem_h = {} # elem_id -> list of IP H values or max IP H

        in_node_table = False
        in_elem_table = False

        for l in inc_block:
            if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in l:
                in_node_table = True
                in_elem_table = False
                continue
            elif "THE FOLLOWING TABLE IS PRINTED AT THE INTEGRATION POINTS" in l:
                in_elem_table = True
                in_node_table = False
                continue
            elif "MAXIMUM" in l:
                in_node_table = False
                in_elem_table = False
                continue

            if in_node_table:
                parts = l.split()
                if len(parts) >= 4 and parts[0].isdigit():
                    nid = int(parts[0])
                    u1 = float(parts[1])
                    u2 = float(parts[2])
                    d = float(parts[3])
                    nodal_u1[nid] = u1
                    nodal_u2[nid] = u2
                    nodal_d[nid] = d
            elif in_elem_table:
                parts = l.split()
                # e.g. "   1234       1     1.234567E-02 ... "
                # format: ELEM_ID [PT] SDV13 SDV14 SDV15 SDV16
                if len(parts) == 5 and parts[0].isdigit():
                    eid = int(parts[0])
                    # parts: [eid, sdv13, sdv14, sdv15, sdv16]
                    h_val = float(parts[4])
                    if eid not in elem_h:
                        elem_h[eid] = []
                    elem_h[eid].append(h_val)
                elif len(parts) == 6 and parts[0].isdigit():
                    eid = int(parts[0])
                    # parts: [eid, ipt, sdv13, sdv14, sdv15, sdv16]
                    h_val = float(parts[5])
                    if eid not in elem_h:
                        elem_h[eid] = []
                    elem_h[eid].append(h_val)

        frames.append({
            "step": step_num,
            "inc": inc_num,
            "nodal_d": nodal_d,
            "nodal_u1": nodal_u1,
            "nodal_u2": nodal_u2,
            "elem_h": elem_h
        })

    print(f"Parsed {len(frames)} frames. Nodes per frame: {len(frames[0]['nodal_d'])}, Elements per frame: {len(frames[0]['elem_h'])}")
    return frames

def audit_pointwise_physics():
    frames = parse_full_dat(DAT_R2R14)
    
    # 1. Pointwise phase evolution: d(n+1) - d(n)
    all_nodes = sorted(list(frames[0]["nodal_d"].keys()))
    total_nodes = len(all_nodes)
    
    phase_pointwise_violation_count = 0
    phase_max_negative_increment = 0.0
    nodes_with_healing = set()
    
    total_point_evaluations = 0
    
    print("\n--- Pointwise Phase Evolution (d(n+1) - d(n)) Across Frames ---")
    for f_idx in range(len(frames) - 1):
        f_curr = frames[f_idx]
        f_next = frames[f_idx + 1]
        
        step_c, inc_c = f_curr["step"], f_curr["inc"]
        step_n, inc_n = f_next["step"], f_next["inc"]
        
        neg_inc_frame = 0.0
        viol_count_frame = 0
        
        for nid in all_nodes:
            d_c = f_curr["nodal_d"].get(nid, 0.0)
            d_n = f_next["nodal_d"].get(nid, 0.0)
            diff = d_n - d_c
            total_point_evaluations += 1
            
            if diff < -1e-6: # Beyond numerical tolerance
                viol_count_frame += 1
                phase_pointwise_violation_count += 1
                nodes_with_healing.add(nid)
                if abs(diff) > phase_max_negative_increment:
                    phase_max_negative_increment = abs(diff)
                if abs(diff) > neg_inc_frame:
                    neg_inc_frame = abs(diff)
                    
        print(f"Frame {step_c}:{inc_c} -> {step_n}:{inc_n}: Violations = {viol_count_frame}/{total_nodes}, Max -Delta d = {neg_inc_frame:.6f}")

    phase_fraction_of_points_with_healing = len(nodes_with_healing) / total_nodes
    print(f"\nPhase Pointwise Summary:")
    print(f"  phase_pointwise_violation_count = {phase_pointwise_violation_count}")
    print(f"  phase_max_negative_increment    = {phase_max_negative_increment:.6f}")
    print(f"  nodes_with_healing              = {len(nodes_with_healing)} / {total_nodes}")
    print(f"  phase_fraction_of_points_with_healing = {phase_fraction_of_points_with_healing:.4f}")

    # 2. Pointwise history evolution: H(n+1) - H(n)
    all_elems = sorted(list(frames[0]["elem_h"].keys()))
    total_elems = len(all_elems)
    
    history_pointwise_violation_count = 0
    history_max_negative_increment = 0.0
    elems_with_h_drop = set()
    
    print("\n--- Pointwise History Evolution (H(n+1) - H(n)) Across Frames ---")
    for f_idx in range(len(frames) - 1):
        f_curr = frames[f_idx]
        f_next = frames[f_idx + 1]
        
        step_c, inc_c = f_curr["step"], f_curr["inc"]
        step_n, inc_n = f_next["step"], f_next["inc"]
        
        neg_inc_h_frame = 0.0
        viol_count_h_frame = 0
        
        for eid in all_elems:
            h_c_list = f_curr["elem_h"].get(eid, [0.0])
            h_n_list = f_next["elem_h"].get(eid, [0.0])
            
            for ip in range(min(len(h_c_list), len(h_n_list))):
                h_c = h_c_list[ip]
                h_n = h_n_list[ip]
                diff = h_n - h_c
                if diff < -1e-6:
                    viol_count_h_frame += 1
                    history_pointwise_violation_count += 1
                    elems_with_h_drop.add(eid)
                    if abs(diff) > history_max_negative_increment:
                        history_max_negative_increment = abs(diff)
                    if abs(diff) > neg_inc_h_frame:
                        neg_inc_h_frame = abs(diff)

        print(f"Frame {step_c}:{inc_c} -> {step_n}:{inc_n}: Violations = {viol_count_h_frame}, Max -Delta H = {neg_inc_h_frame:.6e}")

    print(f"\nHistory Pointwise Summary:")
    print(f"  history_pointwise_violation_count = {history_pointwise_violation_count}")
    print(f"  history_max_negative_increment    = {history_max_negative_increment:.6e}")

    # 3. History Field Reconciliation (Item 2)
    # Parse R2R13 terminal frame
    frames_r2r13 = parse_full_dat(DAT_R2R13)
    term_r2r13 = frames_r2r13[-1]
    step1_r2r14 = frames[0]
    term_r2r14 = frames[-1]

    # Get max H across all elements
    h_vals_r2r13_term = [max(v) for v in term_r2r13["elem_h"].values() if len(v) > 0]
    h_vals_r2r14_step1 = [max(v) for v in step1_r2r14["elem_h"].values() if len(v) > 0]
    h_vals_r2r14_term = [max(v) for v in term_r2r14["elem_h"].values() if len(v) > 0]

    r2r13_term_hmax = max(h_vals_r2r13_term) if h_vals_r2r13_term else 0.0
    r2r14_step1_hmax = max(h_vals_r2r14_step1) if h_vals_r2r14_step1 else 0.0
    r2r14_term_hmax = max(h_vals_r2r14_term) if h_vals_r2r14_term else 0.0

    # Element-by-element L2 difference at handoff
    common_eids = sorted(list(set(term_r2r13["elem_h"].keys()) & set(step1_r2r14["elem_h"].keys())))
    diff_sq_sum = 0.0
    norm_sq_sum = 0.0
    for eid in common_eids:
        h13 = max(term_r2r13["elem_h"][eid])
        h14 = max(step1_r2r14["elem_h"][eid])
        diff_sq_sum += (h14 - h13) ** 2
        norm_sq_sum += (h13) ** 2

    rel_l2_error = np.sqrt(diff_sq_sum) / np.sqrt(norm_sq_sum) if norm_sq_sum > 0 else 0.0
    abs_diff_hmax = abs(r2r14_step1_hmax - r2r13_term_hmax)

    print("\n================================================================================")
    print("ITEM 2: HISTORY FIELD RECONCILIATION SUMMARY")
    print("================================================================================")
    print(f"R2R13_terminal_authoritative_Hmax = {r2r13_term_hmax:.6f}")
    print(f"R2R14_Step1_authoritative_Hmax   = {r2r14_step1_hmax:.6f}")
    print(f"handoff_Hmax_absolute_difference = {abs_diff_hmax:.6f}")
    print(f"handoff_H_field_relative_L2_error = {rel_l2_error:.6e}")
    print(f"R2R14_terminal_authoritative_Hmax = {r2r14_term_hmax:.6f}")

    return {
        "phase_pointwise_violation_count": phase_pointwise_violation_count,
        "phase_max_negative_increment": phase_max_negative_increment,
        "phase_fraction_of_points_with_healing": phase_fraction_of_points_with_healing,
        "history_pointwise_violation_count": history_pointwise_violation_count,
        "history_max_negative_increment": history_max_negative_increment,
        "R2R13_terminal_authoritative_Hmax": r2r13_term_hmax,
        "R2R14_Step1_authoritative_Hmax": r2r14_step1_hmax,
        "handoff_Hmax_absolute_difference": abs_diff_hmax,
        "handoff_H_field_relative_L2_error": rel_l2_error,
        "R2R14_terminal_authoritative_Hmax": r2r14_term_hmax
    }

if __name__ == '__main__':
    audit_pointwise_physics()
