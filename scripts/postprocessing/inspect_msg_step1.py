#!/usr/bin/env python3
from pathlib import Path

def inspect_msg_step1():
    root = Path(__file__).resolve().parent.parent.parent
    msg_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.msg"
    
    with open(msg_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    print(f"Total lines in msg: {len(lines)}")
    
    # Print first 200 lines
    for i, line in enumerate(lines[:200]):
        print(f"{i+1}: {line.rstrip()}")

if __name__ == "__main__":
    inspect_msg_step1()
