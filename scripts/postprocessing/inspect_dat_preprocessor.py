#!/usr/bin/env python3
"""
Inspect the entire preprocessor header and all warnings/notes in M2STATE_FRACFIX_RESTART2R5.dat.
"""
from pathlib import Path

def inspect_dat_preprocessor():
    root = Path(__file__).resolve().parent.parent.parent
    dat_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.dat"
    
    with open(dat_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    print("=== DAT PREPROCESSOR AUDIT (First 300 lines) ===")
    for i, line in enumerate(lines[:300]):
        if any(w in line for w in ["WARNING", "NOTE", "ERROR", "EQUATION", "MPCS", "DEGREE OF FREEDOM"]):
            print(f"Line {i+1}: {line.strip()}")

if __name__ == "__main__":
    inspect_dat_preprocessor()
