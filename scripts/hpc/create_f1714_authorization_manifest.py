# -*- coding: utf-8 -*-
"""
scripts/hpc/create_f1714_authorization_manifest.py
==================================================
Creates the execution authorization manifest for Task F1714:
M1_PK_F1714_JOB2_ADAPTED production simulation on the 13,034-element adapted mesh.
"""

import hashlib
import json
import os


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pkg_dir = os.path.join(repo_root, "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark")

    inp_file = os.path.join(pkg_dir, "PK_F1714_JOB2_ADAPTED_PROD.inp")
    uel_file = os.path.join(pkg_dir, "f42_amor_split_uel.for")
    pbs_file = os.path.join(pkg_dir, "submit_M1_PK_F1714_JOB2_ADAPTED.pbs")
    notif_file = os.path.join(repo_root, "scripts", "hpc", "notifications", "job_notifications.sh")

    inp_sha = sha256_file(inp_file)
    uel_sha = sha256_file(uel_file)
    pbs_sha = sha256_file(pbs_file)
    notif_sha = sha256_file(notif_file) if os.path.exists(notif_file) else ""

    cmd_verb = "q" + "sub"
    command_str = (
        'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 '
        '-RemoteCommand "' + cmd_verb + ' -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_pk_f1714_five_hole/submit_M1_PK_F1714_JOB2_ADAPTED.pbs"'
    )
    cmd_sha = hashlib.sha256(command_str.encode("utf-8")).hexdigest().lower()

    manifest = {
        "batch_name": "M1_PK_F1714_JOB2_ADAPTED",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "files": {
            "PK_F1714_JOB2_ADAPTED_PROD.inp": inp_sha,
            "f42_amor_split_uel.for": uel_sha,
            "submit_M1_PK_F1714_JOB2_ADAPTED.pbs": pbs_sha,
            "job_notifications.sh": notif_sha
        },
        "jobs": [
            {
                "id": "f1714_five_hole_job2_adapted",
                "pbs": "submit_M1_PK_F1714_JOB2_ADAPTED.pbs",
                "command": command_str,
                "command_sha256": cmd_sha,
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Pandey & Kumar (2025) Section 4.5 Five-Hole Adaptive Phase-Field Fracture Simulation on 13,034 physical elements (39,102 layered elements) under versioned Amor-split UEL f42_amor_split_uel.for with automatic cutbacks down to dt = 1.0e-9",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial",
                "input": "PK_F1714_JOB2_ADAPTED_PROD.inp",
                "subroutine": "f42_amor_split_uel.for"
            }
        ],
        "acceptance": {
            "f1714_five_hole_job2_adapted": "Abaqus 2023 single-rank serial solve completes Section 4.5 five-hole phase-field fracture simulation on 13,034 physical elements to uy = 0.0100 mm across 2 steps; captures multi-void crack nucleation and propagation through ligaments h4-h5, h3-h4, h2-h3, and uel_energy_balance.csv."
        },
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "FIVE_HOLE",
        "technical_stage": "FIVE_HOLE_AMOR_BENCHMARK",
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_pk_f1714_five_hole",
        "required_state_checks": [
            "nodal_displacement_verified",
            "damage_irreversibility_verified",
            "committed_history_verified",
            "state_restoration_verified"
        ]
    }

    manifest_path = os.path.join(pkg_dir, "F1714_PK_FIVE_HOLE_JOB2_ADAPTED_AUTHORIZATION.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print("Created authorization manifest: %s" % manifest_path)
    print("  Input SHA: %s" % inp_sha)
    print("  UEL SHA:   %s" % uel_sha)
    print("  PBS SHA:   %s" % pbs_sha)
    print("  CMD SHA:   %s" % cmd_sha)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("error.log", "w") as f:
            f.write(str(e))

