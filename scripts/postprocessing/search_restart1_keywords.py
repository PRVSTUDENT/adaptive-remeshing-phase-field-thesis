#!/usr/bin/env python3
from pathlib import Path

def search_keywords():
    root = Path(__file__).resolve().parent.parent.parent
    inp_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6R2/M2STATE_FRACFIX_RESTART1R1R6R2.inp"
    with open(inp_path, "r", errors="ignore") as f:
        for i, line in enumerate(f):
            if line.startswith("*") and not line.startswith("**"):
                print(f"Line {i+1}: {line.strip()}")

if __name__ == "__main__":
    search_keywords()
