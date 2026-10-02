#!/usr/bin/env python3
from pathlib import Path

def find_first_nan():
    root = Path(__file__).resolve().parent.parent.parent
    log_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.o$PBS_JOBID"
    
    with open(log_path, "r", errors="ignore") as f:
        line_num = 0
        for line in f:
            line_num += 1
            if "NaN" in line or "nan" in line or "Infinity" in line or "inf" in line:
                print(f"FIRST NON-FINITE FOUND AT LINE {line_num}:")
                print(line.strip())
                # Print next 5 lines
                for _ in range(5):
                    print(f.readline().strip())
                break

if __name__ == "__main__":
    find_first_nan()
