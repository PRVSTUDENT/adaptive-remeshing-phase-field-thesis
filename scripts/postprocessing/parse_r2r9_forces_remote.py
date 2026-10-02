#!/usr/bin/env python3
"""
Remote force parser for R2R9 Step 1 DAT file.
"""

import sys
import json
from pathlib import Path

def main():
    dat_path = Path("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R9/M2STATE_FRACFIX_RESTART2R9_STEP1.dat")
    text = dat_path.read_text(encoding="utf-8", errors="ignore")
    sections = text.split("N O D E   O U T P U T")
    last = sections[-1]

    rp_rf1 = 0.0
    rf1_sum_constrained = 0.0
    rf1_bottom = 0.0

    print("=== FIRST 20 LINES OF LAST NODE OUTPUT SECTION ===")
    for l in last.splitlines()[:20]:
        print(l)

    for line in last.splitlines():
        parts = line.strip().split()
        if not parts or not parts[0].isdigit():
            continue
        nid = int(parts[0])
        if nid == 99999:
            rp_rf1 = float(parts[-1])
        else:
            if len(parts) >= 6:
                try:
                    # Column format: Node, U1, U2, U3, RF1, RF2, RF3
                    rf1 = float(parts[4])
                    rf2 = float(parts[5])
                    if abs(rf1) > 1e-12 or abs(rf2) > 1e-12:
                        rf1_sum_constrained += rf1
                        if nid <= 121:
                            rf1_bottom += rf1
                except:
                    pass

    balance_err = abs(rp_rf1 + rf1_sum_constrained)
    print("\n=== FORCE EXTRACTION RESULTS ===")
    print(f"R2R9_RF1_RP_raw = {rp_rf1:.6f} kN")
    print(f"R2R9_RF1_bottom_raw = {rf1_bottom:.6f} kN")
    print(f"R2R9_RF1_all_constrained_raw = {rf1_sum_constrained:.6f} kN")
    print(f"R2R9_force_balance_error_kN = {balance_err:.6e} kN")

if __name__ == "__main__":
    main()
