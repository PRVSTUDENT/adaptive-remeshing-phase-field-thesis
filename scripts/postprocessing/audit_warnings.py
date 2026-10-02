#!/usr/bin/env python3
from pathlib import Path

def audit_warnings():
    for fpath in [Path("/home/pr21vyci/test_r2r5_step1.msg"), Path("/home/pr21vyci/test_r2r5_step1.dat")]:
        print(f"=== {fpath.name} ===")
        with open(fpath, "r", errors="ignore") as f:
            for idx, line in enumerate(f):
                if any(w in line.lower() for w in ["warning", "error", "negative", "pivot", "singular", "zero pivot"]):
                    if not "[h_startup_trace]" in line.lower() and not "[force_trace]" in line.lower():
                        print(f"Line {idx+1}: {line.strip()}")

if __name__ == "__main__":
    audit_warnings()
