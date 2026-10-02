#!/usr/bin/env python3
"""
Inspect all convergence, solver, singularity, and iteration lines in M2STATE_FRACFIX_RESTART2R5.msg.
"""
from pathlib import Path

def inspect_msg_convergence():
    root = Path(__file__).resolve().parent.parent.parent
    msg_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.msg"
    
    with open(msg_path, "r", errors="ignore") as f:
        for idx, line in enumerate(f):
            if any(k in line for k in ["ITERATION", "CONVERGENCE", "RESIDUAL", "PIVOT", "SINGULAR", "NEGATIVE", "INCREMENT", "STEP"]):
                if not ("[H_STARTUP_TRACE]" in line or "[FORCE_TRACE]" in line or "[STATE_TRACE]" in line):
                    print(f"Line {idx+1}: {line.strip()}")

if __name__ == "__main__":
    inspect_msg_convergence()
