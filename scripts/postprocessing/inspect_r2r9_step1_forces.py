#!/usr/bin/env python3
"""
Inspect R2R9 Step 1 DAT file forces and compare against source job 1389241.
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R2R9_DAT = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R9/M2STATE_FRACFIX_RESTART2R9_STEP1.dat"
SRC_DAT = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389241.mmaster02/M2STATE_FRACFIX_RESTART1R1R8.dat"

def parse_dat_forces(dat_file):
    text = dat_file.read_text(encoding="utf-8", errors="ignore")
    sections = text.split("N O D E   O U T P U T")
    last_section = sections[-1]
    
    rp_rf1 = 0.0
    rf1_sum_constrained = 0.0
    constrained_nodes = {}
    
    for line in last_section.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        if parts[0] == "99999":
            rp_rf1 = float(parts[-1])
        elif parts[0].isdigit():
            nid = int(parts[0])
            # If line has U and RF
            # In UEL decks, U is printed for active DOFs, then RF for active DOFs
            # Let's check line length
            if len(parts) >= 6:
                try:
                    # Column format in DAT: Node, U1, U2, U3, RF1, RF2...
                    # or Node, U1, U2, RF1, RF2
                    # RF1 is typically column index 4 (5th item) or 5 (6th item)
                    # Let's verify by checking if values are non-zero RF
                    # Node 1 to 121 are bottom fixed nodes (U1=0, U2=0, U3=phase, RF1, RF2)
                    pass
                except:
                    pass
    return rp_rf1

def main():
    print("=== SOURCE JOB 1389241.mmaster02 ===")
    src_text = SRC_DAT.read_text(encoding="utf-8", errors="ignore")
    src_sec = src_text.split("N O D E   O U T P U T")[-1]
    
    src_rp_rf1 = 0.0
    src_all_rf1 = 0.0
    src_bottom_rf1 = 0.0
    
    for line in src_sec.splitlines():
        parts = line.strip().split()
        if not parts or not parts[0].isdigit():
            continue
        nid = int(parts[0])
        if nid == 99999:
            src_rp_rf1 = float(parts[-1])
        elif len(parts) >= 6:
            try:
                rf1 = float(parts[4])
                rf2 = float(parts[5])
                if abs(rf1) > 1e-12 or abs(rf2) > 1e-12:
                    src_all_rf1 += rf1
                    if nid <= 121:
                        src_bottom_rf1 += rf1
            except:
                pass

    print(f"Source RP 99999 RF1 = {src_rp_rf1:.6f} kN")
    print(f"Source Bottom RF1 Sum (nodes 1-121) = {src_bottom_rf1:.6f} kN")
    print(f"Source All Constrained RF1 Sum = {src_all_rf1:.6f} kN")
    print(f"Source Balance Error = {abs(src_rp_rf1 + src_all_rf1):.6e} kN")

if __name__ == "__main__":
    main()
