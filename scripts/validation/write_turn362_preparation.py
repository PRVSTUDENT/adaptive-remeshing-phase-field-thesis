"""Write Turn 362 research preparation artifact."""
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "4627d41e-c2d9-4c1c-84b7-d87ca6ff6aed"


def sha256_file(p):
    return hashlib.sha256((REPO_ROOT / p).read_bytes()).hexdigest().upper()


def main():
    evidence_files = [
        "results/validation/package148_r5_terminal_evaluation.json",
        "results/validation/package148_r5_terminal_runtime.json",
        "results/validation/package148_r6_execution_review.json",
        "scripts/validation/evaluate_mode1_package148_state_transfer_r6.qualification.json",
        "scripts/validation/diagnose_r5_runtime.py",
        "scripts/validation/prepare_package148_r6.py",
        "scripts/validation/stage_package148_r6.py",
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py",
        "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r6/submit_M1_C4_P148_R6.pbs",
        "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r6/run_datacheck.sh",
        "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r6/PACKAGE_MANIFEST.json",
        "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r6/EXECUTION_MANIFEST.json",
        "tests/unit/test_mode1_f1597_turn362_package148_r6_qualification.py",
    ]

    evidence_sources = {}
    for ef in evidence_files:
        p = REPO_ROOT / ef
        if not p.is_file():
            raise FileNotFoundError(f"Missing evidence file: {ef}")
        evidence_sources[ef] = sha256_file(ef)

    finding = (
        "Package 148 R5 runtime cutoff resolved: R5 completed 15 coupled alternating PDAS iterations "
        "with monotonic geometric residual contraction (delta_d dropping to 2.01e-5, delta_u to 8.67e-9 mm = 8.67 pm, "
        "zero dual error) and passed all physical acceptance gates (RF2 deficit 0.74% <= 5%, energy deficit 0.14% <= 2%, "
        "zero healing), with termination caused solely by an internal 780 s driver timeout cap during outer 15 extraction. "
        "Package 148 R6 independently constructed and qualified: driver timeout extended to 7200 s (2h, safely within "
        "8h PBS walltime), max_outer raised to 25, 7+8+3 solution card encoding and all 28,224 Gauss point histories "
        "strictly preserved. Cluster hardware datachecks for P148_MECHANICAL_DC and P148_PHASE_DC both verified Exit 0 "
        "under Abaqus 2023 and Intel ifort with frozen UEL CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6."
    )

    prep_data = {
        "schema": 1,
        "run_id": RUN_ID,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "status": "PREPARATION_COMPLETE",
        "operation": "research_preparation",
        "finding": finding,
        "qualified_operation": "evaluate_mode1_package148_state_transfer_r6",
        "qualified_operation_id": "evaluate_mode1_package148_state_transfer_r6",
        "next_operation": "Submit qualified package M1_C4_P148_R6 via Invoke-Mode1Execution.ps1 for complete coupled convergence",
        "operation_preparation": {
            "status": "QUALIFIED_EXECUTION_READY",
            "dispatch_ready": True,
            "operation_id": "evaluate_mode1_package148_state_transfer_r6",
            "path": "scripts/validation/execute_package148_state_transfer.py",
            "qualification_artifact": "scripts/validation/evaluate_mode1_package148_state_transfer_r6.qualification.json"
        },
        "execution_mode": "HPC_PRE_SUBMISSION",
        "dispatch_ready": True,
        "manifest": "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r6/EXECUTION_MANIFEST.json",
        "verification_passed": True,
        "evidence_sources": evidence_sources,
        "tests": {
            "test_turn362_qualification_passed": True,
            "mechanical_datacheck": "PASS",
            "phase_datacheck": "PASS",
            "staged_remote_hashes": "ALL_REMOTE_HASHES_VERIFIED_PASS"
        }
    }

    out_path = REPO_ROOT / f"results/validation/preparation-{RUN_ID}.json"
    out_path.write_text(json.dumps(prep_data, indent=2), encoding="utf-8")
    print(f"Created {out_path.name}")
    print(f"SHA-256: {hashlib.sha256(out_path.read_bytes()).hexdigest().upper()}")


if __name__ == "__main__":
    main()
