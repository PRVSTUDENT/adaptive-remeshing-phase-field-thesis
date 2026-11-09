# -*- coding: utf-8 -*-
"""
scripts/hpc/create_f1708_pk_sec43_job2_adapted_authorization.py
==============================================================
Generates the Mode-I authorization manifest for Task F1708 Section 4.3 Job-2 Phase-Field
Fracture Simulation on the F1703 Native Adapted Mesh.
"""
import json
import hashlib
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
deck_dir = repo_root / "models" / "pandey_kumar_mode1" / "204_pk_sec43_job2_adapted"

def get_hash(filename):
    p = deck_dir / filename
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().lower()

inp_name = "PK_SEC43_JOB2_ADAPTED_PROD.inp"
uel_name = "f42_mixed_uel.for"
pbs_name = "submit_M1_PK_SEC43_JOB2_ADAPTED.pbs"
notif_name = "job_notifications.sh"
dc_name = "M1_PK_SEC43_JOB2_CLUSTER_DATACHECK.dat"

inp_sha = get_hash(inp_name)
uel_sha = get_hash(uel_name)
pbs_sha = get_hash(pbs_name)
notif_sha = get_hash(notif_name)
dc_sha = get_hash(dc_name) if (deck_dir / dc_name).exists() else ""

remote_run_dir = "/scratch9/pr21vyci/runs/mode1_pk_sec43_job2_adapted_f1708"
remote_pbs = f"{remote_run_dir}/{pbs_name}"

cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {remote_pbs}"'
canonical_cmd = " ".join(cmd.strip().split())
cmd_sha = hashlib.sha256(canonical_cmd.encode("utf-8")).hexdigest()

files_dict = {
    inp_name: inp_sha,
    uel_name: uel_sha,
    pbs_name: pbs_sha,
    notif_name: notif_sha
}
if dc_sha:
    files_dict[dc_name] = dc_sha

manifest = {
    "batch_name": "MODE1_PK_SEC43_JOB2_ADAPTED",
    "max_submissions": 1,
    "hours_valid": 24,
    "automatic_retry": False,
    "files": files_dict,
    "jobs": [
        {
            "id": "job2_adapted_prod",
            "pbs": pbs_name,
            "command": cmd,
            "command_sha256": cmd_sha,
            "max_submissions": 1,
            "depends_on": [],
            "purpose": "Pandey & Kumar (2025) Section 4.3 Job-2 Phase-Field Fracture Simulation: 10,065 physical elements (30,195 layered elements), native adapted mesh, 1 CPU serial reference anchor, 16 GB, 12h walltime (overnight execution), 2-step loading schedule to u_y = 1.50 mm (4,500 increments) to reproduce proposed PFM phase-field fracture progression (Figure 16b)",
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "queue": "entry_imfdfkmq",
            "execution": "single-rank serial",
            "input": inp_name,
            "datacheck": dc_name
        }
    ],
    "acceptance": {
        "job2_adapted_prod": "Abaqus 2023 single-rank serial solve completes Section 4.3 Job-2 phase-field fracture simulation on 10,065 physical elements (30,195 layered elements); reproduces primary crack deflection into hole, secondary crack propagation across right ligament to boundary, companion SDV damage field for Figure 16b comparison, and complete energy histories."
    },
    "adapter": "mode1-qualified-batch-v2",
    "scientific_scope": "MODE1",
    "technical_stage": "MODE1_BASELINE",
    "remote_run_dir": remote_run_dir,
    "required_state_checks": [
        "nodal_displacement_verified",
        "damage_irreversibility_verified",
        "committed_history_verified",
        "state_restoration_verified"
    ]
}

manifest_path = deck_dir / "F1708_PK_SEC43_JOB2_ADAPTED_AUTHORIZATION.json"
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"[PASS] Successfully generated manifest: {manifest_path}")
print(f"  Command SHA256: {cmd_sha}")
print(f"  Files: {files_dict}")
