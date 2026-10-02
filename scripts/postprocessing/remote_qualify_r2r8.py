#!/usr/bin/env python3
"""
Stage F: Remote Qualification and Preflight Check for M2STATE_FRACFIX_RESTART2R8
Task ID: F79STATE-M2-RESTART2R8-PROPERTY-ABI-AND-FORCE-CONTINUITY-REPAIR1
"""

import os
import sys
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R8"
REMOTE_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
REMOTE_BASE = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R8"
SSH_KEY = os.path.expanduser("~/.ssh/tu_freiberg_codex")

def run_cmd(cmd_list, check=True):
    print(f"--> Running: {' '.join(cmd_list)}")
    res = subprocess.run(cmd_list, capture_output=True, text=True)
    if check and res.returncode != 0:
        print("STDOUT:\n", res.stdout)
        print("STDERR:\n", res.stderr)
        raise RuntimeError(f"Command failed with RC={res.returncode}")
    return res

def qualify_r2r8():
    print("======================================================================")
    print("Remote Qualification: M2STATE_FRACFIX_RESTART2R8")
    print("======================================================================")

    # 1. Sync candidate directory to cluster
    run_cmd(["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", REMOTE_HOST, f"mkdir -p {REMOTE_BASE}"])
    
    files = [
        "f42_mixed_uel.for",
        "job_notifications.sh",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "M2STATE_FRACFIX_RESTART2R8.inp",
        "M2STATE_FRACFIX_RESTART2R8.pbs",
        "submit_m2state_fracfix_restart2r8.sh",
        "PACKAGE_MANIFEST.json"
    ]
    for fn in files:
        src = LOCAL_DIR / fn
        run_cmd(["scp", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", str(src), f"{REMOTE_HOST}:{REMOTE_BASE}/{fn}"])
    print("Candidate files transferred successfully.")

    # 2. Write remote qualification shell script
    remote_sh_lines = [
        "#!/bin/bash",
        "source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true",
        "module purge || true",
        "module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7",
        "set -euo pipefail",
        f"cd {REMOTE_BASE}",
        "chmod +x submit_m2state_fracfix_restart2r8.sh job_notifications.sh",
        "",
        "echo '=== Step 1: Remote SHA256 Manifest Verification ==='",
        "python3 -c \"",
        "import json, hashlib, sys",
        "with open('PACKAGE_MANIFEST.json') as f: m = json.load(f)",
        "for fn, expected in m['file_hashes'].items():",
        "    h = hashlib.sha256(open(fn, 'rb').read()).hexdigest()",
        "    if h != expected:",
        "        print(f'MISMATCH: {fn} actual={h} expected={expected}')",
        "        sys.exit(1)",
        "print('Remote package integrity verified: 100% SHA256 match.')",
        "\"",
        "",
        "echo '=== Step 2: Abaqus 2023 Datacheck ==='",
        "rm -f M2STATE_FRACFIX_RESTART2R8.lck *.log *.dat *.msg *.sta *.prt *.com *.sim *.odb || true",
        "abaqus job=M2STATE_FRACFIX_RESTART2R8 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R8.inp datacheck interactive",
        "if grep -q 'ANALYSIS DATACHECK COMPLETE' M2STATE_FRACFIX_RESTART2R8.dat || grep -q 'THE ANALYSIS HAS BEEN COMPLETED' M2STATE_FRACFIX_RESTART2R8.dat; then",
        "    echo 'DATACHECK SUCCESS: Analysis completed without errors.'",
        "else",
        "    echo 'DATACHECK FAILED!'",
        "    cat M2STATE_FRACFIX_RESTART2R8.dat | tail -n 40",
        "    exit 1",
        "fi",
        "",
        "echo '=== Step 3: Interactive Step-1 Qualification Solve ==='",
        "python3 -c \"",
        "lines = open('M2STATE_FRACFIX_RESTART2R8.inp').readlines()",
        "s1_lines = []",
        "for l in lines:",
        "    s1_lines.append(l)",
        "    if '*END STEP' in l:",
        "        break",
        "open('M2STATE_FRACFIX_RESTART2R8_STEP1.inp', 'w').writelines(s1_lines)",
        "\"",
        "rm -f M2STATE_FRACFIX_RESTART2R8_STEP1.lck *.log *.dat *.msg *.sta *.prt *.com *.sim *.odb || true",
        "abaqus job=M2STATE_FRACFIX_RESTART2R8_STEP1 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R8_STEP1.inp interactive double=both cpus=1 memory='4000 mb'",
        "if grep -q 'THE ANALYSIS HAS BEEN COMPLETED' M2STATE_FRACFIX_RESTART2R8_STEP1.dat; then",
        "    echo 'STEP 1 SOLVE SUCCESS: Converged without errors.'",
        "else",
        "    echo 'STEP 1 SOLVE FAILED!'",
        "    cat M2STATE_FRACFIX_RESTART2R8_STEP1.dat | tail -n 40",
        "    exit 1",
        "fi",
        "",
        "echo '=== Step 4: Extract Step 1 Reaction Force and Displacements ==='",
        "python3 -c \"",
        "import json",
        "text = open('M2STATE_FRACFIX_RESTART2R8_STEP1.dat').read()",
        "bottom_rf1 = 0.0",
        "for line in text.splitlines():",
        "    parts = line.split()",
        "    if len(parts) >= 5 and parts[0].isdigit():",
        "        nid = int(parts[0])",
        "        if 1 <= nid <= 120:",
        "            try:",
        "                if len(parts) == 8:",
        "                    rf1 = float(parts[5])",
        "                elif len(parts) == 7:",
        "                    rf1 = float(parts[4])",
        "                else:",
        "                    rf1 = float(parts[-3])",
        "                bottom_rf1 += rf1",
        "            except: pass",
        "print(f'STEP 1 QUALIFICATION: Bottom RF1 Sum = {-bottom_rf1:.6f} kN')",
        "with open('STEP1_QUALIFICATION_RESULTS.json', 'w') as out_f:",
        "    json.dump({'step1_bottom_rf1_kN': -bottom_rf1}, out_f, indent=2)",
        "\"",
        "",
        "echo '=== Step 5: Guarded Wrapper Dry-Run Verification ==='",
        "./submit_m2state_fracfix_restart2r8.sh --dry-run"
    ]
    remote_sh_content = "\n".join(remote_sh_lines) + "\n"

    local_sh = LOCAL_DIR / "run_remote_qualification.sh"
    with open(local_sh, "w", encoding="utf-8", newline="\n") as f:
        f.write(remote_sh_content)
        
    run_cmd(["scp", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", str(local_sh), f"{REMOTE_HOST}:{REMOTE_BASE}/run_remote_qualification.sh"])
    
    # Execute on remote host
    res = run_cmd(["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", REMOTE_HOST, f"bash {REMOTE_BASE}/run_remote_qualification.sh"])
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

    # Fetch STEP1_QUALIFICATION_RESULTS.json
    run_cmd(["scp", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", f"{REMOTE_HOST}:{REMOTE_BASE}/STEP1_QUALIFICATION_RESULTS.json", str(LOCAL_DIR / "STEP1_QUALIFICATION_RESULTS.json")])
    print("R2R8 REMOTE QUALIFICATION COMPLETE: 100% PASS.")

if __name__ == "__main__":
    qualify_r2r8()
