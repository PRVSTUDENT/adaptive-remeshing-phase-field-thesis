#!/usr/bin/env python3
"""
F125DIAG DAT & Manifest Reconstructive History Energy Consistency Auditor
Task ID: F125DIAG-M2-R2R13-TERMINAL-HISTORY-ENERGY-CONSISTENCY-AND-CALL-ORDER1
"""

import sys
import os
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

REMOTE_PARSER = """#!/usr/bin/env python3
import os
import re
import json
import math

BASE_STATE   = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch"
BASE_CONTROL = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch"

def parse_dat_nodes_and_sdvs(dat_path):
    if not os.path.exists(dat_path):
        return None, None
        
    nodes_u = {}
    elem_sdvs = {}
    
    current_step = 1
    current_inc = 0
    in_node_table = False
    in_el_table = False
    current_elset = None
    
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "STEP " in line and "INCREMENT" in line:
                m = re.search(r"STEP\s+(\d+)\s+INCREMENT\s+(\d+)", line)
                if m:
                    current_step = int(m.group(1))
                    current_inc = int(m.group(2))
            if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in line:
                in_node_table = True
                in_el_table = False
                continue
            if "THE FOLLOWING TABLE IS PRINTED AT THE INTEGRATION POINTS" in line:
                in_el_table = True
                in_node_table = False
                continue
            if in_node_table:
                if line.startswith("1") or "JOB TIME SUMMARY" in line or "ANALYSIS SUMMARY" in line or "STEP " in line or "THE FOLLOWING TABLE" in line:
                    in_node_table = False
                    continue
                tokens = line.strip().split()
                if len(tokens) >= 3 and tokens[0].isdigit():
                    try:
                        nid = int(tokens[0])
                        u1 = float(tokens[1])
                        u2 = float(tokens[2])
                        nodes_u[nid] = (u1, u2)
                    except Exception:
                        pass
            if in_el_table:
                if line.startswith("1") or "JOB TIME SUMMARY" in line or "ANALYSIS SUMMARY" in line or "STEP " in line or "THE FOLLOWING TABLE" in line:
                    in_el_table = False
                    continue
                tokens = line.strip().split()
                if len(tokens) >= 5 and tokens[0].isdigit() and tokens[1].isdigit():
                    try:
                        eid = int(tokens[0])
                        pt  = int(tokens[1])
                        sdv14 = float(tokens[2])
                        sdv15 = float(tokens[3])
                        sdv16 = float(tokens[4]) # History H
                        elem_sdvs[(eid, pt)] = (sdv14, sdv15, sdv16)
                    except Exception:
                        pass
                        
    return nodes_u, elem_sdvs

def main():
    r13_dat = os.path.join(BASE_STATE, "M2STATE_FRACFIX_RESTART2R13", "M2STATE_FRACFIX_RESTART2R13.dat")
    cont_dat = os.path.join(BASE_CONTROL, "PK10R1_CONTINUOUS_U050", "PK10R1_CONTINUOUS_U050.dat")
    
    r13_u, r13_sdv = parse_dat_nodes_and_sdvs(r13_dat)
    cont_u, cont_sdv = parse_dat_nodes_and_sdvs(cont_dat)
    
    output = {
        "r13_nodes_count": len(r13_u) if r13_u else 0,
        "r13_ips_count": len(r13_sdv) if r13_sdv else 0,
        "cont_nodes_count": len(cont_u) if cont_u else 0,
        "cont_ips_count": len(cont_sdv) if cont_sdv else 0,
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
"""

def main():
    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f125_parse_dat.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_PARSER}\nEOF"]
    subprocess.run(upload_cmd, check=True)

    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    print(res.stdout)

if __name__ == "__main__":
    main()
