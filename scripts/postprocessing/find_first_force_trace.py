#!/usr/bin/env python3
import sys, os

def find_first_force_trace():
    msg_path = "M2STATE_FRACFIX_RESTART2R4.msg"
    if not os.path.exists(msg_path):
        msg_path = "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R4/M2STATE_FRACFIX_RESTART2R4.msg"
    with open(msg_path, "r", errors="ignore") as f:
        count = 0
        for line in f:
            if "[FORCE_TRACE]" in line:
                print(line.strip())
                count += 1
                if count >= 30:
                    break

if __name__ == "__main__":
    find_first_force_trace()
