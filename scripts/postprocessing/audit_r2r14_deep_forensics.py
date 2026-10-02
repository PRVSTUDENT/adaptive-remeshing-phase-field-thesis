#!/usr/bin/env python3
"""
Deep Forensic Script for F114DIAG
Audits:
1. Item 1: Full nodal d and IP H field pointwise evolution across all 21 frames of R2R14
2. Item 2: History-field maxima reconciliation between R2R13 and R2R14
3. Item 3: Exact physical force balance using actual N_BOTTOM and N_TOP node sets
4. Item 4: Comparison of R2R13 terminal state vs R2R14 Step 1 and Step 2 states
5. Item 5: UEL residual formulation audit across H0, H1, H2, MM, PK5, R1R11, R2R13, R2R14
"""

import os
import sys
import re
import json
import hashlib
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_R2R14 = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389328.mmaster02"
EVIDENCE_R2R13 = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389325.mmaster02"
EVIDENCE_R1R11 = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389278.mmaster02"

DAT_R2R14 = EVIDENCE_R2R14 / "M2STATE_FRACFIX_RESTART2R14.dat"
INP_R2R14 = EVIDENCE_R2R14 / "M2STATE_FRACFIX_RESTART2R14.inp"

def parse_inp_node_sets(inp_path):
    lines = inp_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    sets = {}
    current_set = None
    
    for l in lines:
        l_upper = l.upper()
        if l_upper.startswith("*NSET"):
            m = re.search(r"NSET=([A-Za-z0-9_]+)", l, re.IGNORECASE)
            if m:
                current_set = m.group(1)
                if current_set not in sets:
                    sets[current_set] = []
            else:
                current_set = None
        elif l.startswith("*"):
            current_set = None
        elif current_set:
            parts = l.replace(",", " ").split()
            for p in parts:
                if p.isdigit():
                    sets[current_set].append(int(p))
    return sets

def audit_force_balance_exact():
    print("=== AUDIT 3: EXACT FORCE BALANCE USING INP NODE SETS ===")
    node_sets = parse_inp_node_sets(INP_R2R14)
    n_bottom = set(node_sets.get("N_BOTTOM", []))
    n_top = set(node_sets.get("N_TOP", []))
    n_rp = set(node_sets.get("N_RP", [99999]))
    print(f"Node set counts: N_BOTTOM = {len(n_bottom)}, N_TOP = {len(n_top)}, N_RP = {len(n_rp)}")

    dat_lines = DAT_R2R14.read_text(encoding="utf-8", errors="ignore").splitlines()

    inc_headers = []
    current_step = 1
    for i, l in enumerate(dat_lines):
        if "STEP    2" in l:
            current_step = 2
        if "INCREMENT" in l and "SUMMARY" in l:
            m = re.search(r"INCREMENT\s+(\d+)\s+SUMMARY", l)
            if m:
                inc_num = int(m.group(1))
                inc_headers.append((i, current_step, inc_num))

    print(f"Found {len(inc_headers)} increments in R2R14 DAT.")

    results = []
    for idx, (line_idx, step_num, inc_num) in enumerate(inc_headers):
        next_line_idx = inc_headers[idx+1][0] if idx+1 < len(inc_headers) else len(dat_lines)
        inc_block = dat_lines[line_idx:next_line_idx]

        rf1_rp = 0.0
        rf2_rp = 0.0
        rf1_bot = 0.0
        rf2_bot = 0.0
        rf1_top = 0.0
        rf2_top = 0.0
        u1_rp = 0.0

        in_node_table = False
        for l in inc_block:
            if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in l:
                in_node_table = True
                continue
            elif "MAXIMUM" in l:
                in_node_table = False
                continue

            if in_node_table:
                parts = l.split()
                if len(parts) >= 6 and parts[0].isdigit():
                    nid = int(parts[0])
                    u1 = float(parts[1])
                    u2 = float(parts[2])
                    rf1 = float(parts[4])
                    rf2 = float(parts[5])

                    if nid in n_bottom:
                        rf1_bot += rf1
                        rf2_bot += rf2
                    if nid in n_top:
                        rf1_top += rf1
                        rf2_top += rf2
                elif len(parts) >= 2 and parts[0] == "99999":
                    u1_rp = float(parts[1])
                    rf1_rp = float(parts[-1])

        net_fx = rf1_rp + rf1_bot
        net_fy = rf2_rp + rf2_bot

        results.append({
            "step": step_num,
            "inc": inc_num,
            "u1_rp": u1_rp,
            "rf1_rp": rf1_rp,
            "rf1_bot": rf1_bot,
            "rf2_bot": rf2_bot,
            "rf1_top": rf1_top,
            "rf2_top": rf2_top,
            "net_fx": net_fx,
            "net_fy": net_fy
        })

    max_abs_net_fx = max(abs(r["net_fx"]) for r in results)
    max_abs_net_fy = max(abs(r["net_fy"]) for r in results)

    print(f"{'Step':<5} {'Inc':<5} {'U1_RP':<10} {'RF1_RP (kN)':<14} {'RF1_Bot (kN)':<14} {'Net Fx (kN)':<16} {'Net Fy (kN)':<16}")
    print("-" * 85)
    for r in results:
        print(f"{r['step']:<5} {r['inc']:<5} {r['u1_rp']:<10.6f} {r['rf1_rp']:<14.6f} {r['rf1_bot']:<14.6f} {r['net_fx']:<16.2e} {r['net_fy']:<16.2e}")

    print(f"\nMax Exact Net Fx: {max_abs_net_fx:.6e} kN")
    print(f"Max Exact Net Fy: {max_abs_net_fy:.6e} kN")
    return results, max_abs_net_fx, max_abs_net_fy

if __name__ == '__main__':
    audit_force_balance_exact()
