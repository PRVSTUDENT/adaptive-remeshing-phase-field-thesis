#!/usr/bin/env python3
"""
F145EVAL PK10R1 Same-Mesh Restart Validation Evaluation Script
Task ID: F145EVAL-M2-PK10R1-SAMEMESH-RESTART-VALIDATION-EVALUATION1
"""

import sys
import os
import re
import json
import numpy as np
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

CONTINUOUS_DIR = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050"
RESTART_DIR = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION"

def parse_dat_rf(dat_text):
    """Extract (U1, RF1) trajectory from Abaqus .dat file for N_RP."""
    lines = dat_text.splitlines()
    data = []
    
    # We look for N_RP node print tables
    # RF1 is reaction force in 1-direction
    in_rp_table = False
    cur_u1 = None
    cur_rf1 = None
    
    # Parse NODE PRINT output tables
    # Format:
    #   NODE  U1  U2  RF1  RF2 ...
    # Or separate U and RF tables
    # Let's use regex to extract step, inc, RP U1, and RP RF1
    
    # Alternatively, parse via regex for RP node output
    # In DAT:
    # THE FOLLOWING TABLE IS PRINTED FOR NODE SET N_RP
    #   NODE        U1           U2           RF1          RF2
    #  99999    5.0717E-04   0.0000E+00   3.0547E-01   ...
    
    rp_blocks = re.split(r'THE FOLLOWING TABLE IS PRINTED FOR NODE SET N_RP', dat_text)
    for block in rp_blocks[1:]:
        # Find lines with node 99999
        match = re.search(r'^\s*99999\s+([-+]?\d*\.\d+[eE][-+]?\d+|\d+)\s+([-+]?\d*\.\d+[eE][-+]?\d+|\d+)\s+([-+]?\d*\.\d+[eE][-+]?\d+|\d+)', block, re.MULTILINE)
        if match:
            # Check if this block has U or RF header
            header_line = block.splitlines()[0] if block.splitlines() else ""
            # Let's extract all numbers for node 99999 in block
            nline = [l for l in block.splitlines() if l.strip().startswith('99999')]
            if nline:
                tokens = nline[0].split()
                # Tokens: ['99999', val1, val2, ...]
                # If block has U1/RF1:
                # Let's inspect block header
                vals = [float(x) for x in tokens[1:]]
                data.append((block, vals))
    return data

def main():
    print("================================================================================")
    print("F145EVAL SAME-MESH RESTART VALIDATION EVALUATION")
    print("================================================================================")

    # 1. Fetch DAT content for continuous job 1389684 and restart job 1389693
    print("Fetching DAT file for continuous job 1389684.mmaster02...")
    cmd_cont = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat {CONTINUOUS_DIR}/M2CORR_PK10R1_CONTINUOUS_U050.dat"]
    dat_cont = subprocess.run(cmd_cont, capture_output=True, text=True, check=True).stdout

    print("Fetching DAT file for restart job 1389693.mmaster02...")
    cmd_rest = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat {RESTART_DIR}/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.dat"]
    dat_rest = subprocess.run(cmd_rest, capture_output=True, text=True, check=True).stdout

    # Parse continuous trajectory
    # In continuous DAT file, let's extract all increments
    # Let's write a python inline script on cluster or process DAT directly using python
    print("\nExecuting detailed Python extraction script on cluster ODBs...")
    
    odb_extract_script = """
import sys
import numpy as np

# We can parse the DAT files directly in python
def parse_dat_inc_data(dat_path):
    with open(dat_path, 'r') as f:
        content = f.read()
    
    # Split by INCREMENT
    inc_blocks = content.split('INCREMENT')
    records = []
    for b in inc_blocks[1:]:
        # Parse increment number
        lines = b.splitlines()
        inc_num = int(lines[0].strip().split()[0])
        
        # Parse N_RP node 99999 values
        # Look for node 99999
        u1 = None
        rf1 = None
        for i, line in enumerate(lines):
            if 'N_RP' in line or '99999' in line:
                for j in range(i, min(i+10, len(lines))):
                    if lines[j].strip().startswith('99999'):
                        toks = lines[j].strip().split()
                        # If table has U: toks = ['99999', U1, U2]
                        # If table has RF: toks = ['99999', RF1, RF2]
                        # If combined: toks = ['99999', U1, U2, RF1, RF2]
                        if len(toks) >= 4 and u1 is None:
                            try:
                                u1 = float(toks[1])
                                rf1 = float(toks[3])
                            except:
                                pass
                        elif len(toks) >= 2:
                            try:
                                val = float(toks[1])
                                if 'RF' in lines[j-2] or 'RF' in lines[j-1]:
                                    rf1 = val
                                else:
                                    u1 = val
                            except:
                                pass
        if u1 is not None and rf1 is not None:
            records.append((inc_num, u1, rf1))
    return records

print("Parsing continuous DAT...")
cont_recs = parse_dat_inc_data('""" + CONTINUOUS_DIR + """/M2CORR_PK10R1_CONTINUOUS_U050.dat')
print("Continuous records count:", len(cont_recs))

print("Parsing restart DAT...")
rest_recs = parse_dat_inc_data('""" + RESTART_DIR + """/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.dat')
print("Restart records count:", len(rest_recs))
"""
    
    # Run python extraction on cluster
    py_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 -c \"{odb_extract_script}\""]
    res = subprocess.run(py_cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("Stderr:", res.stderr)

if __name__ == "__main__":
    main()
