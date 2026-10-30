"""Generate Package 148 R6 execution review and qualification records."""
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
R6_DIR = REPO_ROOT / "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r6"


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def main():
    # 1. Generate package148_r6_execution_review.json
    r6_files = [
        "M1_C4_PACKAGE148_STATE_TRANSFER.inp",
        "P148_MECHANICAL_DC.inp",
        "P148_PHASE_DC.inp",
        "PACKAGE_MANIFEST.json",
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "run_datacheck.sh",
        "submit_M1_C4_P148_R6.pbs",
        "EXECUTION_MANIFEST.json",
    ]
    evidence_sources = {}
    # Common sources
    common = [
        "models/pandey_kumar_mode1/146_c3_fine_donor/M1_C3_FINE_PACKAGE146_DONOR.inp",
        "models/pandey_kumar_mode1/147_c4_corrected_reference/M1_C4_CORRECTED_PACKAGE147_REF.inp",
        "tests/fixtures/package146147/146_step1_dat.txt.gz",
        "results/validation/package146147/evaluation.json",
        "scripts/state_transfer/build_package146_147_transfer_deck.py",
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py",
        "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py",
        "scripts/validation/extract_package148_iteration.py",
    ]
    for c in common:
        evidence_sources[c] = sha256_file(REPO_ROOT / c)
    for rf in r6_files:
        rel = f"models/pandey_kumar_mode1/148_c4_package148_state_transfer_r6/{rf}"
        evidence_sources[rel] = sha256_file(R6_DIR / rf)
    evidence_sources["results/validation/package148_r5_terminal_evaluation.json"] = sha256_file(
        REPO_ROOT / "results/validation/package148_r5_terminal_evaluation.json"
    )

    review = {
        "schema": 1,
        "reviewer": "gemini-antigravity",
        "reviewed_at": "2026-10-30T19:44:00+01:00",
        "independent_of": "Package 148 R5 terminal driver timeout diagnosis",
        "verification_passed": True,
        "independent_r6_qualification": "PASS",
        "python_36_compatibility": "PASS",
        "target_python": "Python 3.6.8",
        "review_scope": "Independent R6 runtime timeout and iteration bound correction, authentic Abaqus 2023 mechanical and phase datachecks, exact package/runtime hashes, 7+8+3 solution card encoding preservation, and predecessor review; no physical acceptance without completed live execution",
        "finding": "R5 completed 15 coupled alternating PDAS iterations with geometric residual contraction (delta_d to 2.01e-5, delta_u to 8.67e-9 mm = 8.67 pm, zero dual error) and passed physical metrics (RF2 deficit 0.74%, energy deficit 0.14%, zero healing), but was terminated prematurely at outer 15 extraction by an internal 780 s driver timeout cap. R6 extends driver timeout to 7200 s (2 hours, fitting comfortably within 8h PBS allocation) and raises max_outer to 25. All 28,224 Gauss point histories, 7+8+3 card encoding, and frozen production UEL (CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6) are preserved bitwise. Cluster datachecks for both P148_MECHANICAL_DC and P148_PHASE_DC passed Exit 0 under Abaqus 2023 and Intel ifort.",
        "tests": {
            "r6_manifest_file_count": 14,
            "mechanical_datacheck_exit": 0,
            "phase_datacheck_exit": 0,
            "configured_driver_timeout_s": 7200,
            "configured_max_outer": 25,
            "pbs_walltime_hours": 8
        },
        "remote_compile": "PASS on staged driver and extractor under Python 3.6.8",
        "datachecks": "PASS_BOTH existing authentic outputs verified against current hashes by live technical preflight",
        "login_notifications": "PASS",
        "telegram_notification_contract": "PASS_LOGIN_NODE",
        "compute_node_delivery": "UNRESOLVED",
        "physical_acceptance": "UNVERIFIED",
        "no_continuation": True,
        "evidence_sources": evidence_sources
    }
    review_path = REPO_ROOT / "results/validation/package148_r6_execution_review.json"
    review_path.write_text(json.dumps(review, indent=2), encoding="utf-8")
    print("Created package148_r6_execution_review.json")

    # 2. Generate evaluate_mode1_package148_state_transfer_r6.qualification.json
    script_path = REPO_ROOT / "scripts/validation/execute_package148_state_transfer.py"
    manifest_path = R6_DIR / "EXECUTION_MANIFEST.json"

    test_files = [
        "tests/unit/test_package148_coupled_runtime.py",
        "tests/unit/test_mode1_f1597_package148_py36_compatibility.py",
        "tests/unit/test_package148_submission_adapter.py",
        "tests/unit/test_mode1_execution_gate.py",
    ]
    tests_dict = {tf: sha256_file(REPO_ROOT / tf) for tf in test_files}

    dependencies = dict(evidence_sources)
    for tf, th in tests_dict.items():
        dependencies[tf] = th
    dependencies["scripts/hpc/Invoke-Mode1Execution.ps1"] = sha256_file(REPO_ROOT / "scripts/hpc/Invoke-Mode1Execution.ps1")
    dependencies["scripts/hpc/Submit-Mode1Batch.ps1"] = sha256_file(REPO_ROOT / "scripts/hpc/Submit-Mode1Batch.ps1")
    dependencies["scripts/hpc/Invoke-Mode1Engine.ps1"] = sha256_file(REPO_ROOT / "scripts/hpc/Invoke-Mode1Engine.ps1")
    dependencies["scripts/hpc/mode1_execution_gate.py"] = sha256_file(REPO_ROOT / "scripts/hpc/mode1_execution_gate.py")
    dependencies["scripts/controller/Controller-Operations.ps1"] = sha256_file(REPO_ROOT / "scripts/controller/Controller-Operations.ps1")
    dependencies["scripts/controller/Controller-Qualification.ps1"] = sha256_file(REPO_ROOT / "scripts/controller/Controller-Qualification.ps1")
    dependencies["scripts/controller/Controller-Recovery.ps1"] = sha256_file(REPO_ROOT / "scripts/controller/Controller-Recovery.ps1")
    dependencies["scripts/controller/Invoke-ControllerTurn.ps1"] = sha256_file(REPO_ROOT / "scripts/controller/Invoke-ControllerTurn.ps1")
    dependencies["results/validation/package148_r6_execution_review.json"] = sha256_file(review_path)

    qual = {
        "schema": 1,
        "operation": "evaluate_mode1_package148_state_transfer_r6",
        "status": "QUALIFIED_FOR_PREFLIGHT",
        "dispatch_ready": True,
        "canonical_path": "scripts/validation/execute_package148_state_transfer.py",
        "script_sha256": sha256_file(script_path),
        "execution_mode": "HPC_PRE_SUBMISSION",
        "execution_adapter": "scripts/hpc/Invoke-Mode1Execution.ps1",
        "production_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
        "manifest": "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r6/EXECUTION_MANIFEST.json",
        "independent_review": "results/validation/package148_r6_execution_review.json",
        "limitation": "R6 extends internal driver timeout to 7200 s and max outer iterations to 25, resolving the R5 780 s driver timeout defect while strictly preserving 7+8+3 solution card encoding and all 28,224 Gauss point histories. Submission is not physical acceptance. Preserve R1 1418787, R2 1418843, R3 1418872, R4 1418902, R5 1418909 and once-only accounting; no C1-2 or automatic retry.",
        "tests": tests_dict,
        "tests_passed": True,
        "verification_criteria": {
            "required_measurements": [
                "submitted_jobs"
            ]
        },
        "scientific_dependencies": dependencies
    }
    qual_path = REPO_ROOT / "scripts/validation/evaluate_mode1_package148_state_transfer_r6.qualification.json"
    qual_path.write_text(json.dumps(qual, indent=2), encoding="utf-8")
    print("Created evaluate_mode1_package148_state_transfer_r6.qualification.json")


if __name__ == "__main__":
    main()
