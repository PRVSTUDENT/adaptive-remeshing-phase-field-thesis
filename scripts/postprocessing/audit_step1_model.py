#!/usr/bin/env python3
"""
Deep audit of Step 1 input deck structure, degrees of freedom, equations, and elements.
"""
from pathlib import Path
from collections import defaultdict

def audit_step1_model():
    root = Path(__file__).resolve().parent.parent.parent
    inp_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.inp"
    
    with open(inp_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    print("=== AUDIT OF M2STATE_FRACFIX_RESTART2R5.INP ===")
    
    # 1. Parse Nodes
    nodes = {}
    in_nodes = False
    for line in lines:
        if line.startswith("*NODE"):
            in_nodes = True
            continue
        elif in_nodes and line.startswith("*"):
            in_nodes = False
        elif in_nodes:
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 3:
                nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                
    print(f"Total Nodes defined: {len(nodes)}")
    
    # 2. Parse Node Sets
    nsets = defaultdict(list)
    current_nset = None
    for line in lines:
        if line.startswith("*NSET"):
            m = line.split("NSET=")[1].split(",")[0].strip()
            current_nset = m
        elif current_nset and line.startswith("*"):
            current_nset = None
        elif current_nset:
            parts = [p.strip() for p in line.split(",") if p.strip()]
            for p in parts:
                nsets[current_nset].append(int(p))
                
    for nset_name, nlist in nsets.items():
        print(f"NSET {nset_name}: {len(nlist)} nodes (min={min(nlist)}, max={max(nlist)})")
        
    # 3. Parse Equations
    equations = []
    in_equation = False
    eq_terms_expected = 0
    for line in lines:
        if line.startswith("*EQUATION"):
            in_equation = True
            eq_terms_expected = 0
            continue
        elif in_equation and line.startswith("*"):
            in_equation = False
        elif in_equation:
            if eq_terms_expected == 0:
                eq_terms_expected = int(line.strip())
            else:
                equations.append(line.strip())
                
    print(f"Equations defined ({len(equations)} lines):")
    for eq in equations:
        print(f"  {eq}")
        
    # 4. Parse Step 1 Boundaries
    in_step1 = False
    in_bnd = False
    bnds_step1 = []
    for line in lines:
        if "*STEP, NAME=Step-1-PhaseInit" in line:
            in_step1 = True
            continue
        elif in_step1 and "*END STEP" in line:
            in_step1 = False
            break
        elif in_step1 and line.startswith("*BOUNDARY"):
            in_bnd = True
            continue
        elif in_step1 and in_bnd and line.startswith("*"):
            in_bnd = False
        elif in_step1 and in_bnd:
            bnds_step1.append(line.strip())
            
    print(f"\nStep 1 Boundaries ({len(bnds_step1)} lines):")
    for b in bnds_step1[:10]:
        print(f"  {b}")
    print(f"  ... ({len(bnds_step1) - 10} more boundary cards)")
    
    # Categorize Step 1 Boundaries by DOF
    dof_counts = defaultdict(int)
    for b in bnds_step1:
        parts = [p.strip() for p in b.split(",") if p.strip()]
        if len(parts) >= 3:
            dof_start = int(parts[1])
            dof_end = int(parts[2])
            for d in range(dof_start, dof_end + 1):
                dof_counts[d] += 1
                
    print("\nStep 1 Prescribed Boundary Counts by DOF:")
    for dof, count in sorted(dof_counts.items()):
        print(f"  DOF {dof}: {count} specifications")

if __name__ == "__main__":
    audit_step1_model()
