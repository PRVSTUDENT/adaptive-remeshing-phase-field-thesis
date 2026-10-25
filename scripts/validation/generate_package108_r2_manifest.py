#!/usr/bin/env python3
"""
generate_package108_r2_manifest.py
Generates the qualified Mode-I manifest for Package 108 Revision 2:
Candidate C3 Multi-Step Staggered Continuation.
"""

import json
import hashlib
from pathlib import Path

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def generate_manifest():
    repo_root = Path(__file__).resolve().parent.parent.parent
    pkg_dir = repo_root / "models" / "pandey_kumar_mode1" / "108_r2_c3_staggered_continuation"

    inp_name = "M1_C3_STAGGERED_R2_CONTINUATION.inp"
    uel_name = "f42_experimental_irreversible_uel.for"
    pbs_name = "submit_M1_C3_STAGGERED_R2.pbs"
    bounds_name = "d_lower_bounds.csv"
    notif_name = "job_notifications.sh"

    files_dict = {
        inp_name: compute_sha256(pkg_dir / inp_name),
        bounds_name: compute_sha256(pkg_dir / bounds_name),
        uel_name: compute_sha256(pkg_dir / uel_name),
        pbs_name: compute_sha256(pkg_dir / pbs_name),
        notif_name: compute_sha256(pkg_dir / notif_name)
    }

    run_dir = "/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r2"
    cmd_prefix = "powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand"
    sub_cmd = "qsub -q entry_imfdfkmq " + run_dir + "/" + pbs_name
    full_cmd = f'{cmd_prefix} "{sub_cmd}"'
    cmd_canonical = " ".join(full_cmd.strip().split())
    cmd_sha256 = hashlib.sha256(cmd_canonical.encode()).hexdigest()

    manifest = {
        "schema": 1,
        "adapter": "mode1-experimental-irrev-v1",
        "scientific_scope": "MODE1",
        "technical_stage": "C1-1",
        "batch_name": "MODE1_C3_STAGGERED_CONTINUATION_R2",
        "configuration": "STAGGERED_IRREVERSIBLE",
        "hypothesis": "Multi-step alternating minimization with boundary switching avoids Picard cutbacks and achieves continuous +5 nm forward continuation on Candidate C3.",
        "automatic_retry": False,
        "max_submissions": 1,
        "remote_run_dir": run_dir,
        "files": files_dict,
        "jobs": [
            {
                "id": "M1_C3_STAGGERED_R2",
                "purpose": "Abaqus 2023 Candidate C3 multi-step staggered forward continuation (+5 nm) with verified irreversible UEL (R2)",
                "input": inp_name,
                "user_subroutine": uel_name,
                "pbs": pbs_name,
                "datacheck": "M1_C3_STAGGERED_R2.dat",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "command": full_cmd,
                "command_sha256": cmd_sha256,
                "depends_on": []
            }
        ],
        "acceptance": {
            "stage_A_same_load": {
                "u_top_target_mm": 0.00196510735,
                "rf2_continuity_vs_c2_equil_pct_max": 5.0,
                "ef_continuity_vs_c2_equil_pct_max": 2.0,
                "healing_magnitude_max": 1e-08,
                "kkt_violations_max": 0
            },
            "stage_B_forward_continuation": {
                "delta_u_mm": 5e-06,
                "u_top_target_mm": 0.00197010735,
                "expected_rf2_N_approx": 179.3,
                "expected_ef_mJ_approx": 0.0624,
                "monotonic_softening_required": True,
                "monotonic_dissipation_required": True,
                "healing_magnitude_max": 1e-08
            }
        }
    }

    out_path = pkg_dir / "M1_C3_STAGGERED_R2_AUTHORIZATION.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Successfully generated manifest at {out_path}")
    return manifest

if __name__ == "__main__":
    generate_manifest()
