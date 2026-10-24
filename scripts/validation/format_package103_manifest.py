#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
format_package103_manifest.py
Builds M1_C5_PACKAGE103_H1_PILOT_AUTHORIZATION.json with verified file hashes.
"""

import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/103_c5_h1_transfer_pilot"

files_to_hash = [
    "M1_C5_PACKAGE103_H1_PILOT.inp",
    "M1_C5_PACKAGE103_H1_PILOT_DC.dat",
    "PACKAGE_MANIFEST.json",
    "candidate_c5_h1_state_table.csv",
    "candidate_crack_band_mesh_c5.inp",
    "extract_pkg103_results.py",
    "f42_mixed_uel.for",
    "job_notifications.sh",
    "run_pkg103_datacheck.sh",
    "submit_M1_C5_PACKAGE103_H1_PILOT.pbs"
]

file_hashes = {}
for fname in files_to_hash:
    fpath = pkg_dir / fname
    assert fpath.exists(), f"Missing file: {fpath}"
    with open(fpath, "rb") as f:
        file_hashes[fname] = hashlib.sha256(f.read()).hexdigest().lower()

remote_cmd = "powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_package103_c5_h1_pilot/submit_M1_C5_PACKAGE103_H1_PILOT.pbs\""
cmd_sha256 = hashlib.sha256(remote_cmd.encode("utf-8")).hexdigest().lower()

auth_data = {
    "batch_name": "MODE1_PACKAGE_103_C5_H1_PILOT",
    "adapter": "mode1-pdas-iterative-v1",
    "scientific_scope": "MODE1",
    "technical_stage": "MODE1_BASELINE",
    "configuration": "MODE1_BASELINE",
    "max_submissions": 1,
    "hours_valid": 24,
    "automatic_retry": False,
    "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_package103_c5_h1_pilot",
    "files": file_hashes,
    "jobs": [
        {
            "id": "M1_C5_PACKAGE103_H1_PILOT",
            "pbs": "submit_M1_C5_PACKAGE103_H1_PILOT.pbs",
            "command": remote_cmd,
            "command_sha256": cmd_sha256,
            "max_submissions": 1,
            "depends_on": [],
            "purpose": "Package 103: Mode-I Method C Stage C1-2 First Conforming Matched-Displacement Pilot under Exact Bound-Constrained H^1 State Transfer on C5 crack-band mesh solving for mechanical equilibrium and AT2 fracture energy at matched displacement u=0.002052 mm without artificial loading, verifying 100% Gauss-point history preservation, zero healing, zero overshoot, and physical force and fracture-energy continuity.",
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "queue": "entry_imfdfkmq",
            "execution": "single-rank serial",
            "input": "M1_C5_PACKAGE103_H1_PILOT.inp",
            "datacheck": "M1_C5_PACKAGE103_H1_PILOT_DC.dat"
        }
    ],
    "acceptance": {
        "M1_C5_PACKAGE103_H1_PILOT": "Mechanical equilibrium and authentic phase state achieved at matched displacement u=0.002052 mm; reaction force continuity within 5% of authentic Package 94 donor RF2 (112.97 N); Bourdin AT2 fracture energy continuity within 2% of donor (0.137737 mJ); strictly 0 healing nodes (min Delta d >= 0) and 0 overshoot nodes (max d <= 1.0); strictly monotonic committed Gauss-point history H preserved without reset; 100% bitwise frozen UEL hash CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6 preserved."
    }
}

out_path = pkg_dir / "M1_C5_PACKAGE103_H1_PILOT_AUTHORIZATION.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(auth_data, f, indent=2)

print(f"Generated authorization manifest: {out_path}")
print(f"  Command SHA256: {cmd_sha256}")
print(f"  Files hashed: {len(file_hashes)}")
