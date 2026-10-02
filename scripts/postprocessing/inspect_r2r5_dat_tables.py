#!/usr/bin/env python3
from pathlib import Path

def inspect_dat():
    root = Path(__file__).resolve().parent.parent.parent
    dat_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.dat"
    with open(dat_path, "r", errors="ignore") as f:
        in_table = False
        table_lines = []
        for line in f:
            if "NODE OUTPUT" in line or "N O D E   O U T P U T" in line or "U1" in line or "RF1" in line:
                in_table = True
            if in_table:
                table_lines.append(line.rstrip())
                if len(table_lines) >= 60:
                    break
        for l in table_lines:
            print(l)

if __name__ == "__main__":
    inspect_dat()
