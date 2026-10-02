#!/usr/bin/env python3
import sys

def check_dat():
    dat_path = "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.dat"
    with open(dat_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    errors = [l.strip() for l in lines if "***ERROR" in l]
    fatals = [l.strip() for l in lines if "FATAL" in l]
    warnings = [l.strip() for l in lines if "***WARNING" in l]
    
    print(f"syntaxcheck_ERROR_count = {len(errors)}")
    print(f"syntaxcheck_FATAL_count = {len(fatals)}")
    print(f"syntaxcheck_WARNING_count = {len(warnings)}")
    
    for e in errors:
        print("ERROR:", e)
    for f in fatals:
        print("FATAL:", f)
    for w in warnings[:5]:
        print("WARNING:", w)

if __name__ == "__main__":
    check_dat()
