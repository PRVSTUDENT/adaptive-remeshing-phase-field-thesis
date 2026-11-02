# -*- coding: utf-8 -*-
"""
generate_turn22_preparation.py
Generate Turn 22 research preparation artifact:
Package 163-R2 live trajectory transient analysis, contraction rate measurement,
and explicit no-submission decision.
"""

import json
import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

files = [
    "results/validation/package163_r2_trajectory_analysis_turn22.json",
    "results/validation/package163_r2_live_telemetry_turn22.json",
    "scripts/validation/fetch_and_analyze_r2_telemetry.py",
    "tests/unit/test_package163_r2_trajectory_analysis.py",
    "scripts/validation/check_c2_2_submission_gates.py",
    "scripts/state_transfer/build_package_c2_2_continuation.py",
    "scripts/state_transfer/stage_c2_2_specification.py",
    "models/pandey_kumar_mode1/163_c5_package163_r2_c2_1_continuation/EXECUTION_MANIFEST.json"
]

evidence_sources = {}
for rel_path in files:
    p = REPO_ROOT / rel_path
    if not p.exists():
        raise FileNotFoundError("Missing: " + rel_path)
    h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
    evidence_sources[rel_path] = h
    print("{0}: {1}".format(rel_path, h))

analysis = json.loads((REPO_ROOT / "results/validation/package163_r2_trajectory_analysis_turn22.json").read_text(encoding="utf-8"))

finding = (
    "Package 163-R2 (Job 1419489.mmaster02) monitored at outer iteration 48 on mnode097: temporary increment increase "
    "between outers 29-37 diagnosed as active-set relaxation transient (7428 nodes released to free set, -56.6% active reduction) "
    "with zero limit cycling and 100% KKT compliance. Both delta_u (2.92e-7 -> 2.64e-7, rho_u ~ 0.969) and delta_H "
    "(0.0270 -> 0.0243 MPa, rho_H ~ 0.977) have entered steady contraction; 200 outer budget provides ample headroom (~152 outers). "
    "No-submission fallback maintained while R2 computes."
)

prep_artifact = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "verification_passed": True,
    "operation": "research_preparation",
    "title": "Package 163-R2 Actual Solver Trajectory Analysis, Transient Diagnosis, and Budget Evaluation",
    "finding": finding,
    "trajectory_evidence": analysis,
    "job_submission_decision": {
        "submission_withheld": True,
        "reason": "PREDECESSOR_CHECKPOINT_02_PENDING_COMPLETION",
        "running_job_id": "1419489.mmaster02",
        "explanation": "Job 1419489 is actively running in PBS on mnode097. Authentic Checkpoint 02 does not yet exist. Submitting C2-2 now would violate predecessor qualification. Submission is withheld under the no-submission fallback."
    },
    "alignment_with_40_turn_objective": {
        "programme_phase": "Phase C2: C5 Forward Continuation and Crack Propagation Tracking",
        "active_milestone": "Stage C2-1 (+5 nm) coupled convergence and Checkpoint 02 physical validation",
        "turn_budget_status": "Turn 22 of 40: on track. R2 computing in outer 48/200; C2-2 builder fully prepared for instant dispatch once R2 commits Checkpoint 02."
    },
    "next_operation": "Monitor job 1419489.mmaster02 to terminal completion and evaluate authentic Checkpoint02 against unchanged physical acceptance criteria before unlocking Stage C2-2 submission",
    "evidence_sources": evidence_sources,
    "registered_paths": [
        "results/validation/package163_r2_trajectory_analysis_turn22.json",
        "results/validation/package163_r2_live_telemetry_turn22.json",
        "scripts/validation/fetch_and_analyze_r2_telemetry.py",
        "tests/unit/test_package163_r2_trajectory_analysis.py",
        "scripts/validation/generate_turn22_preparation.py"
    ]
}

out_path = REPO_ROOT / "results/validation/preparation-aedeeec0-c665-4644-9792-0ebbaaf0a0da.json"
out_path.write_text(json.dumps(prep_artifact, indent=2) + "\n", encoding="utf-8")
print("Wrote preparation artifact to: " + str(out_path))
