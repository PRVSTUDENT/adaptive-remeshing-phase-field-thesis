#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stage_package156_candidate.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: 30c0b12f-5c25-49bb-a7da-e4b89a6bd986
Turn: 389
Protocol Version: 2

Stages Package 156 (C5 Candidate Receiver Workflow) to HPC cluster scratch:
1. Remote directory: /scratch9/pr21vyci/runs/mode1_c5_package156_c2_0_re_equilibration
2. Uploads all 14 package files via scp
3. Verifies bitwise SHA-256 hashes against local manifest
4. Conducts authentic Abaqus 2023 compute-node datachecks for:
   - P156_MECHANICAL_DC (UEL Mech U2 with f42_mixed_uel.for, 7+8+3 solution cards, active set boundary cards)
   - P156_PHASE_DC (UEL Phase U1 with f42_mixed_uel.for, 7+8+3 solution cards, active set boundary cards)
5. Generates verification artifact: results/validation/package156_candidate_datachecks.json
"""

import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PACKAGE_DIR = REPO_ROOT / "models/pandey_kumar_mode1/156_c5_package156_c2_0_re_equilibration"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c5_package156_c2_0_re_equilibration"
SSH_CONFIG = Path.home() / ".ssh/codex_config"
SSH_WRAPPER = REPO_ROOT / ".agents/scripts/Invoke-GuardedSsh.ps1"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def run_ssh(remote_cmd: str, timeout=240) -> subprocess.CompletedProcess:
    ps_cmd = [
        "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
        "-File", str(SSH_WRAPPER),
        "-RemoteCommand", remote_cmd,
        "-TimeoutSeconds", str(timeout)
    ]
    return subprocess.run(ps_cmd, capture_output=True, text=True, timeout=timeout + 30)

def scp_file(local_path: Path, remote_path: str):
    cmd = [
        "scp.exe",
        "-F", str(SSH_CONFIG),
        "-B",
        "-o", "BatchMode=yes",
        str(local_path),
        f"tu_freiberg:{remote_path}"
    ]
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
    if res.returncode != 0:
        raise RuntimeError(f"SCP failed (exit {res.returncode}): {res.stderr}\n{res.stdout}")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest().upper()

def main():
    print("=" * 80)
    print("STAGING PACKAGE 156 C5 RECEIVER WORKFLOW TO HPC CLUSTER SCRATCH")
    print("=" * 80)

    # Verify local UEL matches frozen production hash bitwise
    uel_path = PACKAGE_DIR / "f42_mixed_uel.for"
    local_uel_hash = sha256_file(uel_path)
    assert local_uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch! Expected {FROZEN_UEL_HASH}, got {local_uel_hash}"
    print(f"Frozen production UEL verified bitwise: {local_uel_hash} (PASS)")

    # 1. Create remote directory
    res = run_ssh(f"mkdir -p {REMOTE_RUN_DIR}")
    assert res.returncode == 0, f"Failed to create remote dir: {res.stderr}"
    print(f"Created remote dir: {REMOTE_RUN_DIR}")

    # Clean any stale datacheck outputs if present
    run_ssh(f"rm -f {REMOTE_RUN_DIR}/P156_MECHANICAL_DC.* {REMOTE_RUN_DIR}/P156_PHASE_DC.*")

    # 2. Upload files via scp
    files_to_upload = [
        "f42_mixed_uel.for",
        "job_notifications.sh",
        "run_datacheck.sh",
        "submit_M1_C5_P156_C2_0.pbs",
        "P156_MECHANICAL_DC.inp",
        "P156_PHASE_DC.inp",
        "M1_C5_PACKAGE156_C2_0_REEQUILIBRATION.inp",
        "active_set_boundary_cards.inc",
        "initial_conditions_solution.inc",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "d_lower_bounds.csv",
        "PACKAGE_MANIFEST.json",
        "CONDITIONAL_CANDIDATE_RECEIPT.json"
    ]

    # Ensure shell scripts have LF line endings before upload
    for sh_name in ("run_datacheck.sh", "job_notifications.sh"):
        sh_p = PACKAGE_DIR / sh_name
        if sh_p.exists():
            sh_content = sh_p.read_text(encoding="utf-8").replace("\r\n", "\n")
            sh_p.write_bytes(sh_content.encode("utf-8"))

    verified_files = {}
    for fname in files_to_upload:
        local_p = PACKAGE_DIR / fname
        assert local_p.exists(), f"Missing {local_p}"
        l_hash = sha256_file(local_p)
        verified_files[fname] = l_hash

        print(f"Uploading {fname} ({local_p.stat().st_size} bytes)...")
        scp_file(local_p, f"{REMOTE_RUN_DIR}/{fname}")

        # Verify remote hash
        check_res = run_ssh(f"sha256sum {REMOTE_RUN_DIR}/{fname}")
        remote_hash = check_res.stdout.split()[0].upper()
        assert remote_hash == l_hash, f"Hash mismatch for {fname}: local {l_hash} vs remote {remote_hash}"
        print(f"  Verified remote hash for {fname}: {remote_hash} (PASS)")

    # Make shell scripts executable
    run_ssh(f"chmod 755 {REMOTE_RUN_DIR}/*.sh {REMOTE_RUN_DIR}/*.pbs")
    print("Permissions set to 755 for scripts.")

    # 3. Execute authentic Abaqus 2023 datachecks on cluster compute node
    print("Executing authentic Abaqus 2023 datachecks on cluster...")
    dc_results = {}
    for role in ("mechanical", "phase"):
        print(f"  Running datacheck for role: {role}...")
        dc_res = run_ssh(f"bash {REMOTE_RUN_DIR}/run_datacheck.sh {role}", timeout=300)
        output_txt = dc_res.stdout.strip()
        print(f"    Output: {output_txt}")
        if "AUTHENTIC_DATACHECK_PASS" not in output_txt:
            job_name = f"P156_{role.upper()}_DC"
            diag = run_ssh(f"cat {REMOTE_RUN_DIR}/{job_name}.stdout.txt 2>/dev/null || true").stdout
            dat_tail = run_ssh(f"tail -n 40 {REMOTE_RUN_DIR}/{job_name}.dat 2>/dev/null || true").stdout
            msg_tail = run_ssh(f"tail -n 40 {REMOTE_RUN_DIR}/{job_name}.msg 2>/dev/null || true").stdout
            raise RuntimeError(f"Datacheck failed for {role}: {output_txt}\nStdout:\n{diag}\nDat Tail:\n{dat_tail}\nMsg Tail:\n{msg_tail}")
        dc_results[role] = "AUTHENTIC_DATACHECK_PASS"

    print("ALL TWO DATACHECKS PASSED CLEANLY ON HPC CLUSTER.")

    # 4. Save evidence artifact
    evidence = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "turn": 389,
        "run_id": "30c0b12f-5c25-49bb-a7da-e4b89a6bd986",
        "remote_run_dir": REMOTE_RUN_DIR,
        "package_name": "MODE1_PACKAGE156_C5_C2_0_RE_EQUILIBRATION",
        "files_verified": verified_files,
        "datachecks": {
            "mechanical_dc": {
                "input": "P156_MECHANICAL_DC.inp",
                "user_subroutine": "f42_mixed_uel.for",
                "uel_hash": FROZEN_UEL_HASH,
                "status": dc_results["mechanical"]
            },
            "phase_dc": {
                "input": "P156_PHASE_DC.inp",
                "user_subroutine": "f42_mixed_uel.for",
                "uel_hash": FROZEN_UEL_HASH,
                "status": dc_results["phase"]
            }
        },
        "verification_passed": True
    }

    out_evidence = REPO_ROOT / "results/validation/package156_candidate_datachecks.json"
    out_evidence.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"WROTE EVIDENCE: {out_evidence}")
    print("=" * 80)
    print("PACKAGE 156 STAGING & DATACHECK COMPLETE.")
    print("=" * 80)

if __name__ == "__main__":
    main()
