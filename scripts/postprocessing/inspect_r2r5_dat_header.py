#!/usr/bin/env python3
from pathlib import Path

def parse_header():
    root = Path(__file__).resolve().parent.parent.parent
    dat_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.dat"
    with open(dat_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    for i in range(84900, 85010):
        print(f"{i}: {lines[i].rstrip()}")

if __name__ == "__main__":
    parse_header()
