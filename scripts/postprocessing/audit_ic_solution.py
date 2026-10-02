#!/usr/bin/env python3
from pathlib import Path

def audit_ic_solution():
    inp_path = Path("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.inp")
    
    with open(inp_path, "r", errors="ignore") as f:
        in_ic = False
        ic_eids = []
        ic_nonfinite = 0
        for line in f:
            if line.startswith("*INITIAL CONDITIONS, TYPE=SOLUTION"):
                in_ic = True
                continue
            elif in_ic and line.startswith("*"):
                in_ic = False
                break
            elif in_ic:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if len(parts) >= 8:
                    try:
                        eid = int(parts[0])
                        ic_eids.append(eid)
                    except ValueError:
                        pass
                for p in parts:
                    if any(bad in p for bad in ["nan", "NaN", "inf", "Inf"]):
                        ic_nonfinite += 1

    print(f"Total elements with IC SOLUTION: {len(ic_eids)}")
    print(f"  Range: min={min(ic_eids)}, max={max(ic_eids)}")
    print(f"  Non-finite values found: {ic_nonfinite}")

if __name__ == "__main__":
    audit_ic_solution()
