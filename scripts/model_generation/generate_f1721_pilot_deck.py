#!/usr/bin/env python3
"""
Generate Task F1721 Adapted Staggered Diagnostic Pilot Input Deck
(PK_F1721_ADAPTED_PILOT.inp)

Derived from the verified 13,163-element F1720 adapted model (PK_F1720_ADAPTED_PFM.inp),
preserving:
- Exactly 13,402 nodes (13,401 continuum nodes + reference node 13402)
- Exactly 39,489 layered elements (13,163 Layer 1 PF, 13,163 Layer 2 Mech, 13,163 Layer 3 UMAT)
- Identical node sets, element sets, MPC equations, and material properties
- Dummy modulus scaling s = 4.7619e-14 for exact mechanical neutrality

Implements the reconstructed literature increment schedule (Pandey & Kumar 2025 Sec. 4.5):
- Step 1: *STATIC, DIRECT with dt = 1.0e-4, T = 0.20 (2,000 increments to uy = 0.0050 mm)
- Step 2: *STATIC, DIRECT with dt = 5.0e-5, T = 0.25 (5,000 increments to uy = 0.0100 mm)
"""

import os
import hashlib

def build_f1721_pilot_deck(source_path, target_path):
    print(f"Reading source deck: {source_path}")
    with open(source_path, 'r') as f:
        lines = f.readlines()
    
    # Locate where Step 1 begins
    step1_idx = None
    for i, line in enumerate(lines):
        if line.strip().upper().startswith('*STEP') and 'STEP-1' in line.strip().upper():
            # Go back to find comment banner before step 1
            step1_idx = i
            while step1_idx > 0 and lines[step1_idx - 1].strip().startswith('**'):
                step1_idx -= 1
            break
            
    if step1_idx is None:
        raise ValueError("Could not find Step-1 in source deck!")
        
    print(f"Preserving base model lines 0 to {step1_idx-1} ({step1_idx} lines)")
    
    # Create new header
    header_lines = [
        "*HEADING\n",
        "Task F1721: Five-Hole Staggered Operator-Split Adaptive Diagnostic Pilot (Method A)\n",
        "** Specimen: Pandey & Kumar (2025) Section 4.5 Five-Hole Plate (1.0 x 1.0 mm)\n",
        "** Physical Mesh: 13163 elements (12851 quads, 312 tris), 13401 nodes\n",
        "** Total Layered Elements: 39489, Total Nodes: 13402\n",
        "** Reconstructed Literature Schedule: *STATIC, DIRECT\n",
        "** Step 1: 2,000 incs at dt = 1.0e-4, T = 0.20 -> delta_u = 2.5 nm/inc to u = 0.0050 mm\n",
        "** Step 2: 5,000 incs at dt = 5.0e-5, T = 0.25 -> delta_u = 1.0 nm/inc to u = 0.0100 mm\n",
        "** Subroutine: f1721_proposed_staggered_coupling_uel.for\n",
        "** ==========================================================\n"
    ]
    
    # Locate where heading ends in source (first user element card)
    uel_idx = None
    for i, line in enumerate(lines):
        if line.strip().upper().startswith('*USER ELEMENT'):
            uel_idx = i
            break
            
    if uel_idx is None:
        raise ValueError("Could not find *USER ELEMENT in source deck!")
        
    # Reconstructed step definitions
    step_lines = [
        "** ----------------------------------------------------------\n",
        "** STEP 1: Pre-Critical Loading to u = 0.0050 mm (Reconstructed Literature Schedule)\n",
        "** 2,000 increments at dt = 1.0e-4, T_step = 0.20 -> delta_u = 2.5 nm/inc\n",
        "** ----------------------------------------------------------\n",
        "*STEP, NAME=Step-1, NLGEOM=NO, INC=2500\n",
        "*STATIC, DIRECT\n",
        "1.0e-4, 0.20\n",
        "*BOUNDARY\n",
        "N_BOTTOM, 2, 2, 0.0\n",
        "N_PIN, 1, 1, 0.0\n",
        "N_RP, 1, 1, 0.0\n",
        "N_RP, 2, 2, 0.0050\n",
        "*OUTPUT, FIELD, FREQUENCY=10\n",
        "*ELEMENT OUTPUT, ELSET=umatelem\n",
        "S, MISESERI, MISESAVG, EVOL, SDV\n",
        "*ELEMENT OUTPUT, ELSET=PHASE_ELEM\n",
        "SDV\n",
        "*NODE OUTPUT, NSET=N_RP\n",
        "U, RF\n",
        "*NODE OUTPUT, NSET=N_BOTTOM\n",
        "RF\n",
        "*OUTPUT, HISTORY\n",
        "*NODE OUTPUT, NSET=N_RP\n",
        "U2, RF2\n",
        "*END STEP\n",
        "** ----------------------------------------------------------\n",
        "** STEP 2: Critical Fracture Propagation to u = 0.0100 mm (Reconstructed Literature Schedule)\n",
        "** 5,000 increments at dt = 5.0e-5, T_step = 0.25 -> delta_u = 1.0 nm/inc\n",
        "** ----------------------------------------------------------\n",
        "*STEP, NAME=Step-2, NLGEOM=NO, INC=6000\n",
        "*STATIC, DIRECT\n",
        "5.0e-5, 0.25\n",
        "*BOUNDARY\n",
        "N_BOTTOM, 2, 2, 0.0\n",
        "N_PIN, 1, 1, 0.0\n",
        "N_RP, 1, 1, 0.0\n",
        "N_RP, 2, 2, 0.0100\n",
        "*OUTPUT, FIELD, FREQUENCY=10\n",
        "*ELEMENT OUTPUT, ELSET=umatelem\n",
        "S, MISESERI, MISESAVG, EVOL, SDV\n",
        "*ELEMENT OUTPUT, ELSET=PHASE_ELEM\n",
        "SDV\n",
        "*NODE OUTPUT, NSET=N_RP\n",
        "U, RF\n",
        "*NODE OUTPUT, NSET=N_BOTTOM\n",
        "RF\n",
        "*OUTPUT, HISTORY\n",
        "*NODE OUTPUT, NSET=N_RP\n",
        "U2, RF2\n",
        "*END STEP\n"
    ]
    
    # Assemble full deck
    out_lines = header_lines + lines[uel_idx:step1_idx] + step_lines
    
    print(f"Writing target deck: {target_path} ({len(out_lines)} lines)")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, 'w') as f:
        f.writelines(out_lines)
        
    # Compute and report hash
    with open(target_path, 'rb') as f:
        h = hashlib.sha256(f.read()).hexdigest()
    sz = os.path.getsize(target_path)
    print(f"Generated deck successfully:")
    print(f"  Path: {target_path}")
    print(f"  Size: {sz} bytes")
    print(f"  SHA-256: {h}")
    return target_path, sz, h

if __name__ == '__main__':
    src = os.path.join('models', 'pandey_kumar_mode1', '214_f1720_adapted_mesh', 'PK_F1720_ADAPTED_PFM.inp')
    tgt = os.path.join('models', 'pandey_kumar_mode1', '214_f1720_adapted_mesh', 'PK_F1721_ADAPTED_PILOT.inp')
    build_f1721_pilot_deck(src, tgt)
