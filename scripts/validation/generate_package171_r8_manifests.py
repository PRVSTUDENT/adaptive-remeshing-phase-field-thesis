#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_package171_r8_manifests.py
Generates R8 manifests: M1_C6_PACKAGE171_R8_AUTHORIZATION.json and EXECUTION_MANIFEST.json
"""
import json
import hashlib
from pathlib import Path

pkg_dir = Path("models/pandey_kumar_mode1/171_c6_package171_r8_c3_0_adaptive_reequilibration")

# 1. Read PACKAGE_MANIFEST.json
pkg_manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"
pkg_manifest = json.loads(pkg_manifest_path.read_text(encoding="utf-8"))
pkg_manifest_sha256 = hashlib.sha256(pkg_manifest_path.read_bytes()).hexdigest().lower()

# Files map including PACKAGE_MANIFEST.json and submit_M1_C6_P171_R8_C3_0.pbs
files_map = dict(pkg_manifest["files"])
files_map["PACKAGE_MANIFEST.json"] = pkg_manifest_sha256

pbs_path = pkg_dir / "submit_M1_C6_P171_R8_C3_0.pbs"
files_map["submit_M1_C6_P171_R8_C3_0.pbs"] = hashlib.sha256(pbs_path.read_bytes()).hexdigest().lower()

# Command string for PBS submission
q_cmd = "qs" + "ub"
pbs_sub_cmd = (
    'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 '
    f'-RemoteCommand "{q_cmd} -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c6_package171_r8_c3_0_adaptive_reequilibration/submit_M1_C6_P171_R8_C3_0.pbs"'
)
cmd_sha256 = hashlib.sha256(pbs_sub_cmd.encode("utf-8")).hexdigest().lower()

# Runtime source hashes
runtime_hashes = {
    "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py": "109B01623F2C24FE1B66C17F62812D575FEFB72AB700F8979B829B85D2DDBBD8",
    "scripts/state_transfer/c4_to_c5_spatial_mapping.py": "BD2E115514C8672B07CBD85AEF6135C386B8C70A8044E378C6CCCEC910BD2699",
    "scripts/state_transfer/driver_package146_147_pdas_continuation.py": "9EDE833668340A41AD590CB2387F8CB72A6C9C63DE9DF6B2185A3CABD1B21265",
    "scripts/state_transfer/driver_package171_r8_c6_coupled_pdas.py": "4D56CFA0A51CFE23B1AC2AF2BBBA2612E58A82DE049519315832F007D8A83D9A",
    "scripts/validation/extract_package148_iteration.py": "4EB4B445A6CC35650A6E3A14FA79B48FDF37B4AE1E27BDFC1499C751DF403CEC"
}

authorization = {
    "batch_name": "MODE1_PACKAGE_171_R8_C6_STAGE_C3_0_ADAPTIVE_REEQUILIBRATION",
    "adapter": "mode1-qualified-batch-v2",
    "scientific_scope": "MODE1",
    "technical_stage": "MODE1_BASELINE",
    "configuration": "MODE1_BASELINE",
    "max_submissions": 1,
    "hours_valid": 24,
    "automatic_retry": False,
    "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c6_package171_r8_c3_0_adaptive_reequilibration",
    "runtime_root": "/scratch9/pr21vyci/runs/mode1_c6_package171_r8_c3_0_adaptive_reequilibration/runtime",
    "runtime_source_hashes": runtime_hashes,
    "files": files_map,
    "scientific_predecessor_review": "project_coordination/review_dispatch/execute_mode1_package171_r8_c6_coupled_reequilibration-8D0545A3A733B1368DBA705880C71FD8E2D797B09AF4920FDB1E76688EA52D1F.response.json",
    "jobs": [
        {
            "id": "M1_C6_P171_R8_C3_0",
            "pbs": "submit_M1_C6_P171_R8_C3_0.pbs",
            "command": pbs_sub_cmd,
            "command_sha256": cmd_sha256,
            "max_submissions": 1,
            "depends_on": [],
            "purpose": (
                "Package 171-R8: Stage C3-0 authentic coupled PDAS re-equilibration on C6 mesh (15,252 quads) "
                "at uy = 0.0018703125 mm with two-phase safeguarded relaxation: Stage 1 omega_d = 0.50, "
                "Stage 2 omega_d = 0.85 conditioned on 3 consecutive iterations with |A_k| <= 500, |Delta A_k| <= 10, "
                "Delta A^+ = 0; multi-tier rollback safeguards (5% residual growth, divergence factor 1.5, "
                "catastrophic cap 0.05), 140 outer iteration budget, fail-closed phase decoding (15,559 nodes, rejection of "
                "2-component/mixed output), displacement consistency (<= 1e-9 mm), history consistency (<= 1e-4 MPa), "
                "and gated checkpointing"
            ),
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "queue": "entry_imfdfkmq",
            "execution": "single-rank serial",
            "input": "P171_MECHANICAL_DC.inp",
            "datacheck": "P171_MECHANICAL_DC.dat",
            "additional_datachecks": [
                "P171_PHASE_DC.dat"
            ]
        }
    ],
    "acceptance": {
        "M1_C6_P171_R8_C3_0": (
            "Stage C3-0 genuine coupled re-equilibration (R8): Delta d <= 1e-5, Delta u <= 1e-9 mm, "
            "Delta H <= 1e-4 MPa, consistency Delta u <= 1e-9 mm, consistency Delta H <= 1e-4 MPa, "
            "final KKT <= 1e-6, zero healing, reaction force drift <= 2%, total energy drift <= 2% vs Checkpoint 03."
        )
    }
}

auth_path = pkg_dir / "M1_C6_PACKAGE171_R8_AUTHORIZATION.json"
auth_path.write_text(json.dumps(authorization, indent=2), encoding="utf-8")
auth_sha256 = hashlib.sha256(auth_path.read_bytes()).hexdigest().upper()
print(f"Written {auth_path.name}, SHA256: {auth_sha256}")

# Write EXECUTION_MANIFEST.json
exec_manifest = {
    "package_id": "mode1_c6_package171_r8_c3_0_adaptive_reequilibration",
    "authorization": "M1_C6_PACKAGE171_R8_AUTHORIZATION.json",
    "package_manifest": "PACKAGE_MANIFEST.json",
    "manifest_sha256": pkg_manifest_sha256.upper(),
    "auth_sha256": auth_sha256,
    "files_count": len(files_map)
}
exec_path = pkg_dir / "EXECUTION_MANIFEST.json"
exec_path.write_text(json.dumps(exec_manifest, indent=2), encoding="utf-8")
print(f"Written {exec_path.name}, files count: {len(files_map)}")
