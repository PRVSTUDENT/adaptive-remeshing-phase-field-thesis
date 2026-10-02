#!/usr/bin/env python3
"""
Salvage and Scientific Extraction Script for Job 1389325.mmaster02 (M2STATE_FRACFIX_RESTART2R13)
Task ID: F109STATE-M2-CORRECTED-RESTART2-R2R13-EVALUATION-AND-VALIDATION1
"""

import os
import sys
import json
import re
import subprocess
import hashlib
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_DIR = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389325.mmaster02"
LOCAL_PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13"
REMOTE_PKG_DIR = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13"
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

def run_ssh(cmd, timeout=300):
    ssh_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, cmd]
    res = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
    return res.returncode, res.stdout, res.stderr

def run_scp_from_remote(remote_file, local_dest):
    scp_cmd = ["scp", "-i", SSH_KEY, f"{SSH_HOST}:{remote_file}", str(local_dest)]
    res = subprocess.run(scp_cmd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def salvage():
    print("======================================================================")
    print("Salvaging Evidence for Job: 1389325.mmaster02 (M2STATE_FRACFIX_RESTART2R13)")
    print("======================================================================")
    
    if not EVIDENCE_DIR.exists():
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    files_to_download = [
        "M2STATE_FRACFIX_RESTART2R13.dat",
        "M2STATE_FRACFIX_RESTART2R13.msg",
        "M2STATE_FRACFIX_RESTART2R13.sta",
        "M2STATE_FRACFIX_RESTART2R13.prt",
        "M2STATE_FRACFIX_RESTART2R13.pbs.log",
        "M2STATE_FRACFIX_RESTART2R13.com",
        "M2STATE_FRACFIX_RESTART2R13.inp",
        "f42_mixed_uel.for",
        "PACKAGE_MANIFEST.json",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json"
    ]

    for fn in files_to_download:
        print(f"Downloading {fn}...")
        rc, out, err = run_scp_from_remote(f"{REMOTE_PKG_DIR}/{fn}", EVIDENCE_DIR / fn)
        if rc != 0:
            print(f"Warning: could not download {fn}: {err}")
        else:
            print(f"  {fn} saved ({sha256_file(EVIDENCE_DIR / fn)[:16]}...)")

    # Extract scientific results from DAT file
    dat_path = EVIDENCE_DIR / "M2STATE_FRACFIX_RESTART2R13.dat"
    dat_text = dat_path.read_text(encoding="utf-8", errors="ignore")

    # Parse RP 99999 trajectory across increments
    # Search for occurrences of node 99999 in dat
    rp_matches = re.findall(r"^\s*99999\s+([-\d.E+]+)\s+([-\d.E+]+)", dat_text, re.MULTILINE)
    print(f"\nFound {len(rp_matches)} RP Node 99999 output records in DAT.")
    
    trajectory = []
    for u1_str, rf1_str in rp_matches:
        try:
            u1 = float(u1_str)
            rf1 = float(rf1_str)
            trajectory.append((u1, rf1))
        except ValueError:
            pass

    print("\n--- RP NODE 99999 TRAJECTORY (u1 vs RF1) ---")
    print(f"{'Index':>5} {'U1 (mm)':>12} {'RF1 (kN)':>14} {'RF1 (N)':>12}")
    for idx, (u1, rf1) in enumerate(trajectory):
        print(f"{idx:>5d} {u1:>12.6f} {rf1:>14.8f} {rf1*1000:>12.3f}")

    # Step 1 Handoff point
    step1_u1, step1_rf1 = trajectory[0]
    
    # Peak Force in Step 2
    rf1_vals = [rf1 for u1, rf1 in trajectory]
    peak_rf1 = max(rf1_vals)
    peak_idx = rf1_vals.index(peak_rf1)
    peak_u1 = trajectory[peak_idx][0]
    terminal_u1, terminal_rf1 = trajectory[-1]

    print("\n--- SUMMARY OF KEY SCIENTIFIC METRICS ---")
    print(f"Step 1 Handoff:   U1 = {step1_u1:.6f} mm, RF1 = {step1_rf1:.8f} kN ({step1_rf1*1000:.3f} N)")
    print(f"Peak Force:       U1 = {peak_u1:.6f} mm, RF1 = {peak_rf1:.8f} kN ({peak_rf1*1000:.3f} N) at Inc {peak_idx}")
    print(f"Terminal State:   U1 = {terminal_u1:.6f} mm, RF1 = {terminal_rf1:.8f} kN ({terminal_rf1*1000:.3f} N)")
    
    # Save structured summary JSON
    summary = {
        "job_id": "1389325.mmaster02",
        "candidate": "M2STATE_FRACFIX_RESTART2R13",
        "source_job_id": "1389278.mmaster02",
        "total_increments": len(trajectory),
        "step1_handoff_u1_mm": step1_u1,
        "step1_handoff_rf1_kN": step1_rf1,
        "peak_u1_mm": peak_u1,
        "peak_rf1_kN": peak_rf1,
        "terminal_u1_mm": terminal_u1,
        "terminal_rf1_kN": terminal_rf1,
        "trajectory": [{"inc": i, "u1_mm": u, "rf1_kN": rf} for i, (u, rf) in enumerate(trajectory)],
        "evidence_sha256": {fn: sha256_file(EVIDENCE_DIR / fn) for fn in files_to_download if (EVIDENCE_DIR / fn).exists()}
    }

    (EVIDENCE_DIR / "JOB_1389325_SCIENTIFIC_SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\nSaved JOB_1389325_SCIENTIFIC_SUMMARY.json")

if __name__ == '__main__':
    salvage()
