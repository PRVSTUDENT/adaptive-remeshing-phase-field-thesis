#!/usr/bin/env python3
import sys, os

def parse_msg():
    msg_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R4/M2STATE_FRACFIX_RESTART2R4.msg"
    if not os.path.exists(msg_path):
        msg_path = "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R4/M2STATE_FRACFIX_RESTART2R4.msg"
    with open(msg_path, "r", errors="ignore") as f:
        for line in f:
            l_lower = line.lower()
            if any(k in l_lower for k in ["warning", "pivot", "singularity", "error", "zero pivot", "negative eigenvalue", "nan"]):
                print(line.strip())

if __name__ == "__main__":
    parse_msg()
