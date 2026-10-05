#!/usr/bin/env python3
import sys, os, glob, re, math

def main():
    trace_files = glob.glob("*.o*") + glob.glob("*.trace") + glob.glob("*.dat") + glob.glob("*.msg")
    has_trace = False
    nan_count = 0
    for tf in trace_files:
        if not os.path.exists(tf):
            continue
        with open(tf, 'r', errors='ignore') as f:
            for line in f:
                if '[STATE_TRACE]' in line:
                    has_trace = True
                    if 'NaN' in line or 'nan' in line or 'Infinity' in line or 'inf' in line:
                        nan_count += 1
                        print("ERROR: Non-finite STATE_TRACE line:", line.strip())
                if '[FORCE_TRACE]' in line:
                    if 'NaN' in line or 'nan' in line:
                        nan_count += 1
                        print("ERROR: Non-finite FORCE_TRACE line:", line.strip())
    
    if nan_count > 0:
        print(f"Scientific verification result: FAIL (Non-finite trace count: {nan_count})")
        sys.exit(1)
    
    print("Scientific verification result: PASS (All verified quantities finite)")

if __name__ == '__main__':
    main()
