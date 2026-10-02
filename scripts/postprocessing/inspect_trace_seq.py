#!/usr/bin/env python3
import sys, os

def inspect_trace():
    msg_path = "M2STATE_FRACFIX_RESTART2R4.msg"
    if not os.path.exists(msg_path):
        msg_path = "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R4/M2STATE_FRACFIX_RESTART2R4.msg"
    with open(msg_path, "r", errors="ignore") as f:
        traces = []
        for line in f:
            if "[H_STARTUP_TRACE]" in line or "[FORCE_TRACE]" in line or "[STATE_TRACE]" in line:
                traces.append(line.strip())
                if len(traces) >= 50:
                    break
        for t in traces:
            print(t)

if __name__ == "__main__":
    inspect_trace()
