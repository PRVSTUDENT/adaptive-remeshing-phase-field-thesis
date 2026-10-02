#!/usr/bin/env python3
import sys, os, re
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent.parent
    r2r4_dir = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R4"
    r2r4_inp = r2r4_dir / "M2STATE_FRACFIX_RESTART2R4.inp"
    r2r4_for = r2r4_dir / "f42_mixed_uel.for"
    
    print("=== ROOT CAUSE 1: N_TOP CONNECTIVITY & COORDINATES ===")
    nodes = {}
    elements = {}
    nsets = {}
    
    current_set = None
    reading_nodes = False
    reading_elements = False
    
    with open(r2r4_inp, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*NODE"):
                reading_nodes = True
                reading_elements = False
                current_set = None
                continue
            elif l.startswith("*ELEMENT"):
                reading_nodes = False
                reading_elements = True
                current_set = None
                continue
            elif l.startswith("*NSET"):
                reading_nodes = False
                reading_elements = False
                m = re.search(r"NSET=([A-Za-z0-9_]+)", l, re.I)
                if m:
                    current_set = m.group(1)
                    if current_set not in nsets:
                        nsets[current_set] = []
                continue
            elif l.startswith("*"):
                reading_nodes = False
                reading_elements = False
                current_set = None
                continue
                
            if reading_nodes:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    nodes[nid] = (x, y)
                except (ValueError, IndexError):
                    pass
            elif reading_elements:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                try:
                    eid = int(parts[0])
                    elem_nodes = [int(p) for p in parts[1:]]
                    elements[eid] = elem_nodes
                except (ValueError, IndexError):
                    pass
            elif current_set:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                for p in parts:
                    try:
                        nsets[current_set].append(int(p))
                    except ValueError:
                        pass
                        
    print(f"Total declared nodes in INP: {len(nodes)}")
    print(f"Total declared elements in INP: {len(elements)}")
    
    # Active element nodes
    active_elem_nodes = set()
    for eid, enodes in elements.items():
        for nid in enodes:
            active_elem_nodes.add(nid)
            
    print(f"Active nodes connected to elements: {len(active_elem_nodes)} (min={min(active_elem_nodes)}, max={max(active_elem_nodes)})")
    
    # Unconnected / orphan nodes
    orphan_nodes = set(nodes.keys()) - active_elem_nodes
    print(f"Declared nodes not in any element: {len(orphan_nodes)} (min={min(orphan_nodes) if orphan_nodes else 'N/A'}, max={max(orphan_nodes) if orphan_nodes else 'N/A'})")
    
    # Check N_TOP
    n_top = nsets.get("N_TOP", [])
    print(f"N_TOP node count: {len(n_top)}")
    n_top_connected = [n for n in n_top if n in active_elem_nodes]
    n_top_orphan = [n for n in n_top if n in orphan_nodes]
    print(f"N_TOP connected node count: {len(n_top_connected)}")
    print(f"N_TOP orphan node count: {len(n_top_orphan)}")
    
    if n_top_orphan:
        y_orphans = [nodes[n][1] for n in n_top_orphan]
        print(f"N_TOP orphan Y coordinates: min={min(y_orphans)}, max={max(y_orphans)}")
        
    # Find actual physical top boundary nodes among active element nodes
    y_max_active = max(nodes[n][1] for n in active_elem_nodes)
    print(f"Physical top Y among active connected nodes: {y_max_active:.6f}")
    
    physical_top_nodes = [n for n in active_elem_nodes if abs(nodes[n][1] - y_max_active) < 1e-5]
    print(f"Physical top connected node count: {len(physical_top_nodes)} (min={min(physical_top_nodes)}, max={max(physical_top_nodes)})")
    
    # Check N_BOTTOM
    n_bottom = nsets.get("N_BOTTOM", [])
    y_min_active = min(nodes[n][1] for n in active_elem_nodes)
    print(f"Physical bottom Y among active connected nodes: {y_min_active:.6f}")
    n_bottom_connected = [n for n in n_bottom if n in active_elem_nodes]
    n_bottom_orphan = [n for n in n_bottom if n in orphan_nodes]
    print(f"N_BOTTOM node count: {len(n_bottom)} (connected={len(n_bottom_connected)}, orphan={len(n_bottom_orphan)})")

    print("\n=== ROOT CAUSE 2: STEP 1 BOUNDARY DISPLACEMENT ===")
    step1_lines = []
    in_step1 = False
    with open(r2r4_inp, "r") as f:
        for line in f:
            if "STEP, NAME=Step-1" in line:
                in_step1 = True
            elif "STEP, NAME=Step-2" in line:
                in_step1 = False
            if in_step1:
                step1_lines.append(line)
                
    rp_step1_disp = None
    for line in step1_lines:
        if "99999," in line or "N_TOP," in line:
            print(f"Step 1 boundary line: {line.strip()}")
            
    print("\n=== ROOT CAUSE 3: JTYPE 4 F_INT INITIALIZATION ===")
    with open(r2r4_for, "r") as f:
        content = f.read()
        
    jtype4_block = content.split("ELSE IF (JTYPE .EQ. 4) THEN")[1].split("C ===")[0]
    has_f_int_zero = "F_INT(1)" in jtype4_block and "ZERO" in jtype4_block and "=" in jtype4_block
    print(f"JTYPE 4 has explicit F_INT zeroing: {has_f_int_zero}")
    if not has_f_int_zero:
        print("Confirmed: JTYPE 4 lacks DO I=1, 6; F_INT(I) = ZERO; ENDDO before accumulation.")

if __name__ == "__main__":
    main()
