#!/usr/bin/env python3
from pathlib import Path

def parse_msg_solver():
    root = Path(__file__).resolve().parent.parent.parent
    msg_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.msg"
    
    with open(msg_path, "r", errors="ignore") as f:
        count = 0
        for line in f:
            if not line.startswith("[") and ("ITERATION" in line or "CONVERGENCE" in line or "CRITERIA" in line or "INCREMENT" in line or "ERROR" in line or "WARNING" in line or "CORRECTION" in line or "RESIDUAL" in line or "PIVOT" in line or "SINGULARITY" in line or "STEP" in line):
                print(line.rstrip())
                count += 1
                if count >= 100:
                    break

if __name__ == "__main__":
    parse_msg_solver()
