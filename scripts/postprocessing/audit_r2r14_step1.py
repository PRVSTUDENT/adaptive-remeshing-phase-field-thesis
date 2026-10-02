#!/usr/bin/env python3
"""
Audit Step 1 PhaseInit Solve for M2STATE_FRACFIX_RESTART2R14
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R14"
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
REMOTE_DAT = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R14/M2STATE_FRACFIX_RESTART2R14_STEP1.dat"

def main():
    local_dat = LOCAL_PKG_DIR / "M2STATE_FRACFIX_RESTART2R14_STEP1.dat"
    scp_cmd = ["scp", "-i", SSH_KEY, f"{SSH_HOST}:{REMOTE_DAT}", str(local_dat)]
    subprocess.run(scp_cmd, check=True)
    
    lines = local_dat.read_text(encoding="utf-8", errors="ignore").splitlines()
    rf1_bot = 0.0
    rf2_bot = 0.0
    rp_rf1 = 0.0
    in_all_table = False
    in_rp_table = False
    for l in lines:
        if "THE FOLLOWING TABLE IS PRINTED FOR NODE SET N_RP" in l:
            in_rp_table = True
            in_all_table = False
            continue
        if in_rp_table:
            parts = l.split()
            if len(parts) >= 2 and parts[0] == "99999":
                rp_rf1 = float(parts[-1])
                in_rp_table = False
        if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in l:
            in_all_table = True
            continue
        if in_all_table and "MAXIMUM" in l:
            in_all_table = False
            break
        if in_all_table:
            parts = l.split()
            if len(parts) >= 2 and parts[0] == "99999":
                rp_rf1 = float(parts[-1])
            elif len(parts) >= 6 and parts[0].isdigit():
                nid = int(parts[0])
                if nid % 49 == 1:  # bottom node
                    rf1_bot += float(parts[4])
                    rf2_bot += float(parts[5])

    print("================================================================================")
    print("STEP 1 PHASEINIT RECONCILIATION AUDIT: M2STATE_FRACFIX_RESTART2R14")
    print("================================================================================")
    print(f"Source 1389325 Terminal RF1 (U1=0.030mm):  0.654334 kN")
    print(f"Target R2R14 Step 1 RP RF1:                {rp_rf1:.6f} kN")
    print(f"Target R2R14 Step 1 Bottom Sum RF1:        {rf1_bot:.6f} kN")
    print(f"Absolute Force Difference:                 {abs(rp_rf1 - 0.654334):.6f} kN")
    pct_diff = abs(rp_rf1 - 0.654334) / 0.654334 * 100
    print(f"Percentage Discrepancy:                    {pct_diff:.4f}%")
    print(f"Global RF1 Equilibrium (RP + Bottom):      {rp_rf1 + rf1_bot:.6e} kN")
    print(f"Global RF2 Equilibrium (Bottom):           {rf2_bot:.6e} kN")
    
    if pct_diff < 0.1:
        print("\nQUALIFICATION VERDICT: PASS_EXACT_PHYSICAL_CONTINUITY")
    else:
        print("\nQUALIFICATION VERDICT: FAIL")

if __name__ == '__main__':
    main()
