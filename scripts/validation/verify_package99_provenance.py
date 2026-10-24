#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_package99_provenance.py
Compares local SHA-256 hashes against remote cluster scratch hashes
for all Package 99 files using explicit absolute paths.
"""
import hashlib
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/99_c5_pdas_authentic_nodal_extraction_pilot"
rem_dir = "/scratch9/pr21vyci/runs/mode1_package99_c5_pdas_pilot"

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

files = [
    "candidate_c5_frame7_mapped_state_table.csv",
    "candidate_crack_band_mesh_c5.inp",
    "extract_pdas_subproblem_odb.py",
    "f42_mixed_uel.for",
    "job_notifications.sh",
    "M1_C5_PACKAGE99_SEED_TRANSFER.inp",
    "pdas_cluster_execution_adapter.py",
    "submit_M1_C5_PACKAGE99_PDAS_PILOT.pbs",
    "PACKAGE_MANIFEST.json"
]

local_hashes = {}
for f in files:
    local_hashes[f] = sha256_file(pkg_dir / f)

# Query remote hashes via guarded ssh with explicit absolute paths
remote_paths = [f"{rem_dir}/{f}" for f in files]
remote_cmd = "sha256sum " + " ".join(remote_paths)
cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "{remote_cmd}"'
res = subprocess.run(cmd, shell=True, capture_output=True, text=True)

remote_hashes = {}
for line in res.stdout.splitlines():
    line = line.strip()
    if not line or line.startswith("**") or line.startswith("Job"): continue
    parts = line.split()
    if len(parts) >= 2 and len(parts[0]) == 64:
        fname = Path(parts[1]).name
        remote_hashes[fname] = parts[0].upper()

print("=== PACKAGE 99 LOCAL VS REMOTE PROVENANCE AUDIT ===")
print(f"{'File':45s} | {'Local SHA256 (first 12)':14s} | {'Remote SHA256 (first 12)':14s} | {'Status'}")
print("-" * 85)
all_match = True
for f in files:
    loc = local_hashes.get(f, "MISSING")
    rem = remote_hashes.get(f, "MISSING")
    match = (loc == rem) and (loc != "MISSING")
    if not match: all_match = False
    print(f"{f:45s} | {loc[:12]:14s} | {rem[:12]:14s} | {'MATCH' if match else 'MISMATCH'}")

provenance_report = {
    "schema": 1,
    "status": "PACKAGE99_PROVENANCE_VERIFIED" if all_match else "PROVENANCE_MISMATCH",
    "package": "PACKAGE_99_C5_PDAS_AUTHENTIC_NODAL_EXTRACTION_PILOT",
    "remote_run_dir": rem_dir,
    "all_files_match": all_match,
    "files": {}
}

for f in files:
    provenance_report["files"][f] = {
        "local_sha256": local_hashes[f],
        "remote_sha256": remote_hashes.get(f, "MISSING"),
        "match": local_hashes[f] == remote_hashes.get(f, "")
    }

out_path = REPO_ROOT / "results/validation/mode1_f1597/package99_source_provenance_audit.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(provenance_report, f, indent=2)

print(f"\nSaved provenance report to {out_path}")
