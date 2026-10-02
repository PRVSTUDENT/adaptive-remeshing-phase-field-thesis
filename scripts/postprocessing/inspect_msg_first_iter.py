#!/usr/bin/env python3
"""
Inspect msg lines between 29700 and 40000 to see what happened during the first iteration calls to JTYPE 2.
"""
from pathlib import Path

def inspect_msg_first_iter():
    root = Path(__file__).resolve().parent.parent.parent
    msg_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.msg"
    
    with open(msg_path, "r", errors="ignore") as f:
        for idx, line in enumerate(f):
            if idx >= 29700 and idx <= 40000:
                if "[FORCE_TRACE]" in line or "[H_STARTUP_TRACE]" in line or "JELEM=" in line:
                    print(f"Line {idx+1}: {line.strip()}")

if __name__ == "__main__":
    inspect_msg_first_iter()
