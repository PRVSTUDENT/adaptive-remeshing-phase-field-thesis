#!/usr/bin/env python3
"""
F127QUAL Mesh Topology & Physical Element Count Verification Script (Direct Card Counter)
Task ID: F127QUAL-M2-CORRECTED-UEL-TRANSACTIONAL-STATE-AND-BASELINE-DEFINITION1
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

REMOTE_SCRIPT = """#!/usr/bin/env python3
import os
import re
import json

BASE_VERIF = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch"
BASE_CTRL  = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch"

def count_elements(inp_path):
    if not os.path.exists(inp_path):
        return 0, 0
    
    physical_elements = set()
    total_elements = 0
    in_elem = False
    
    with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            l = line.strip()
            if l.upper().startswith("*ELEMENT"):
                in_elem = True
                continue
            if l.startswith("*"):
                in_elem = False
                continue
            if in_elem and l and l[0].isdigit():
                tokens = [t.strip() for t in l.split(",")]
                if tokens[0].isdigit():
                    eid = int(tokens[0])
                    total_elements += 1
                    # Physical element IDs are 1..N_PHYS or N_PHYS+1..2*N_PHYS
                    # In our format, UEL quad phase elements are 1..N_PHYS
                    physical_elements.add(eid)
                    
    # In our dual UEL layer (JTYPE=1 phase elements 1..N_PHYS, JTYPE=2 mechanical elements N_PHYS+1..2*N_PHYS):
    # Maximum element ID for UEL is 2*N_PHYS.
    max_eid = max(physical_elements) if physical_elements else 0
    n_phys = max_eid // 2 if max_eid % 2 == 0 else max_eid
    return total_elements, n_phys

def main():
    h1_inp = os.path.join(BASE_VERIF, "M2REF_H1_FULL_U050", "M2REF_H1_FULL_U050.inp")
    h2_inp = os.path.join(BASE_VERIF, "M2REF_H2_FULL_U050", "M2REF_H2_FULL_U050.inp")
    pk10_inp = os.path.join(BASE_CTRL, "PK10R1_CONTINUOUS_U050", "PK10R1_CONTINUOUS_U050.inp")
    
    _, h1_nphys = count_elements(h1_inp)
    _, h2_nphys = count_elements(h2_inp)
    _, pk10_nphys = count_elements(pk10_inp)
    
    out = {
        "H1_full_physical_element_count": h1_nphys,
        "H2_full_physical_element_count": h2_nphys,
        "PK10R1_physical_element_count": pk10_nphys,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
"""

def main():
    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f127_mesh_check.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)

    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    print(res.stdout)

if __name__ == "__main__":
    main()
