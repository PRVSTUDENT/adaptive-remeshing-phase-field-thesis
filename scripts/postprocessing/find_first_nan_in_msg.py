#!/usr/bin/env python3
"""
Find exact first line in M2STATE_FRACFIX_RESTART2R5.msg containing NaN or non-finite value.
"""
from pathlib import Path

def find_first_nan_in_msg():
    root = Path(__file__).resolve().parent.parent.parent
    msg_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.msg"
    
    with open(msg_path, "r", errors="ignore") as f:
        for idx, line in enumerate(f):
            if "NaN" in line or "nan" in line or "Infinity" in line or "inf" in line:
                print(f"FIRST NON-FINITE IN MSG AT LINE {idx+1}:")
                print(line.rstrip())
                # Print previous 10 lines
                break

if __name__ == "__main__":
    find_first_nan_in_msg()
