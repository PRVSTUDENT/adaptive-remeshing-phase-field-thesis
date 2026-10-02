#!/usr/bin/env python3
"""
Forensic audit of UEL call sequence, Step 1 equilibrium, and ODB states for Job 1389224.
"""
from pathlib import Path
import re

def audit_chronology():
    root = Path(__file__).resolve().parent.parent.parent
    base_dir = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5"
    msg_path = base_dir / "M2STATE_FRACFIX_RESTART2R5.msg"
    dat_path = base_dir / "M2STATE_FRACFIX_RESTART2R5.dat"
    sta_path = base_dir / "M2STATE_FRACFIX_RESTART2R5.sta"
    log_path = base_dir / "M2STATE_FRACFIX_RESTART2R5.o$PBS_JOBID"
    
    print("=== 1. CHRONOLOGICAL LOG AUDIT ===")
    h_traces = []
    state_traces = []
    force_traces = []
    nan_traces = []
    
    with open(log_path, "r", errors="ignore") as f:
        line_idx = 0
        for line in f:
            line_idx += 1
            if "[H_STARTUP_TRACE]" in line:
                h_traces.append((line_idx, line.strip()))
            elif "[STATE_TRACE]" in line:
                state_traces.append((line_idx, line.strip()))
                if "NaN" in line or "nan" in line:
                    nan_traces.append((line_idx, line.strip()))
            elif "[FORCE_TRACE]" in line:
                if len(force_traces) < 5 or "NaN" in line or "nan" in line:
                    force_traces.append((line_idx, line.strip()))
                if ("NaN" in line or "nan" in line) and len(nan_traces) < 20:
                    nan_traces.append((line_idx, line.strip()))

    print(f"Total H_STARTUP_TRACE lines: {len(h_traces)}")
    if h_traces:
        print(f"  First H trace (line {h_traces[0][0]}): {h_traces[0][1]}")
        print(f"  Last H trace (line {h_traces[-1][0]}): {h_traces[-1][1]}")
        
    print(f"Total STATE_TRACE lines: {len(state_traces)}")
    if state_traces:
        print(f"  First STATE trace (line {state_traces[0][0]}): {state_traces[0][1]}")
        
    print(f"First 10 non-finite trace occurrences:")
    for lidx, text in nan_traces[:10]:
        print(f"  Line {lidx}: {text}")

if __name__ == "__main__":
    audit_chronology()
