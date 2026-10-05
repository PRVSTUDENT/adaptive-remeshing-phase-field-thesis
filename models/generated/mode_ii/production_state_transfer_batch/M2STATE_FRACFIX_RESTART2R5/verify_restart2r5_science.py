#!/usr/bin/env python3
import sys, re, glob
from pathlib import Path

def verify_science():
    out_files = glob.glob("M2STATE_FRACFIX_RESTART2R5.o*")
    msg_files = glob.glob("M2STATE_FRACFIX_RESTART2R5.msg")
    
    files_to_check = out_files + msg_files
    if not files_to_check:
        print("No log files found to verify.")
        sys.exit(1)
        
    nan_count = 0
    trace_count = 0
    for fpath in files_to_check:
        with open(fpath, "r", errors="ignore") as f:
            for line in f:
                if "[FORCE_TRACE]" in line or "[STATE_TRACE]" in line or "[H_STARTUP_TRACE]" in line:
                    trace_count += 1
                    if "NaN" in line or "nan" in line or "Infinity" in line or "inf" in line:
                        nan_count += 1
                        print(f"ERROR: Non-finite trace line in {fpath}: {line.strip()}")
                        
    print(f"Total evaluated trace lines: {trace_count}")
    if nan_count > 0:
        print(f"Scientific verification result: FAIL (Non-finite trace count: {nan_count})")
        sys.exit(1)
    else:
        print("Scientific verification result: PASS (All trace lines strictly finite)")

if __name__ == '__main__':
    verify_science()
