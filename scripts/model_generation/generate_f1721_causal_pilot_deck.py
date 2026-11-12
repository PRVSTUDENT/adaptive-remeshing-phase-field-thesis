#!/usr/bin/env python3
"""
Generate Task F1721 Bounded Causal-Isolation Pilot Input Deck
(PK_F1721_CAUSAL_PILOT.inp)

Derived from the verified 13,163-element F1720 adapted model (PK_F1720_ADAPTED_PFM.inp),
preserving:
- Exactly 13,402 nodes (13,401 continuum nodes + reference node 13402)
- Exactly 39,489 layered elements (13,163 Layer 1 PF, 13,163 Layer 2 Mech, 13,163 Layer 3 UMAT)
- Identical node sets, element sets, MPC equations, and material properties
- Dummy modulus scaling s = 4.7619e-14 for exact mechanical neutrality
- The original F1720 automatic incrementation strategy (*STATIC with cutbacks down to dt_min = 1.0e-9)

Causal Isolation Design (Supervisory Review HND-F1721-PILOT-QUAL-001):
- Changes ONLY the coupling implementation (trial-state reads -> committed-state reads in UEL)
- Holds the original F1720 automatic incrementation controls (*STATIC, dt_initial=0.0025, dt_min=1.0e-9)
- Shortens the Step 2 displacement target from 0.0080 mm to 0.00580 mm (just past the 0.0056645 mm failure point)
- Provides a strict 1-variable causal test of Hypothesis F1721-H1-R1
"""

import os
import hashlib

def build_f1721_causal_pilot_deck(source_path, target_path):
    print(f"Reading source deck: {source_path}")
    with open(source_path, 'r') as f:
        lines = f.readlines()
    
    # Locate where Step 1 begins
    step1_idx = None
    for i, line in enumerate(lines):
        if line.strip().upper().startswith('*STEP') and 'STEP-1' in line.strip().upper():
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
        "Task F1721: Five-Hole Bounded Causal-Isolation Diagnostic Pilot (Method A)\n",
        "** Specimen: Pandey & Kumar (2025) Section 4.5 Five-Hole Plate (1.0 x 1.0 mm)\n",
        "** Physical Mesh: 13163 elements (12851 quads, 312 tris), 13401 nodes\n",
        "** Total Layered Elements: 39489, Total Nodes: 13402\n",
        "** Causal Isolation Control: Retains original F1720 *STATIC automatic incrementation\n",
        "** Step 1: *STATIC, 0.02, 1.0, 1.0e-8, 0.02 -> uy = 0.0050 mm (50 nominal incs)\n",
        "** Step 2: *STATIC, 0.0025, 0.2666666666667, 1.0e-9, 0.0025 -> uy = 0.00580 mm (preserves rate 0.0030 mm/time)\n",
        "** Subroutine: f1721_proposed_staggered_coupling_uel.for (committed-state reads)\n",
        "** Supervisory Directives: HND-F1721-PILOT-QUAL-001/002 Causal Isolation Protocol\n",
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
        
    # Causal step definitions (preserving F1720 *STATIC automatic incrementation)
    step_lines = [
        "** ----------------------------------------------------------\n",
        "** STEP 1: Pre-Critical Loading to u = 0.0050 mm (Identical to F1720 Baseline)\n",
        "** ----------------------------------------------------------\n",
        "*STEP, NAME=Step-1, NLGEOM=NO, INC=2500\n",
        "*STATIC\n",
        "0.02, 1.0, 1.0e-8, 0.02\n",
        "*BOUNDARY\n",
        "N_BOTTOM, 2, 2, 0.0\n",
        "N_PIN, 1, 1, 0.0\n",
        "N_RP, 1, 1, 0.0\n",
        "N_RP, 2, 2, 0.0050\n",
        "*OUTPUT, FIELD, FREQUENCY=1\n",
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
        "** STEP 2: Critical Fracture Propagation to uy = 0.00580 mm (Bounded Causal Pilot)\n",
        "** Retains F1720 *STATIC automatic incrementation (dt_initial=0.0025, dt_min=1.0e-9)\n",
        "** Sets Step 2 time period T2 = 0.2666666666667 to preserve physical loading rate 0.0030 mm/time\n",
        "** ----------------------------------------------------------\n",
        "*STEP, NAME=Step-2, NLGEOM=NO, INC=5000\n",
        "*STATIC\n",
        "0.0025, 0.2666666666667, 1.0e-9, 0.0025\n",
        "*BOUNDARY\n",
        "N_BOTTOM, 2, 2, 0.0\n",
        "N_PIN, 1, 1, 0.0\n",
        "N_RP, 1, 1, 0.0\n",
        "N_RP, 2, 2, 0.00580\n",
        "*OUTPUT, FIELD, FREQUENCY=1\n",
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
    print(f"Generated causal pilot deck successfully:")
    print(f"  Path: {target_path}")
    print(f"  Size: {sz} bytes")
    print(f"  SHA-256: {h}")
    return target_path, sz, h

if __name__ == '__main__':
    src = os.path.join('models', 'pandey_kumar_mode1', '214_f1720_adapted_mesh', 'PK_F1720_ADAPTED_PFM.inp')
    tgt = os.path.join('models', 'pandey_kumar_mode1', '214_f1720_adapted_mesh', 'PK_F1721_CAUSAL_PILOT.inp')
    build_f1721_causal_pilot_deck(src, tgt)
