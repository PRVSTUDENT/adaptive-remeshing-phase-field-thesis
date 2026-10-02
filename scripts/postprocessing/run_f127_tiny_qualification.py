#!/usr/bin/env python3
"""
F127QUAL Tiny Non-Production Qualification Script for Transactional UEL
Task ID: F127QUAL-M2-CORRECTED-UEL-TRANSACTIONAL-STATE-AND-BASELINE-DEFINITION1
"""

import sys
import os
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

FORTRAN_PATH = ROOT / "models/generated/mode_ii/production_control_batch/f42_mixed_uel_transactional.for"

TINY_INP = """*HEADING
Tiny 4-Element Non-Production Qualification Deck for Transactional UEL
*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=6, VARIABLES=16, UNSYMM
3
*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=6, VARIABLES=16, UNSYMM
1, 2
*NODE
1, 0.0, 0.0
2, 1.0, 0.0
3, 2.0, 0.0
4, 0.0, 1.0
5, 1.0, 1.0
6, 2.0, 1.0
7, 0.0, 2.0
8, 1.0, 2.0
9, 2.0, 2.0
*ELEMENT, TYPE=U1, ELSET=E_PHASE
1, 1, 2, 5, 4
2, 2, 3, 6, 5
3, 4, 5, 8, 7
4, 5, 6, 9, 8
*ELEMENT, TYPE=U2, ELSET=E_MECH
5, 1, 2, 5, 4
6, 2, 3, 6, 5
7, 4, 5, 8, 7
8, 5, 6, 9, 8
*UEL PROPERTY, ELSET=E_PHASE
0.015, 0.0027, 210.0, 0.3, 1.0e-7, 4.0
*UEL PROPERTY, ELSET=E_MECH
0.015, 0.0027, 210.0, 0.3, 1.0e-7, 4.0
*NSET, NSET=N_BOTTOM
1, 2, 3
*NSET, NSET=N_TOP
7, 8, 9
*STEP, NAME=Step-1, INC=100
*STATIC
0.1, 1.0, 1.0e-5, 0.5
*BOUNDARY
N_BOTTOM, 1, 2, 0.0
N_TOP, 2, 2, 0.01
N_TOP, 1, 1, 0.005
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT
U, RF
*END STEP
"""

def main():
    print("================================================================================")
    print("EXECUTING F127QUAL TINY NON-PRODUCTION QUALIFICATION")
    print("================================================================================")

    # 1. Compute SHA256 of Fortran source
    content = FORTRAN_PATH.read_text(encoding="utf-8", errors="ignore")
    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    print(f"Transactional UEL Candidate SHA256: {sha256}")

    # 2. Build local tiny package dir
    pkg_dir = ROOT / "models/generated/mode_ii/production_control_batch/QUAL_TINY_4ELEM"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    
    (pkg_dir / "f42_mixed_uel_transactional.for").write_text(content, encoding="utf-8")
    (pkg_dir / "QUAL_TINY_4ELEM.inp").write_text(TINY_INP, encoding="utf-8")

    # 3. Sync to cluster
    remote_pkg_dir = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/QUAL_TINY_4ELEM"
    sync_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"mkdir -p {remote_pkg_dir}"]
    subprocess.run(sync_cmd, check=True)
    
    scp_cmd1 = ["scp", "-i", SSH_KEY, str(pkg_dir / "f42_mixed_uel_transactional.for"), f"{SSH_HOST}:{remote_pkg_dir}/"]
    scp_cmd2 = ["scp", "-i", SSH_KEY, str(pkg_dir / "QUAL_TINY_4ELEM.inp"), f"{SSH_HOST}:{remote_pkg_dir}/"]
    subprocess.run(scp_cmd1, check=True)
    subprocess.run(scp_cmd2, check=True)

    # 4. Run Abaqus Datacheck and Execution on Cluster
    run_abq_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"export PATH=/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin:/cluster/application/abaqus/2023/Commands:$PATH; source /etc/profile.d/lmod.sh 2>/dev/null || true; module load gcc/11.4.0 intel/2024.2.0 abaqus/2023; cd {remote_pkg_dir} && /cluster/application/abaqus/2023/Commands/abaqus job=QUAL_TINY_4ELEM input=QUAL_TINY_4ELEM.inp user=f42_mixed_uel_transactional.for interactive 2>&1"
    ]
    
    print("\nExecuting Abaqus 2023 Tiny Non-Production Qualification Run...")
    res = subprocess.run(run_abq_cmd, capture_output=True, text=True, timeout=300)
    print("Abaqus Stdout Output:\n", res.stdout)

    compile_pass = "End Compiling Abaqus/Standard User Subroutines" in res.stdout
    datacheck_pass = "ANALYSIS DATACHECK COMPLETE" in res.stdout or "Abaqus JOB QUAL_TINY_4ELEM COMPLETED" in res.stdout
    execution_pass = "Abaqus JOB QUAL_TINY_4ELEM COMPLETED" in res.stdout

    out = {
        "candidate_sha256": sha256,
        "compile_result": "PASS" if compile_pass else "FAIL",
        "datacheck_result": "PASS" if datacheck_pass else "FAIL",
        "tiny_execution_result": "PASS" if execution_pass else "FAIL"
    }
    print("\nQualification Summary:")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
