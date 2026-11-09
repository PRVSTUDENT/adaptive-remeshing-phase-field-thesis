# -*- coding: utf-8 -*-
"""
create_f1705_hole_e10_prod_authorization.py
============================================
Generates the Mode-I authorization manifest for Task F1705 Method A Hole Benchmark
Candidate E10 Production Fracture Simulation.
"""
import json
import hashlib
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
deck_dir = repo_root / "models" / "pandey_kumar_mode1" / "177_method_a_hole_e10_prod"

def get_hash(filename):
    p = deck_dir / filename
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().lower()

inp_name = "PK_HOLE_SEL_E10_PROD.inp"
uel_name = "f42_mixed_uel.for"
pbs_name = "submit_M1_HOLE_SEL_E10_PROD.pbs"
notif_name = "job_notifications.sh"
dc_name = "M1_HOLE_SEL_E10_CLUSTER_DATACHECK.dat"

inp_sha = get_hash(inp_name)
uel_sha = get_hash(uel_name)
pbs_sha = get_hash(pbs_name)
notif_sha = get_hash(notif_name)
dc_sha = get_hash(dc_name) if (deck_dir / dc_name).exists() else ""

remote_run_dir = "/scratch9/pr21vyci/runs/mode1_method_a_hole_f1705_prod"
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
    "batch_name": "MODE1_METHOD_A_HOLE_E10_PROD",
    "max_submissions": 1,
    "hours_valid": 24,
    "automatic_retry": False,
    "files": files_dict,
    "jobs": [
        {
            "id": "hole_e10_prod",
            "pbs": pbs_name,
            "command": cmd,
            "command_sha256": cmd_sha,
            "max_submissions": 1,
            "depends_on": [],
            "purpose": "Method A Hole Benchmark Candidate E10 Production Fracture Simulation: 9,164 physical elements (27,492 layered elements), narrow crack-following selective mesh, 1 CPU serial, 16 GB, 8h walltime, 2-step loading to u_y = 0.0150 mm to evaluate crack propagation, hole deflection, and load-displacement response",
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
        "hole_e10_prod": "Abaqus 2023 single-rank serial solve completes Method A Candidate E10 phase-field fracture simulation on 9,164 physical elements (27,492 layered elements); extracts complete load-displacement curve P(u), crack deflection into hole and right-flank propagation, companion SDV damage field, and energy histories."
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

manifest_path = deck_dir / "METHOD_A_HOLE_E10_PROD_AUTHORIZATION.json"
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"[PASS] Successfully generated manifest: {manifest_path}")
print(f"  Command SHA256: {cmd_sha}")
print(f"  Files: {files_dict}")
