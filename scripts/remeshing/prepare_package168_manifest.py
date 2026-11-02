#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare_package168_manifest.py
==============================
Builds and verifies the execution authorization manifest and package manifest
for Package 168: C5 Companion Continuum MISESERI Error Estimation.
"""

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "168_c5_companion_miseseri"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def main():
    inp_name = "M1_C5_COMPANION_MISESERI.inp"
    uel_name = "f42_mixed_uel.for"
    notif_name = "job_notifications.sh"
    pbs_name = "submit_M1_C5_COMPANION_MISESERI.pbs"
    dc_name = "M1_C5_COMPANION_MISESERI_DC.dat"

    inp_path = PKG_DIR / inp_name
    uel_path = PKG_DIR / uel_name
    notif_path = PKG_DIR / notif_name
    pbs_path = PKG_DIR / pbs_name
    dc_path = PKG_DIR / dc_name

    assert inp_path.is_file(), f"Missing {inp_path}"
    assert uel_path.is_file(), f"Missing {uel_path}"
    assert notif_path.is_file(), f"Missing {notif_path}"
    assert pbs_path.is_file(), f"Missing {pbs_path}"
    assert dc_path.is_file(), f"Missing {dc_path}"

    inp_hash = sha256_file(inp_path)
    uel_hash = sha256_file(uel_path)
    notif_hash = sha256_file(notif_path)
    pbs_hash = sha256_file(pbs_path)
    dc_hash = sha256_file(dc_path)

    # First update PACKAGE_MANIFEST.json
    pkg_manifest_data = {
        "schema": 1,
        "package_name": "MODE1_C5_COMPANION_MISESERI",
        "job_name": "M1_C5_COMPANION_MISESERI",
        "purpose": "Companion continuum linear-elastic static model on Candidate C5 discretization (12,996 CPE4 quads, 13,278 nodes) to recover authentic Abaqus MISESERI/MISESAVG error indicators for causal, same-load Method C C5->C6 adaptive remeshing.",
        "mesh_provenance": {
            "source_deck": "models\\pandey_kumar_mode1\\155_c5_candidate_mesh\\M1_C5_CANDIDATE_MESH.inp",
            "source_sha256": "db261f26d34352db743432a47fc929bf6b4b4e808a1d4c13146ff4902776d197",
            "elements": 12996,
            "nodes": 13278,
            "element_type": "CPE4",
            "duplicate_slit_flank_pairs": 53,
            "ligament_nodes": 62,
            "kinematic_tie_equations": 115
        },
        "loading": {
            "step_name": "STATIC_ELASTIC",
            "perturbation": True,
            "prescribed_u2_mm": 0.0018703125442191958,
            "load_source_fixture": "Validated checkpoint models\\pandey_kumar_mode1\\167_c5_package167_r3_c2_2_continuation\\evidence\\1419566.mmaster02\\converged_checkpoint_03.json at uy = 0.0018703125 mm"
        },
        "material": {
            "name": "STEEL",
            "youngs_modulus_kN_mm2": 210.0,
            "poissons_ratio": 0.3
        },
        "output_fields_requested": [
            "S",
            "MISESERI",
            "MISESAVG",
            "EVOL",
            "U",
            "RF"
        ],
        "files": {
            inp_name: inp_hash,
            uel_name: uel_hash,
            notif_name: notif_hash,
            pbs_name: pbs_hash,
            dc_name: dc_hash
        },
        "checkpoint_lineage": {
            "consumed_checkpoint_path": "models\\pandey_kumar_mode1\\167_c5_package167_r3_c2_2_continuation\\evidence\\1419566.mmaster02\\converged_checkpoint_03.json",
            "consumed_checkpoint_sha256": "EAA122B911FDFC353D230C4BFFCCD60F75D7FAF4A9FBBEC9E5CF6A8B51C0A476",
            "target_uy_mm": 0.0018703125442191958,
            "baseline_uy_mm": 0.0018653125442191958,
            "reaction_force_kN": 0.17992419004440308,
            "total_energy_kNmm": 0.00022639903,
            "outer_iteration": 2,
            "coupled_convergence": True,
            "contract": "Package 167 Stage C2-2 Forward Continuation"
        }
    }

    pkg_manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    with open(pkg_manifest_path, "w", encoding="utf-8") as f:
        json.dump(pkg_manifest_data, f, indent=2)

    pkg_manifest_hash = sha256_file(pkg_manifest_path)

    # Command specification
    remote_run_dir = "/scratch9/pr21vyci/runs/mode1_c5_package168_companion_miseseri"
    command_str = (
        'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 '
        f'-RemoteCommand "qsub -q entry_imfdfkmq {remote_run_dir}/{pbs_name}"'
    )
    canon_cmd = ' '.join(command_str.strip().split())
    command_hash = hashlib.sha256(canon_cmd.encode()).hexdigest().lower()

    # Build M1_C5_COMPANION_AUTHORIZATION.json
    auth_data = {
        "batch_name": "MODE1_PACKAGE_168_C5_COMPANION_MISESERI",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": remote_run_dir,
        "files": {
            inp_name: inp_hash,
            uel_name: uel_hash,
            notif_name: notif_hash,
            pbs_name: pbs_hash,
            "PACKAGE_MANIFEST.json": pkg_manifest_hash
        },
        "jobs": [
            {
                "id": "M1_C5_COMPANION_MISESERI",
                "pbs": pbs_name,
                "command": command_str,
                "command_sha256": command_hash,
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Package 168: Companion continuum linear elastic solve on C5 mesh at prescribed displacement uy = 0.0018703125 mm for authentic MISESERI error recovery",
                "cpus": 1,
                "memory_gb": 8,
                "walltime_hours": 1,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial",
                "input": inp_name,
                "datacheck": dc_name
            }
        ],
        "acceptance": {
            "M1_C5_COMPANION_MISESERI": "Exit code 0; authentic field outputs MISESERI, MISESAVG, S, EVOL captured in ODB for error-driven adaptation."
        }
    }

    auth_path = PKG_DIR / "M1_C5_COMPANION_AUTHORIZATION.json"
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(auth_data, f, indent=2)

    # Also write EXECUTION_MANIFEST.json
    exec_manifest_path = PKG_DIR / "EXECUTION_MANIFEST.json"
    with open(exec_manifest_path, "w", encoding="utf-8") as f:
        json.dump(auth_data, f, indent=2)

    print("Successfully generated:")
    print(f"  {pkg_manifest_path.name}: {pkg_manifest_hash}")
    print(f"  {auth_path.name}: {sha256_file(auth_path)}")
    print(f"  {exec_manifest_path.name}: {sha256_file(exec_manifest_path)}")
    print(f"  Command SHA256: {command_hash}")


if __name__ == "__main__":
    main()
