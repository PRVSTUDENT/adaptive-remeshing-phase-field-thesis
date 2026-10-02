#!/usr/bin/env python3
from pathlib import Path

def search_dat_steps():
    root = Path(__file__).resolve().parent.parent.parent
    dat_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.dat"
    
    with open(dat_path, "r", errors="ignore") as f:
        for i, line in enumerate(f):
            if "INCREMENT" in line or "STEP" in line or "N O D E   O U T P U T" in line:
                print(f"Line {i+1}: {line.strip()}")

if __name__ == "__main__":
    search_dat_steps()
