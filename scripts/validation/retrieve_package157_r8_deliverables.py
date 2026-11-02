#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
retrieve_package157_r8_deliverables.py
Retrieves authentic terminal outputs for Package 157 Revision 8 (PBS Job 1419490.mmaster02)
from cluster scratch to local package directory.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r8"
EVIDENCE_DIR = PKG_DIR / "evidence/1419490.mmaster02"
SSH_CFG = Path.home() / ".ssh/codex_config"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c4_package157_c1_2_continuation_r8"
REMOTE_CONT_DIR = f"{REMOTE_RUN_DIR}/continuation_1419490.mmaster02"

files_to_fetch = [
    (f"{REMOTE_CONT_DIR}/runtime_report.json", "runtime_report.json"),
    (f"{REMOTE_CONT_DIR}/converged_checkpoint_01.json", "converged_checkpoint_01.json"),
    (f"{REMOTE_CONT_DIR}/live_iteration_telemetry.json", "live_iteration_telemetry.json"),
    (f"{REMOTE_RUN_DIR}/M1_C4_P157_C1_2_R8.pbs_execution.log", "pbs_execution.log"),
]

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Retrieving terminal deliverables for Package 157 R8 (Job 1419490.mmaster02) to {EVIDENCE_DIR}...")

    hashes = {}
    for remote_src, local_name in files_to_fetch:
        dst = EVIDENCE_DIR / local_name
        src = f"tu_freiberg:{remote_src}"
        cmd = ["scp", "-B", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", "-F", str(SSH_CFG), src, str(dst)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"SCP failed for {local_name}: {res.stderr}")
        size = dst.stat().st_size
        file_sha = sha256_file(dst)
        hashes[local_name] = {"size": size, "sha256": file_sha}
        print(f"  Fetched: {local_name} ({size} bytes, SHA-256: {file_sha[:16]}...)")

    # Fetch qstat accounting
    res = subprocess.run([
        "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
        str(REPO_ROOT / ".agents/scripts/Invoke-GuardedSsh.ps1"),
        "-RemoteCommand", "qstat -fx 1419490.mmaster02"
    ], capture_output=True, text=True)
    if res.returncode == 0:
        qstat_file = EVIDENCE_DIR / "qstat_accounting.txt"
        qstat_file.write_text(res.stdout, encoding="utf-8")
        print(f"  Saved: qstat_accounting.txt ({qstat_file.stat().st_size} bytes)")

    manifest_path = EVIDENCE_DIR / "retrieval_manifest.json"
    manifest = {
        "job_id": "1419490.mmaster02",
        "task_id": "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE",
        "package": "157_c4_package157_c1_2_continuation_r8",
        "files": hashes
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Retrieval complete. Manifest written to {manifest_path}")

if __name__ == "__main__":
    main()
