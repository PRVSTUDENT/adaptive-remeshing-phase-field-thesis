#!/usr/bin/env python3
from pathlib import Path

def parse_msg():
    root = Path(__file__).resolve().parent.parent.parent
    msg_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.msg"
    with open(msg_path, "r", errors="ignore") as f:
        for i in range(150):
            line = f.readline()
            if not line:
                break
            print(line.rstrip())

if __name__ == "__main__":
    parse_msg()
