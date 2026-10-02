#!/usr/bin/env python3
from pathlib import Path

def check_traces():
    root = Path(__file__).resolve().parent.parent.parent
    log_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.o$PBS_JOBID"
    
    state_traces = []
    force_traces = []
    
    with open(log_path, "r", errors="ignore") as f:
        for line in f:
            if "[STATE_TRACE]" in line:
                state_traces.append(line.rstrip())
                if len(state_traces) <= 10 or len(state_traces) % 1000 == 0:
                    print(f"STATE_TRACE: {line.strip()}")
            elif "[FORCE_TRACE]" in line:
                force_traces.append(line.rstrip())
                if len(force_traces) <= 10 or len(force_traces) % 1000 == 0:
                    print(f"FORCE_TRACE: {line.strip()}")
                    
    print(f"\nTotal STATE_TRACE lines: {len(state_traces)}")
    print(f"Total FORCE_TRACE lines: {len(force_traces)}")

if __name__ == "__main__":
    check_traces()
