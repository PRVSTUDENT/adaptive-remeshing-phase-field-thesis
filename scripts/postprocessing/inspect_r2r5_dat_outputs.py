#!/usr/bin/env python3
from pathlib import Path

def parse_dat_tail():
    root = Path(__file__).resolve().parent.parent.parent
    dat_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.dat"
    with open(dat_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    print(f"Total lines in dat: {len(lines)}")
    print("Lines from 85000 to 85100:")
    for l in lines[85000:85100]:
        print(l.rstrip())

if __name__ == "__main__":
    parse_dat_tail()
