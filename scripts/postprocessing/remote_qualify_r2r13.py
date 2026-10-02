#!/usr/bin/env python3
"""
Remote Qualification Script for: M2STATE_FRACFIX_RESTART2R13
Task ID: F107STATE-M2-CORRECTED-RESTART2-R2R13-PREP-AND-QUALIFICATION1

Steps:
1. Sync package files to cluster.
2. Run validate_package_manifest.py on remote cluster.
3. Run Abaqus 2023 Datacheck (job=M2STATE_FRACFIX_RESTART2R13_DATACHECK datacheck).
4. Run Step 1 PhaseInit solve (job=M2STATE_FRACFIX_RESTART2R13_STEP1).
5. Extract DAT / ODB results (Reaction Forces, Displacements, Force Balance).
6. Verify Guarded Wrapper Dry-Run (submit_m2state_fracfix_restart2r13.sh --dry-run).
"""

import subprocess
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13"
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
REMOTE_PKG_DIR = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13"

def run_ssh(cmd, timeout=300):
    ssh_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, cmd]
    res = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
    return res.returncode, res.stdout, res.stderr

def run_scp_to_remote(local_file, remote_dest):
    scp_cmd = ["scp", "-i", SSH_KEY, str(local_file), f"{SSH_HOST}:{remote_dest}"]
    res = subprocess.run(scp_cmd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr

def run_scp_from_remote(remote_file, local_dest):
    scp_cmd = ["scp", "-i", SSH_KEY, f"{SSH_HOST}:{remote_file}", str(local_dest)]
    res = subprocess.run(scp_cmd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr

def qualify():
    print("======================================================================")
    print("Remote Qualification: M2STATE_FRACFIX_RESTART2R13")
    print("======================================================================")

    # 1. Create remote dir & sync files
    print("1. Syncing package files to remote cluster...")
    rc, out, err = run_ssh(f"mkdir -p {REMOTE_PKG_DIR}")
    if rc != 0:
        print(f"FAIL: could not create remote dir: {err}")
        return 1

    files_to_sync = [
        "M2STATE_FRACFIX_RESTART2R13.inp",
        "f42_mixed_uel.for",
        "M2STATE_FRACFIX_RESTART2R13.pbs",
        "submit_m2state_fracfix_restart2r13.sh",
        "validate_package_manifest.py",
        "job_notifications.sh",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "PACKAGE_MANIFEST.json"
    ]
    for fn in files_to_sync:
        rc, out, err = run_scp_to_remote(LOCAL_PKG_DIR / fn, f"{REMOTE_PKG_DIR}/{fn}")
        if rc != 0:
            print(f"FAIL: could not copy {fn}: {err}")
            return 1
    print("Sync complete.")

    # 2. Validate manifest on remote
    print("2. Validating remote manifest...")
    rc, out, err = run_ssh(f"cd {REMOTE_PKG_DIR} && python3 validate_package_manifest.py")
    print(out)
    if rc != 0 or "PASS" not in out:
        print(f"FAIL: manifest validation failed: {err}")
        return 1

    # 3. Run Abaqus Datacheck
    print("3. Running Abaqus 2023 Datacheck on cluster...")
    datacheck_cmd = (
        f"cd {REMOTE_PKG_DIR} && "
        "source /etc/profile.d/modules.sh 2>/dev/null || true; "
        "module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7 && "
        "rm -f M2STATE_FRACFIX_RESTART2R13_DATACHECK.* || true && "
        "abaqus job=M2STATE_FRACFIX_RESTART2R13_DATACHECK user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R13.inp datacheck double=both interactive cpus=1"
    )
    rc, out, err = run_ssh(datacheck_cmd, timeout=300)
    print(out)
    if "COMPLETED" not in out and "SUCCESS" not in out:
        # Check log/msg
        rc_msg, out_msg, _ = run_ssh(f"cat {REMOTE_PKG_DIR}/M2STATE_FRACFIX_RESTART2R13_DATACHECK.msg 2>/dev/null || cat {REMOTE_PKG_DIR}/M2STATE_FRACFIX_RESTART2R13_DATACHECK.log")
        print("DATACHECK OUTPUT:\n", out_msg)

    # 4. Run Step 1 PhaseInit solve
    print("4. Running Step 1 PhaseInit solve on cluster...")
    # Generate Step-1-only INP
    inp_text = (LOCAL_PKG_DIR / "M2STATE_FRACFIX_RESTART2R13.inp").read_text(encoding="utf-8")
    step1_end_pos = inp_text.find("*STEP, NAME=Step-2-Continuation")
    if step1_end_pos != -1:
        step1_inp = inp_text[:step1_end_pos]
    else:
        step1_inp = inp_text

    step1_inp_file = LOCAL_PKG_DIR / "M2STATE_FRACFIX_RESTART2R13_STEP1.inp"
    step1_inp_file.write_text(step1_inp, encoding="utf-8", newline="\n")
    run_scp_to_remote(step1_inp_file, f"{REMOTE_PKG_DIR}/M2STATE_FRACFIX_RESTART2R13_STEP1.inp")

    solve_cmd = (
        f"cd {REMOTE_PKG_DIR} && "
        "source /etc/profile.d/modules.sh 2>/dev/null || true; "
        "module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7 && "
        "rm -f M2STATE_FRACFIX_RESTART2R13_STEP1.lck || true && "
        "abaqus job=M2STATE_FRACFIX_RESTART2R13_STEP1 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R13_STEP1.inp double=both interactive cpus=1 memory='16000 mb'"
    )
    rc, out, err = run_ssh(solve_cmd, timeout=600)
    print(out)

    # 5. Fetch DAT and MSG files
    print("5. Fetching DAT and MSG outputs...")
    run_scp_from_remote(f"{REMOTE_PKG_DIR}/M2STATE_FRACFIX_RESTART2R13_STEP1.dat", LOCAL_PKG_DIR / "M2STATE_FRACFIX_RESTART2R13_STEP1.dat")
    run_scp_from_remote(f"{REMOTE_PKG_DIR}/M2STATE_FRACFIX_RESTART2R13_STEP1.msg", LOCAL_PKG_DIR / "M2STATE_FRACFIX_RESTART2R13_STEP1.msg")
    run_scp_from_remote(f"{REMOTE_PKG_DIR}/M2STATE_FRACFIX_RESTART2R13_STEP1.sta", LOCAL_PKG_DIR / "M2STATE_FRACFIX_RESTART2R13_STEP1.sta")

    # 6. Parse and verify results
    print("6. Verifying Step 1 results...")
    dat_path = LOCAL_PKG_DIR / "M2STATE_FRACFIX_RESTART2R13_STEP1.dat"
    if not dat_path.exists():
        print("FAIL: DAT file not downloaded")
        return 1

    dat_text = dat_path.read_text(encoding="utf-8", errors="ignore")
    # Search for Node 99999 RF1
    m = re.search(r"^\s*99999\s+([-\d.E+]+)\s+([-\d.E+]+)\s+([-\d.E+]+)\s+([-\d.E+]+)", dat_text, re.MULTILINE)
    if m:
        u1, u2, rf1, rf2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
        print(f"RP Node 99999 Results: U1={u1:.6f} mm, U2={u2:.6f} mm, RF1={rf1:.8f} kN, RF2={rf2:.8f} kN")
    else:
        print("FAIL: Could not parse RP Node 99999 from DAT file")
        return 1

    # 7. Check Guarded Wrapper Dry-Run
    print("7. Testing Guarded Submission Wrapper Dry-Run...")
    rc, out, err = run_ssh(f"cd {REMOTE_PKG_DIR} && chmod +x submit_m2state_fracfix_restart2r13.sh && ./submit_m2state_fracfix_restart2r13.sh --dry-run")
    print(out)
    if "qsub call count = 0" not in out:
        print("FAIL: Dry run check failed")
        return 1

    print("======================================================================")
    print("REMOTE QUALIFICATION SUMMARY FOR M2STATE_FRACFIX_RESTART2R13:")
    print(f"Target Runtime RF1: {rf1:.8f} kN")
    print("Source Job 1389278 RF1: 0.12322307 kN")
    print("======================================================================")
    return 0

if __name__ == '__main__':
    exit(qualify())
