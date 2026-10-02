#!/usr/bin/env python3
"""
Inspect Both Element Layers (Phase 1..9612 vs Mechanical 9613..19224) in DAT
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_R2R13 = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389325.mmaster02"
EVIDENCE_R2R14 = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389328.mmaster02"
DAT_R2R13 = EVIDENCE_R2R13 / "M2STATE_FRACFIX_RESTART2R13.dat"
DAT_R2R14 = EVIDENCE_R2R14 / "M2STATE_FRACFIX_RESTART2R14.dat"

def inspect_layers(dat_path, desc):
    print(f"\n=== Inspecting {desc} ({dat_path.name}) ===")
    lines = dat_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    
    # Check Step 1 Inc 1 and Terminal Inc
    inc_indices = []
    for i, l in enumerate(lines):
        if "INCREMENT" in l and "SUMMARY" in l:
            inc_indices.append(i)
            
    print(f"Total increments found: {len(inc_indices)}")

    for tag, inc_idx in [("First Inc (Step 1 Inc 1)", inc_indices[0]), ("Last Inc (Terminal)", inc_indices[-1])]:
        block = lines[inc_idx:inc_idx+200000] # large enough
        
        phase_sdv16 = {}
        mech_sdv16 = {}
        
        in_elem_tab = False
        for l in block:
            if "THE FOLLOWING TABLE IS PRINTED AT THE INTEGRATION POINTS" in l:
                in_elem_tab = True
                continue
            elif "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in l:
                in_elem_tab = False
                break
            if in_elem_tab:
                parts = l.split()
                if len(parts) >= 5 and parts[0].isdigit():
                    eid = int(parts[0])
                    # parts: [eid, sdv13, sdv14, sdv15, sdv16] or [eid, ipt, sdv13, sdv14, sdv15, sdv16]
                    h_val = float(parts[-1])
                    if eid <= 9612:
                        phase_sdv16[eid] = h_val
                    else:
                        mech_sdv16[eid] = h_val

        max_phase = max(phase_sdv16.values()) if phase_sdv16 else 0.0
        max_mech = max(mech_sdv16.values()) if mech_sdv16 else 0.0
        print(f"{tag}:")
        print(f"  Phase Elements (1..9612): count = {len(phase_sdv16)}, max(SDV16) = {max_phase:.6f}")
        print(f"  Mech  Elements (9613..19224): count = {len(mech_sdv16)}, max(SDV16) = {max_mech:.6f}")

if __name__ == '__main__':
    inspect_layers(DAT_R2R13, "R2R13 (1389325.mmaster02)")
    inspect_layers(DAT_R2R14, "R2R14 (1389328.mmaster02)")
