#!/usr/bin/env python3
"""
Mode-II PK10R2 Equation Repair and Deck Integrity Verification Tool
Task ID: F220PREP-M2-PK10R2-EQUATION-REPAIR-AND-QUALIFICATION1
"""

import os
import sys
import hashlib
from pathlib import Path

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def repair_and_verify_pk10r2_deck():
    repo_root = Path(__file__).resolve().parent.parent.parent
    pk10r2_dir = repo_root / "models" / "generated" / "mode_ii" / "production_control_batch" / "M2CORR_PK10R2_TOPOLOGY_CORRECTED"
    inp_path = pk10r2_dir / "M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp"
    
    old_hash = compute_sha256(inp_path)
    print(f"Original PK10R2 INP Hash: {old_hash}")
    
    with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    # Find N_TOP nodes
    ntop_nodes = []
    in_ntop = False
    for line in lines:
        if "*NSET, NSET=N_TOP" in line.upper():
            in_ntop = True
            continue
        if in_ntop:
            if line.startswith("*"):
                in_ntop = False
                continue
            parts = [int(p.strip()) for p in line.replace(",", " ").split() if p.strip()]
            ntop_nodes.extend(parts)
            
    print(f"Found {len(ntop_nodes)} nodes in N_TOP: {ntop_nodes[0]} .. {ntop_nodes[-1]}")
    assert len(ntop_nodes) == 127, f"Expected 127 nodes, got {len(ntop_nodes)}"
    
    # Locate the erroneous *Equation block
    eq_start = None
    eq_end = None
    for i, line in enumerate(lines):
        if line.strip().upper() == "*EQUATION":
            eq_start = i
            # The next two lines are '2' and 'N_TOP, 1, 1.0, N_RP, 1, -1.0'
            eq_end = i + 3
            break
            
    assert eq_start is not None, "Could not find *Equation in INP"
    print(f"Found *Equation at line {eq_start+1} to {eq_end}")
    print("Old block:")
    for l in lines[eq_start:eq_end]:
        print("  ", l.strip())
        
    # Construct replacement equation blocks (H1/H2 reference standard)
    new_eq_lines = ["** ==========================================================\n",
                    "** EQUATIONS (Mode-II pure shear constraint: individual top ties)\n",
                    "** ==========================================================\n"]
    for nid in ntop_nodes:
        new_eq_lines.append("*Equation\n")
        new_eq_lines.append("2\n")
        new_eq_lines.append(f"{nid}, 1, 1.0, 99999, 1, -1.0\n")
        
    # Assemble new deck
    # Find where the section comment starts before *Equation if present
    comment_start = eq_start
    if lines[eq_start-1].startswith("**") and lines[eq_start-2].startswith("**") and lines[eq_start-3].startswith("**"):
        comment_start = eq_start - 3
        
    new_lines = lines[:comment_start] + new_eq_lines + lines[eq_end:]
    
    # Write repaired file
    with open(inp_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    new_hash = compute_sha256(inp_path)
    print(f"\nRepaired PK10R2 INP Hash: {new_hash}")
    
    # Integrity verification
    print("\n=== DECK INTEGRITY VERIFICATION ===")
    with open(inp_path, "r", encoding="utf-8") as f:
        re_lines = f.readlines()
        
    eq_count = 0
    constrained_nodes = set()
    for i, l in enumerate(re_lines):
        if l.strip().upper() == "*EQUATION":
            eq_count += 1
            data_line = re_lines[i+2].strip()
            parts = [p.strip() for p in data_line.split(",")]
            node_i = int(parts[0])
            dof1 = int(parts[1])
            coeff1 = float(parts[2])
            rp_node = int(parts[3])
            dof2 = int(parts[4])
            coeff2 = float(parts[5])
            
            assert dof1 == 1, f"Expected DOF 1, got {dof1}"
            assert coeff1 == 1.0, f"Expected coeff 1.0, got {coeff1}"
            assert rp_node == 99999, f"Expected RP node 99999, got {rp_node}"
            assert dof2 == 1, f"Expected RP DOF 1, got {dof2}"
            assert coeff2 == -1.0, f"Expected RP coeff -1.0, got {coeff2}"
            constrained_nodes.add(node_i)
            
    print(f"Total *Equation blocks verified: {eq_count}")
    print(f"Total Unique Constrained Top Nodes: {len(constrained_nodes)}")
    assert eq_count == 127, f"Expected 127 equations, got {eq_count}"
    assert constrained_nodes == set(ntop_nodes), "Mismatch between N_TOP and constrained nodes!"
    print("ALL 127 TOP NODES CONSTRAINED INDIVIDUALLY AND RIGIDLY TO RP (99999) WITH ZERO SUMMATION REMAINING: PASS!")

if __name__ == "__main__":
    repair_and_verify_pk10r2_deck()
