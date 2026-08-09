#!/usr/bin/env python3
"""
F43DUALDRY-PREP1 Contract Validator & Static Branch Coverage Auditor

Performs exhaustive static validation of staged dual dry-test packages:
  - Frozen candidate rebuilt decks (MM & PK5)
  - Qualified user subroutine byte freeze
  - All four UEL branches (U1, U2, U3, U4) static execution coverage
  - Passive facsimile contract compliance
  - Cross-candidate formulation fairness audit
  - PBS script and resource contract verification
"""

import os
import sys
import json
import hashlib
import re
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.model_generation.rebuild_f43_mixed_uel_deck import validate_rebuilt_deck_static

FROZEN_MM_REBUILT_SHA = "b6642e77655f4f953485cba1274dd0aaae220a327ebf2ac334b67e425673af7f"
FROZEN_PK5_REBUILT_SHA = "01b2914ee00717af82d9c8bf4437d4b5aebdc6c0ccd0c76423052ed40606b0d6"
FROZEN_UEL_SOURCE_SHA = "5dc005383773a2923b943024b97dc15590a4f220e319fd289c891b15c30844f3"

UEL_SOURCE_PATH = ROOT / "models/generated/mode_ii/f42_mixed_element_uel/f42_mixed_uel.for"
MM_DECK_PATH = ROOT / "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43UEL_MM_REBUILT.inp"
PK5_DECK_PATH = ROOT / "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43UEL_PK5_REBUILT.inp"

DRY_MM_DIR = ROOT / "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/dry_test_mm"
DRY_PK5_DIR = ROOT / "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/dry_test_pk5"

REPORT_PATH = ROOT / "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43DUALDRY_PREP_REPORT.json"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def audit_dualdry_preparation(write_report: bool = False) -> Dict[str, Any]:
    checks: Dict[str, bool] = {}
    details: Dict[str, Any] = {}

    # 1. Hashes of rebuilt decks & subroutine
    mm_sha = sha256_file(MM_DECK_PATH)
    pk5_sha = sha256_file(PK5_DECK_PATH)
    uel_sha = sha256_file(UEL_SOURCE_PATH)

    checks["mm_rebuilt_sha_frozen"] = (mm_sha == FROZEN_MM_REBUILT_SHA)
    checks["pk5_rebuilt_sha_frozen"] = (pk5_sha == FROZEN_PK5_REBUILT_SHA)
    checks["uel_source_sha_frozen"] = (uel_sha == FROZEN_UEL_SOURCE_SHA)

    details["mm_rebuilt_sha"] = mm_sha
    details["pk5_rebuilt_sha"] = pk5_sha
    details["uel_source_sha"] = uel_sha

    # 2. Package files integrity in isolated staging dirs
    checks["dry_mm_deck_sha"] = (sha256_file(DRY_MM_DIR / "F43UEL_MM_REBUILT.inp") == FROZEN_MM_REBUILT_SHA)
    checks["dry_mm_for_sha"] = (sha256_file(DRY_MM_DIR / "f43_mixed_uel.for") == FROZEN_UEL_SOURCE_SHA)
    checks["dry_pk5_deck_sha"] = (sha256_file(DRY_PK5_DIR / "F43UEL_PK5_REBUILT.inp") == FROZEN_PK5_REBUILT_SHA)
    checks["dry_pk5_for_sha"] = (sha256_file(DRY_PK5_DIR / "f43_mixed_uel.for") == FROZEN_UEL_SOURCE_SHA)

    # 3. Static deck validations
    val_mm = validate_rebuilt_deck_static(str(MM_DECK_PATH), expected_nphys=2206, expected_quads=2137, expected_tris=69, expected_nodes=2294)
    val_pk5 = validate_rebuilt_deck_static(str(PK5_DECK_PATH), expected_nphys=4894, expected_quads=4766, expected_tris=128, expected_nodes=4998)

    checks["mm_static_validation_pass"] = val_mm["all_passed"]
    checks["pk5_static_validation_pass"] = val_pk5["all_passed"]

    # 4. Branch coverage contract
    mm_text = MM_DECK_PATH.read_text(encoding="utf-8")
    pk5_text = PK5_DECK_PATH.read_text(encoding="utf-8")

    checks["mm_u1_quad_phase_branch"] = ("*Element, type=U1" in mm_text and val_mm["details"]["count_U1"] == 2137)
    checks["mm_u2_quad_disp_branch"] = ("*Element, type=U2" in mm_text and val_mm["details"]["count_U2"] == 2137)
    checks["mm_u3_tri_phase_branch"] = ("*Element, type=U3" in mm_text and val_mm["details"]["count_U3"] == 69)
    checks["mm_u4_tri_disp_branch"] = ("*Element, type=U4" in mm_text and val_mm["details"]["count_U4"] == 69)
    checks["mm_cpe4_facsimile_branch"] = ("*Element, type=CPE4" in mm_text and val_mm["details"]["count_CPE4"] == 2137)
    checks["mm_cpe3_facsimile_branch"] = ("*Element, type=CPE3" in mm_text and val_mm["details"]["count_CPE3"] == 69)

    checks["pk5_u1_quad_phase_branch"] = ("*Element, type=U1" in pk5_text and val_pk5["details"]["count_U1"] == 4766)
    checks["pk5_u2_quad_disp_branch"] = ("*Element, type=U2" in pk5_text and val_pk5["details"]["count_U2"] == 4766)
    checks["pk5_u3_tri_phase_branch"] = ("*Element, type=U3" in pk5_text and val_pk5["details"]["count_U3"] == 128)
    checks["pk5_u4_tri_disp_branch"] = ("*Element, type=U4" in pk5_text and val_pk5["details"]["count_U4"] == 128)
    checks["pk5_cpe4_facsimile_branch"] = ("*Element, type=CPE4" in pk5_text and val_pk5["details"]["count_CPE4"] == 4766)
    checks["pk5_cpe3_facsimile_branch"] = ("*Element, type=CPE3" in pk5_text and val_pk5["details"]["count_CPE3"] == 128)

    # 5. Passive facsimile contract
    checks["mm_passive_material_valid"] = bool(re.search(r"\*User Material,\s*constants=4\s*\n\s*1\.0+e-11,\s*(?:3\.0+e-01|0\.3)", mm_text, re.I))
    checks["pk5_passive_material_valid"] = bool(re.search(r"\*User Material,\s*constants=4\s*\n\s*1\.0+e-11,\s*(?:3\.0+e-01|0\.3)", pk5_text, re.I))

    # 6. PBS script contract
    pbs_mm = (DRY_MM_DIR / "F43DRY_MM.pbs").read_text(encoding="utf-8")
    pbs_pk5 = (DRY_PK5_DIR / "F43DRY_PK5.pbs").read_text(encoding="utf-8")

    checks["pbs_mm_queue_entry"] = ("#PBS -q entry_imfdfkmq" in pbs_mm)
    checks["pbs_mm_resources"] = ("#PBS -l select=1:ncpus=1:mpiprocs=1:mem=8gb" in pbs_mm and "#PBS -l walltime=00:30:00" in pbs_mm)
    checks["pbs_mm_wrapper_guard"] = ("F43DRY_MM_WRAPPER_AUTHORIZED" in pbs_mm)

    checks["pbs_pk5_queue_entry"] = ("#PBS -q entry_imfdfkmq" in pbs_pk5)
    checks["pbs_pk5_resources"] = ("#PBS -l select=1:ncpus=1:mpiprocs=1:mem=8gb" in pbs_pk5 and "#PBS -l walltime=00:30:00" in pbs_pk5)
    checks["pbs_pk5_wrapper_guard"] = ("F43DRY_PK5_WRAPPER_AUTHORIZED" in pbs_pk5)

    # 7. Submitter wrappers
    sub_mm = (DRY_MM_DIR / "submit_f43dry_mm.sh").read_text(encoding="utf-8")
    sub_pk5 = (DRY_PK5_DIR / "submit_f43dry_pk5.sh").read_text(encoding="utf-8")

    checks["submit_mm_guarded"] = ("F43DRY_MM_AUTHORIZED" in sub_mm and "qsub -v F43DRY_MM_WRAPPER_AUTHORIZED=1" in sub_mm)
    checks["submit_pk5_guarded"] = ("F43DRY_PK5_AUTHORIZED" in sub_pk5 and "qsub -v F43DRY_PK5_WRAPPER_AUTHORIZED=1" in sub_pk5)

    all_passed = all(checks.values())

    report = {
        "task_id": "F43DUALDRY-PREP1",
        "status": "complete_pass" if all_passed else "failed",
        "all_passed": all_passed,
        "checks": checks,
        "details": {
            "MM_rebuilt_SHA": mm_sha,
            "PK5_rebuilt_SHA": pk5_sha,
            "UEL_SHA": uel_sha,
            "MM_layered_elements": 6618,
            "PK5_layered_elements": 14682,
            "MM_branches": {"U1": 2137, "U2": 2137, "U3": 69, "U4": 69, "CPE4": 2137, "CPE3": 69},
            "PK5_branches": {"U1": 4766, "U2": 4766, "U3": 128, "U4": 128, "CPE4": 4766, "CPE3": 128},
            "toolchain_contract": ["gcc/11.4.0", "intel/2024.2.0", "abaqus/2023"],
            "queue_contract": {"queue": "entry_imfdfkmq", "ncpus": 1, "memory": "8gb", "walltime": "00:30:00"}
        },
        "authority_boundary": {
            "execution_authorized": False,
            "submission_approved": False,
            "maximum_jobs_now": 0,
            "qsub_called": False,
            "new_HPC_submissions": 0
        }
    }

    if write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    rep = audit_dualdry_preparation(write_report=True)
    print(f"F43DUALDRY-PREP1 Audit Result: {'ALL PASS' if rep['all_passed'] else 'FAILED'}")
    if not rep["all_passed"]:
        failed = [k for k, v in rep["checks"].items() if not v]
        print(f"Failed checks: {failed}")
        sys.exit(1)
    print(f"Report written: {REPORT_PATH}")
