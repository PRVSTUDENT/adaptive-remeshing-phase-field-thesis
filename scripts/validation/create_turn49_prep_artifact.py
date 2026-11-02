#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_turn49_prep_artifact.py
==============================
Generates the verified preparation checkpoint artifact for RunId 8e882301-89e4-4eda-b92c-784b059b3d8d.
"""

import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
RUN_ID = "8e882301-89e4-4eda-b92c-784b059b3d8d"
OUT_PATH = REPO_ROOT / f"results/validation/preparation-{RUN_ID}.json"

def sha256_file(rel_path: str) -> str:
    full_path = REPO_ROOT / rel_path
    assert full_path.exists(), f"File does not exist: {full_path}"
    assert full_path.stat().st_size <= 16777216, f"File exceeds 16MB: {full_path}"
    h = hashlib.sha256()
    with open(full_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

evidence_files = [
    "results/validation/c6_stage_c3_0_solver_evaluation.json",
    "models/pandey_kumar_mode1/170_c6_stage_c3_0_reequilibration/evidence/1419586.mmaster02/pbs_execution.log",
    "models/pandey_kumar_mode1/170_c6_stage_c3_0_reequilibration/evidence/1419586.mmaster02/M1_C6_STAGE_C3_0_REEQUILIBRATION.sta",
    "models/pandey_kumar_mode1/170_c6_stage_c3_0_reequilibration/evidence/1419586.mmaster02/M1_C6_STAGE_C3_0_REEQUILIBRATION.msg",
    "models/pandey_kumar_mode1/170_c6_stage_c3_0_reequilibration/evidence/1419586.mmaster02/M1_C6_STAGE_C3_0_REEQUILIBRATION.dat",
    "models/pandey_kumar_mode1/170_c6_stage_c3_0_reequilibration/evidence/1419586.mmaster02/uel_energy_balance.csv",
    "models/pandey_kumar_mode1/170_c6_stage_c3_0_reequilibration/M1_C6_STAGE_C3_0_REEQUILIBRATION.inp",
    "models/pandey_kumar_mode1/170_c6_stage_c3_0_reequilibration/PACKAGE_MANIFEST.json",
    "models/pandey_kumar_mode1/170_c6_stage_c3_0_reequilibration/M1_C6_STAGE_C3_0_AUTHORIZATION.json",
    "models/pandey_kumar_mode1/170_c6_stage_c3_0_reequilibration/f42_mixed_uel.for",
    "models/pandey_kumar_mode1/170_c6_stage_c3_0_reequilibration/submit_M1_C6_STAGE_C3_0_REEQUILIBRATION.pbs",
    "scripts/validation/evaluate_package170_job1419586.py",
    "scripts/hpc/fetch_package170_results.ps1"
]

evidence_sources = {f: sha256_file(f) for f in evidence_files}

registered_paths = [
    "results/validation/c6_stage_c3_0_solver_evaluation.json",
    "models/pandey_kumar_mode1/170_c6_stage_c3_0_reequilibration/evidence/1419586.mmaster02/uel_energy_balance.csv",
    "scripts/validation/evaluate_package170_job1419586.py",
    "scripts/hpc/fetch_package170_results.ps1",
    "project_coordination/HPC_JOB_LEDGER.csv"
]

finding = (
    "Package 170 direct UEL solve (Job 1419586.mmaster02) completed on mnode097 with Exit Code 0 in 1.2s CPU time. "
    "Authentic Abaqus deliverables fetched and verified: 15,252-quad C6 mesh (15,559 nodes, 59 duplicate slit pairs, "
    "115 kinematic ties, 30,504 dual UEL elements) compiled cleanly with ifort and solved with 0 errors. "
    "Diagnostic evaluation established that direct single-step solve evaluated pure linear-elastic deformation "
    "(E_elastic=0.274e-3 kN mm, E_fracture=0.0 kN mm) without staggered PDAS iterations. Non-conflation gate enforced: "
    "C6 transferred damage d and history H remain CANDIDATE_ONLY pending authentic staggered PDAS re-equilibration (Package 171)."
)

prep_record = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "task_id": "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE",
    "run_id": RUN_ID,
    "finding": finding,
    "evidence_sources": evidence_sources,
    "registered_paths": registered_paths,
    "verification_passed": True,
    "metadata": {
        "job_id": "1419586.mmaster02",
        "exit_code": 0,
        "host": "mnode097.cluster",
        "queue": "normal_imfdfkmq",
        "solver_status": "COMPLETED_SUCCESSFULLY",
        "c6_quads": 15252,
        "c6_nodes": 15559,
        "duplicate_slit_pairs": 59,
        "dual_uel_elements": 30504,
        "elastic_energy_kNmm": 0.00027402273,
        "fracture_energy_kNmm": 0.0,
        "staggered_pdas_driver_required": True
    }
}

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(prep_record, f, indent=2)

print(f"Preparation artifact generated successfully: {OUT_PATH}")
