#!/usr/bin/env python3
"""
Inspect msg lines between 39000 and 50000 to trace the second call/iteration in Step 1.
"""
from pathlib import Path

def inspect_msg_between():
    root = Path(__file__).resolve().parent.parent.parent
    msg_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.msg"
    
    with open(msg_path, "r", errors="ignore") as f:
        for idx, line in enumerate(f):
            if idx >= 39200 and idx <= 49600:
                if any(k in line for k in ["ITERATION", "CONVERGENCE", "RESIDUAL", "PIVOT", "SINGULAR", "NEGATIVE", "INCREMENT", "STEP", "JELEM=  9877", "JELEM= 19477", "JELEM= 19752", "JELEM= 19753"]):
                    print(f"Line {idx+1}: {line.strip()}")

if __name__ == "__main__":
    inspect_msg_between()
