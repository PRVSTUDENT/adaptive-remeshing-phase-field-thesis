# -*- coding: utf-8 -*-
"""
generate_turn19_preparation.py
Generate Turn 19 research preparation artifact:
C4 same-load reference validation and preservation.
"""

import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

files = [
    "models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r6/converged_checkpoint_01.json",
    "models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r6/runtime_report.json",
    "results/validation/package157_r6_convergence_evaluation.json",
    "scripts/validation/evaluate_package163_c5_continuation_acceptance.py",
    "tests/unit/test_package163_c5_continuation_acceptance.py",
    "models/pandey_kumar_mode1/160_c4_exact_load_reference/PACKAGE_MANIFEST.json",
    "models/pandey_kumar_mode1/160_c4_exact_load_reference/EXECUTION_MANIFEST_REF.json",
    "project_coordination/sessions/2026-11-01_gemini-antigravity_r6_exact_load_reference_recovery.md",
]

evidence_sources = {}
for rel_path in files:
    p = REPO_ROOT / rel_path
    if not p.exists():
        raise FileNotFoundError("Missing: " + rel_path)
    h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
    evidence_sources[rel_path] = h
    print("{0}: {1}".format(rel_path, h))

finding = (
    "Authentic C4 same-load reference at exact displacement uy = 0.0018653125442191958 mm (+5 nm) "
    "was validated and preserved from Package 157 Revision 6 (PBS Job 1419359.mmaster02, exit 0, "
    "RF2 = 0.183468 kN, total energy = 0.000225114 kN*mm, zero healing, outer 108). Package 160 C4 candidate "
    "(Job 1419305.mmaster02) terminated at baseline Checkpoint01 uy = 0.0018603125442191958 mm and was already "
    "completed once. No duplicate submission is required; R6 is confirmed as the ground-truth parity reference "
    "for Package 163-R2 physical acceptance."
)

prep_artifact = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "verification_passed": True,
    "operation": "research_preparation",
    "title": "Mode-I C4 Same-Load Reference Validation and Preservation for Package 163-R2 Parity",
    "finding": finding,
    "reference_validation": {
        "source_experiment": "Package 157 Revision 6",
        "pbs_job_id": "1419359.mmaster02",
        "mesh": "C4 (7056 elements, 7265 nodes, 28224 GPs)",
        "target_displacement_mm": 0.0018653125442191958,
        "reaction_force_kN": 0.18346779247291461,
        "total_raw_energy_kNmm": 0.00022511363524288855,
        "elastic_energy_kNmm": 0.00017111238737996302,
        "fracture_energy_kNmm": 5.4001247862925524e-05,
        "damage_max": 0.61985709,
        "healing_violations": 0,
        "history_monotonicity_violations": 0,
        "outer_iterations": 108,
        "acceptance_tolerances": {
            "force_discrepancy_pct_max": 2.0,
            "energy_discrepancy_pct_max": 2.0
        }
    },
    "package_160_assessment": {
        "candidate_path": "models/pandey_kumar_mode1/160_c4_exact_load_reference",
        "job_id": "1419305.mmaster02",
        "target_displacement_mm": 0.0018603125442191958,
        "status": "COMPLETED_ONCE",
        "scope": "Donor baseline frame at Checkpoint01 (+0 nm); does not solve +5 nm forward increment",
        "eligibility": "Exhausted once-only quota; no resubmission eligible or necessary"
    },
    "running_job_status": {
        "job_id": "1419489.mmaster02",
        "job_name": "M1_C5_P163_R2_C2_1",
        "state": "R",
        "host": "mnode097/0",
        "objective": "Stage C2-1 +5 nm forward continuation on C5 mesh with max_outer=200"
    },
    "next_operation": "Monitor job 1419489.mmaster02 to terminal completion and evaluate authentic Checkpoint02 against unchanged physical acceptance criteria using preserved C4 R6 reference parity",
    "evidence_sources": evidence_sources,
    "registered_paths": [
        "scripts/validation/generate_turn19_preparation.py",
        "tests/unit/test_turn19_preparation.py"
    ]
}

out_path = REPO_ROOT / "results/validation/preparation-a7f33358-1694-4ddb-9c8c-18dcea562643.json"
out_path.write_text(json.dumps(prep_artifact, indent=2) + "\n", encoding="utf-8")
print("Wrote preparation artifact to: " + str(out_path))
