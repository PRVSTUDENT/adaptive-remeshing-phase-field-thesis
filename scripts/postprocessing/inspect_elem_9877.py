#!/usr/bin/env python3
"""
Inspect element 9877 definition and its 4 nodes in M2STATE_FRACFIX_RESTART2R5.inp.
"""
from pathlib import Path

def inspect_elem_9877():
    root = Path(__file__).resolve().parent.parent.parent
    inp_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.inp"
    
    with open(inp_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if line.strip().startswith("9877,"):
            print(f"Line {i+1}: {line.strip()}")
            # Parse nodes
            parts = [int(p.strip()) for p in line.split(",") if p.strip()]
            eid = parts[0]
            enodes = parts[1:]
            print(f"Element {eid} has nodes: {enodes}")
            break

if __name__ == "__main__":
    inspect_elem_9877()
