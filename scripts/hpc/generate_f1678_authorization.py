"""Generate METHOD_A_HOLE_F1678_PROD_AUTHORIZATION.json for Invoke-Mode1Execution.ps1."""
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis\Adaptive remeshing")
HOLE_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole"

def sha256_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().lower()

inp_sha = sha256_file(HOLE_DIR / "PK_HOLE_F1664_METHOD_A_PROD.inp")
uel_sha = sha256_file(REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for")
pbs_sha = sha256_file(HOLE_DIR / "submit_M1_HOLE_F1664_METHOD_A_PROD.pbs")
notif_sha = sha256_file(REPO_ROOT / "scripts" / "hpc" / "notifications" / "job_notifications.sh")

q = "qsub"
command_str = (
    r'powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 '
    f'-RemoteCommand "{q} -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_method_a_hole_f1664_prod/submit_M1_HOLE_F1664_METHOD_A_PROD.pbs"'
)
command_sha = hashlib.sha256(command_str.encode("utf-8")).hexdigest()

auth = {
    "batch_name": "MODE1_METHOD_A_HOLE_F1664_PROD",
    "max_submissions": 1,
    "hours_valid": 24,
    "automatic_retry": False,
    "files": {
        "PK_HOLE_F1664_METHOD_A_PROD.inp": inp_sha,
        "f42_mixed_uel.for": uel_sha,
        "submit_M1_HOLE_F1664_METHOD_A_PROD.pbs": pbs_sha,
        "job_notifications.sh": notif_sha
    },
    "jobs": [
        {
            "id": "hole_f1664_prod",
            "pbs": "submit_M1_HOLE_F1664_METHOD_A_PROD.pbs",
            "command": command_str,
            "command_sha256": command_sha,
            "max_submissions": 1,
            "depends_on": [],
            "purpose": (
                "Method A Refined Fracture Production Simulation: 20,213 physical elements "
                "(60,639 total layered elements), native 5% MISESERI adapted mesh, 2-step loading "
                "to u = 0.0120 mm to evaluate crack propagation and load-displacement response"
            ),
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "queue": "entry_imfdfkmq",
            "execution": "single-rank serial",
            "input": "PK_HOLE_F1664_METHOD_A_PROD.inp",
            "datacheck": "M1_HOLE_F1664_METHOD_A_DATACHECK.dat"
        }
    ],
    "acceptance": {
        "hole_f1664_prod": (
            "Abaqus 2023 single-rank serial solve executes refined Method A phase-field fracture "
            "simulation on 20,213 physical elements (60,639 layered elements); extracts complete "
            "load-displacement curve P(u), crack deflection into hole and right-flank propagation, "
            "companion SDV damage field, and energy histories."
        )
    },
    "adapter": "mode1-qualified-batch-v2",
    "scientific_scope": "MODE1",
    "technical_stage": "MODE1_BASELINE",
    "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_method_a_hole_f1664_prod",
    "required_state_checks": [
        "nodal_displacement_verified",
        "damage_irreversibility_verified",
        "committed_history_verified",
        "state_restoration_verified"
    ]
}

out_path = HOLE_DIR / "METHOD_A_HOLE_F1678_PROD_AUTHORIZATION.json"
out_path.write_text(json.dumps(auth, indent=2), encoding="utf-8")
print(f"Generated {out_path}")
print(f"Inp: {inp_sha}")
print(f"Uel: {uel_sha}")
print(f"Pbs: {pbs_sha}")
print(f"Notif: {notif_sha}")
print(f"Command SHA: {command_sha}")
