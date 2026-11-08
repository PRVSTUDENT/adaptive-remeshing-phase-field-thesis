# -*- coding: utf-8 -*-
import json
import hashlib
from pathlib import Path

repo_root = Path(r"D:\Master thesis\Adaptive remeshing")
deck_dir = repo_root / "models/pandey_kumar_mode1/192_pk_sec43_staggered_job1"

def get_hash(filename):
    p = deck_dir / filename
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().lower()

inp_name = "PK_SEC43_STAGGERED_JOB1.inp"
uel_name = "f42_staggered_variant_uel.for"
pbs_name = "submit_M1_PK_SEC43_STAGGERED_JOB1.pbs"
notif_name = "job_notifications.sh"
dc_name = "PK_SEC43_STAGGERED_DC.dat"

inp_sha = get_hash(inp_name)
uel_sha = get_hash(uel_name)
pbs_sha = get_hash(pbs_name)
notif_sha = get_hash(notif_name)
dc_sha = get_hash(dc_name)

remote_run_dir = "/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1"
remote_pbs = f"{remote_run_dir}/{pbs_name}"

cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {remote_pbs}"'
cmd_sha = hashlib.sha256(cmd.encode("utf-8")).hexdigest()

manifest = {
    "batch_name": "MODE1_METHOD_A_PK_SEC43_STAGGERED",
    "max_submissions": 1,
    "hours_valid": 24,
    "automatic_retry": False,
    "files": {
        inp_name: inp_sha,
        uel_name: uel_sha,
        pbs_name: pbs_sha,
        notif_name: notif_sha,
        dc_name: dc_sha
    },
    "jobs": [
        {
            "id": "pk_sec43_staggered_job1",
            "pbs": pbs_name,
            "command": cmd,
            "command_sha256": cmd_sha,
            "max_submissions": 1,
            "depends_on": [],
            "purpose": "Method A Pandey-Kumar Section 4.3 Job-1 Staggered-Solver Rerun: Operator-split staggered solver (*STATIC, DIRECT, Molnar & Gravouil 2017 Ref [72] cited by Pandey & Kumar 2025) on 3,923 physical elements (11,769 layered elements), 1-CPU serial, 2-step loading to u_y = 1.5 mm, generating authentic donor state across load increments for native MISESERI error evaluation and comparison against Fig. 15b.",
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
        "pk_sec43_staggered_job1": "Abaqus 2023 single-rank serial solve completes Stage B Job-1 staggered operator-split phase-field fracture simulation on 3,923 physical elements (11,769 layered elements) to u_y approx 1.5 mm, producing donor ODB for native MISESERI evaluation against Fig. 15b."
    },
    "adapter": "mode1-experimental-staggered-v1",
    "configuration": "STAGGERED_SOLVER",
    "hypothesis": "Molnar & Gravouil (2017) staggered operator split (*STATIC, DIRECT) resolves monolithic Newton tangent non-convexity during damage localization, enabling full horizon simulation without cutback exhaustion.",
    "scientific_scope": "MODE1",
    "technical_stage": "STAGGERED_SOLVER",
    "remote_run_dir": remote_run_dir,
    "required_state_checks": [
        "nodal_displacement_verified",
        "damage_irreversibility_verified",
        "committed_history_verified",
        "state_restoration_verified"
    ]
}

manifest_path = deck_dir / "METHOD_A_PK_SEC43_STAGGERED_AUTHORIZATION.json"
with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)

print(f"[PASS] Successfully generated manifest: {manifest_path}")
print(f"  Command SHA256: {cmd_sha}")
