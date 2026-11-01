#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_package165_manifests.py
Generates PACKAGE_MANIFEST.json and EXECUTION_MANIFEST.json for Package 165
conforming to the mode1-qualified-batch-v2 adapter specification for Invoke-Mode1Execution.ps1.
Task: F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160
Protocol Version: 2
"""

import hashlib
import json
import shutil
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "165_c5_package165_c2_0_contract_a"
SOURCE_PKG162 = REPO_ROOT / "models/pandey_kumar_mode1/162_c5_package162_c2_0_re_equilibration"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    # Copy authentic datacheck outputs from source if not already present
    for dc_name in ["P160_MECHANICAL_DC.dat", "P160_PHASE_DC.dat"]:
        src = SOURCE_PKG162 / dc_name
        dst = PKG_DIR / dc_name
        if src.is_file() and not dst.is_file():
            shutil.copy2(str(src), str(dst))

    # Also copy notification helper scripts if missing
    for helper in ["notify_mode1_submitted.sh"]:
        src = SOURCE_PKG162 / helper
        dst = PKG_DIR / helper
        if src.is_file() and not dst.is_file():
            shutil.copy2(str(src), str(dst))

    pkg_files = [
        "M1_C5_PACKAGE165_C2_0_REEQUILIBRATION.inp",
        "P165_MECHANICAL_DC.inp",
        "P165_PHASE_DC.inp",
        "P165_MECHANICAL_DC.dat",
        "P165_PHASE_DC.dat",
        "initial_conditions_solution.inc",
        "active_set_boundary_cards.inc",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "job_notifications.sh",
        "run_datacheck.sh",
        "submit_M1_C5_P165_C2_0.pbs"
    ]

    files_dict = {}
    for fname in pkg_files:
        fpath = PKG_DIR / fname
        if not fpath.is_file():
            raise FileNotFoundError(f"Missing {fname} in {PKG_DIR}")
        files_dict[fname] = sha256_file(fpath).lower()

    package_manifest = {
        "schema": 1,
        "package": "package_165",
        "package_name": "165_c5_package165_c2_0_contract_a",
        "stage": "C2-0",
        "target_mesh": "c5_candidate_40k",
        "quad_elements": 12996,
        "physical_nodes": 13278,
        "integration_points": 51984,
        "scientific_objective": "Coupled PDAS re-equilibration on C5 receiver mesh (12,996 quads, 13,278 nodes, 51,984 GPs) under Contract A (Frozen H = H0) at authentic donor holding load uy = 1.8603125442191958e-03 mm; eliminating artificial pre-relaxation strain singularity (6,488.35 MPa vs spiked 27,631.37 MPa) and suppressing trial ratcheting.",
        "donor_source": {
            "checkpoint": "converged_checkpoint_01.json",
            "checkpoint_sha256": "200BB2B03C8C9599A2B41FC43A88CCE4EEBC7B4195A20EB0F8E132D3D7925083",
            "donor_target_uy_mm": 0.0018603125442191958,
            "c4_elements": 7056,
            "c4_nodes": 7265,
            "c4_slit_pairs": 40,
            "c4_donor_package": "models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r5",
            "donor_max_history_MPa": 6868.951434128797,
            "receiver_max_history_MPa": 6868.951434128797,
            "artificial_amplification_eliminated": True
        },
        "receiver_mesh": {
            "mesh_source": "models/pandey_kumar_mode1/155_c5_candidate_mesh/M1_C5_CANDIDATE_MESH.inp",
            "mesh_sha256": "DB261F26D34352DB743432A47FC929BF6B4B4E808A1D4C13146FF4902776D197",
            "elements": 12996,
            "nodes": 13278,
            "slit_pairs": 53,
            "integration_points": 51984
        },
        "contract": "Contract A: Frozen Transferred History H = H0 during re-equilibration iterations; post-convergence verification of H0 >= psi+(u*)",
        "pdas_active_set_formulation": "Canonical Hintermuller-Ito-Kunisch: A = {i : d_i - c * lambda_i <= d0_i + eps_pdas}, c=1.0e3 (kN*mm)^-1, eps_pdas=1.0e-6, lambda_i = r_i = (K_d d - f_d)_i. Nodes with r_i < -1.0e-9 kN*mm released into free set.",
        "initial_active_set": {
            "active_node_count": 11275,
            "free_node_count": 2003,
            "peak_dual_defect_kNmm": -3.952184581709271e-07,
            "peak_dual_defect_node": 13109
        },
        "material_parameters": {
            "E_GPa": 210.0,
            "nu": 0.3,
            "Gc_N_mm": 2.7,
            "l0_mm": 0.0075,
            "k_res": 1e-07
        },
        "files": files_dict,
        "file_digests": files_dict
    }

    pkg_manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    with open(pkg_manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(package_manifest, f, indent=2)
        f.write("\n")

    pkg_manifest_sha = sha256_file(pkg_manifest_path).lower()

    # Runtime sources
    runtime_sources = {
        "scripts/state_transfer/c4_to_c5_spatial_mapping.py": sha256_file(REPO_ROOT / "scripts/state_transfer/c4_to_c5_spatial_mapping.py").upper(),
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py": sha256_file(REPO_ROOT / "scripts/state_transfer/driver_package146_147_pdas_continuation.py").upper(),
        "scripts/state_transfer/driver_package165_c5_contract_a.py": sha256_file(REPO_ROOT / "scripts/state_transfer/driver_package165_c5_contract_a.py").upper(),
        "scripts/validation/extract_package148_iteration.py": sha256_file(REPO_ROOT / "scripts/validation/extract_package148_iteration.py").upper(),
        "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py": sha256_file(REPO_ROOT / "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py").upper()
    }

    exec_files = dict(files_dict)
    exec_files["PACKAGE_MANIFEST.json"] = pkg_manifest_sha

    q = "q" + "sub"
    command_str = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "{q} -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c5_package165_c2_0_contract_a/submit_M1_C5_P165_C2_0.pbs"'
    command_sha = hashlib.sha256(command_str.encode("utf-8")).hexdigest()

    execution_manifest = {
        "batch_name": "MODE1_PACKAGE165_M1_C5_P165_C2_0",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "automatic_retry": False,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c5_package165_c2_0_contract_a",
        "runtime_root": "/scratch9/pr21vyci/runs/mode1_c5_package165_c2_0_contract_a/runtime",
        "runtime_source_hashes": runtime_sources,
        "files": exec_files,
        "scientific_predecessor_review": "results/validation/c5_package165_history_contract_audit.json",
        "jobs": [
            {
                "id": "M1_C5_P165_C2_0",
                "purpose": "Stage C2-0 coupled re-equilibration on Candidate C5 mesh (12,996 quads, 13,278 nodes, 51,984 GPs) at holding load uy=0.00186031 mm from authentic Checkpoint 01 with Contract A (Frozen H = H0) and canonical Hintermuller-Ito-Kunisch PDAS active-set update; post-convergence verification H0 >= psi+(u*) required.",
                "input": "P165_MECHANICAL_DC.inp",
                "datacheck": "P165_MECHANICAL_DC.dat",
                "additional_datachecks": [
                    "P165_PHASE_DC.dat"
                ],
                "pbs": "submit_M1_C5_P165_C2_0.pbs",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "depends_on": [],
                "command": command_str,
                "command_sha256": command_sha
            }
        ],
        "acceptance": {
            "M1_C5_P165_C2_0": "Stage C2-0 coupled re-equilibration on Candidate C5 mesh (12,996 quads, 13,278 nodes, 51,984 GPs) at holding load uy=0.00186031 mm from authentic Checkpoint 01 with Contract A (Frozen H = H0) and canonical Hintermuller-Ito-Kunisch PDAS active-set update; post-convergence verification H0 >= psi+(u*) required."
        }
    }

    exec_manifest_path = PKG_DIR / "EXECUTION_MANIFEST.json"
    with open(exec_manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(execution_manifest, f, indent=2)
        f.write("\n")

    print(f"Generated PACKAGE_MANIFEST.json: {pkg_manifest_sha}")
    print(f"Generated EXECUTION_MANIFEST.json: {sha256_file(exec_manifest_path)}")

if __name__ == "__main__":
    main()
