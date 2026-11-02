# -*- coding: utf-8 -*-
"""
stage_c2_2_specification.py
Mode-I Method C Cycle 2: Stage C2-2 (+5 nm Forward Continuation) Specification and Predecessor Guard.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2

Defines the mathematical, physical, and computational specifications for Stage C2-2
forward continuation on the Candidate C5 mesh, resolves predecessor lineage strictly
to Package 163-R3 (Job 1419499.mmaster02) and Package 157-R8 (Job 1419490.mmaster02),
explicitly rejects all disqualified R2 artifacts (Job 1419489.mmaster02), and enforces
the mandatory no-submission fallback when either predecessor is pending or unaccepted.

Lineage & Predecessor Guard:
1. Predecessor State: Strictly bound to Checkpoint 02 (converged at uy = 0.0018653125442191958 mm
   from Job 1419499.mmaster02 / Package 163-R3). Never starts from Checkpoint 01, synthetic state,
   or disqualified Package 163-R2 artifacts (Job 1419489.mmaster02).
2. Reference Benchmark: Strictly bound to independent C4-R8 reference (converged at target
   uy = 0.0018703125442191958 mm from Job 1419490.mmaster02 / Package 157-R8).
3. Step Scope: In-mesh forward continuation on existing C5 mesh (12,996 CPE4 elements, 13,278 nodes,
   51,984 integration points). No spatial interpolation or remeshing in this stage.
4. Stepping Schedule:
   - Initial displacement: uy_initial = 0.0018653125442191958 mm
   - Forward increment:    Delta_uy   = +0.0000050000000000000 mm (+5.0 nm)
   - Target displacement:  uy_target  = 0.0018703125442191958 mm
5. Staggered PDAS Solver:
   - Max outer iterations: 200
   - Tolerances: Delta_d <= 1e-5, Delta_u <= 1e-9 mm, Delta_H <= 1e-4 MPa
   - KKT tolerances: dual error <= 1e-6 kN*mm, free residual <= 1e-6 kN
   - Invariants: strict zero healing (healing >= -1e-6), monotone history (Delta_H >= 0.0)
   - Non-accumulating history law: H*(x) = max(H0(x), psi+(u*(x)))
   - Frozen UEL: SHA-256 CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6
6. Dual Predecessor Fail-Closed Guard:
   - If Checkpoint 02 (R3) or C4 reference (R8) is absent, unverified, or unaccepted,
     submission is strictly prohibited. The system records NO_SUBMISSION_FALLBACK.
"""

from __future__ import print_function, division
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

STAGE_NAME = "STAGE_C2_2_FORWARD_CONTINUATION"
MESH_STAGE = "C5"
TOTAL_C5_ELEMENTS = 12996
TOTAL_C5_NODES = 13278
TOTAL_C5_GPS = 51984
TOTAL_C5_SVARS = 207936

BASELINE_UY_MM = 0.0018653125442191958     # Checkpoint 02 load
INCREMENT_UY_MM = 0.0000050000000000000    # +5.0 nm forward step
TARGET_UY_MM = 0.0018703125442191958       # Checkpoint 03 load

MAX_OUTER_ITERATIONS = 200
TOL_DELTA_D = 1.0e-5
TOL_DELTA_U_MM = 1.0e-9
TOL_DELTA_H_MPA = 1.0e-4
TOL_FREE_RESIDUAL_KN = 1.0e-6
TOL_DUAL_ERROR_KNMM = 1.0e-6
HEALING_TOLERANCE = 1.0e-6

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

# Active Predecessor Lineage: Package 163-R3
ACTIVE_PREDECESSOR_JOB_ID = "1419499.mmaster02"
DISQUALIFIED_PREDECESSOR_JOB_IDS = ["1419489.mmaster02"]
R3_RUN_DIR = REPO_ROOT / "models/pandey_kumar_mode1/163_c5_package163_r3_c2_1_continuation"
CHECKPOINT_02_EXPECTED_PATH = R3_RUN_DIR / "evidence/1419499.mmaster02/converged_checkpoint_02.json"
CHECKPOINT_02_FALLBACK_PATH = R3_RUN_DIR / "converged_checkpoint_02.json"
R3_ACCEPTANCE_REPORT_PRIMARY = REPO_ROOT / "results/validation/package163_r3_c5_continuation_acceptance_report.json"
R3_ACCEPTANCE_REPORT_FALLBACK = R3_RUN_DIR / "evidence/1419499.mmaster02/package163_acceptance_report.json"

# Active Reference Lineage: Package 157-R8
ACTIVE_REFERENCE_JOB_ID = "1419490.mmaster02"
R8_RUN_DIR = REPO_ROOT / "models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r8"
C4_R8_ACCEPTANCE_REPORT_PRIMARY = REPO_ROOT / "results/validation/package157_r8_c1_2_continuation_acceptance_report.json"
C4_R8_ACCEPTANCE_REPORT_FALLBACK = R8_RUN_DIR / "evidence/1419490.mmaster02/package157_r8_acceptance_report.json"


def get_c2_2_specification():
    """Return the complete canonical specification dictionary for Stage C2-2."""
    return {
        "stage": STAGE_NAME,
        "mesh": MESH_STAGE,
        "discretization": {
            "elements": TOTAL_C5_ELEMENTS,
            "nodes": TOTAL_C5_NODES,
            "gauss_points": TOTAL_C5_GPS,
            "history_svars": TOTAL_C5_SVARS
        },
        "load_schedule": {
            "initial_uy_mm": BASELINE_UY_MM,
            "increment_uy_mm": INCREMENT_UY_MM,
            "target_uy_mm": TARGET_UY_MM
        },
        "solver": {
            "type": "STAGGERED_PDAS_NONACCUMULATING",
            "max_outer_iterations": MAX_OUTER_ITERATIONS,
            "delta_d_tol": TOL_DELTA_D,
            "delta_u_tol_mm": TOL_DELTA_U_MM,
            "delta_h_tol_MPa": TOL_DELTA_H_MPA,
            "free_residual_tol_kN": TOL_FREE_RESIDUAL_KN,
            "dual_error_tol_kNmm": TOL_DUAL_ERROR_KNMM,
            "healing_tolerance": HEALING_TOLERANCE
        },
        "predecessor_binding": {
            "required_checkpoint": "converged_checkpoint_02.json",
            "required_job_id": ACTIVE_PREDECESSOR_JOB_ID,
            "disqualified_job_ids": DISQUALIFIED_PREDECESSOR_JOB_IDS,
            "source_directory": str(R3_RUN_DIR),
            "predecessor_mesh": MESH_STAGE,
            "predecessor_load_uy_mm": BASELINE_UY_MM,
            "reference_benchmark_job_id": ACTIVE_REFERENCE_JOB_ID,
            "reference_benchmark_target_uy_mm": TARGET_UY_MM
        },
        "frozen_uel_sha256": FROZEN_UEL_SHA256,
        "resource_allocation": {
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "queue": "entry_imfdfkmq"
        }
    }


def evaluate_c2_2_submission_eligibility(checkpoint_override=None, r3_report_override=None, r8_report_override=None):
    """
    Evaluate whether Stage C2-2 is eligible for PBS submission.
    Implements the strict Dual Predecessor Guard:
    1. Rejects any artifact originating from disqualified Package 163-R2.
    2. Resolves Checkpoint 02 strictly from accepted Package 163-R3 output.
    3. Verifies physical acceptance report for Checkpoint 02.
    4. Verifies physical acceptance report for independent C4-R8 reference.
    Returns (eligible: bool, status: str, details: dict).
    """
    spec = get_c2_2_specification()

    # Determine Checkpoint 02 path
    chkpt_path = None
    if checkpoint_override is not None:
        chkpt_path = Path(checkpoint_override)
    elif CHECKPOINT_02_EXPECTED_PATH.exists():
        chkpt_path = CHECKPOINT_02_EXPECTED_PATH
    elif CHECKPOINT_02_FALLBACK_PATH.exists():
        chkpt_path = CHECKPOINT_02_FALLBACK_PATH

    # Check for disqualified R2 artifact contamination
    if chkpt_path is not None:
        p_str = str(chkpt_path).replace("\\", "/")
        if "package163_r2" in p_str or "1419489.mmaster02" in p_str:
            return {
                "eligible_for_submission": False,
                "status": "NO_SUBMISSION_FALLBACK",
                "block_reason": "REJECTED_DISQUALIFIED_R2_PREDECESSOR",
                "explanation": (
                    "Checkpoint 02 from disqualified Package 163-R2 / Job 1419489.mmaster02 is strictly rejected. "
                    "Package 167 requires authentic Checkpoint 02 from Package 163-R3 (Job 1419499.mmaster02)."
                ),
                "disqualified_source": str(chkpt_path),
                "specification": spec
            }

    if chkpt_path is None or not chkpt_path.exists():
        return {
            "eligible_for_submission": False,
            "status": "NO_SUBMISSION_FALLBACK",
            "block_reason": "PREDECESSOR_CHECKPOINT_02_MISSING",
            "explanation": (
                "Stage C2-2 forward continuation strictly requires physically accepted Checkpoint 02 "
                "(uy = 0.0018653125442191958 mm) from Job 1419499.mmaster02 (Package 163-R3). "
                "Because Job 1419499 is actively computing on cluster, "
                "Checkpoint 02 does not yet exist on disk. In accordance with project protocol, "
                "submission is withheld under the no-submission fallback until authentic R3 results are terminal and certified."
            ),
            "running_predecessor_job_id": ACTIVE_PREDECESSOR_JOB_ID,
            "specification": spec
        }

    # If Checkpoint 02 exists on disk, inspect its contents
    try:
        data = json.loads(chkpt_path.read_text(encoding="utf-8"))
        
        # Check job ID inside checkpoint if recorded
        source_job = data.get("job_id", "")
        if source_job in DISQUALIFIED_PREDECESSOR_JOB_IDS:
            return {
                "eligible_for_submission": False,
                "status": "NO_SUBMISSION_FALLBACK",
                "block_reason": "REJECTED_DISQUALIFIED_R2_PREDECESSOR",
                "explanation": (
                    "Checkpoint 02 metadata identifies source job as %s, which is a disqualified R2 run. "
                    "Stage C2-2 strictly requires Checkpoint 02 from Job %s." % (source_job, ACTIVE_PREDECESSOR_JOB_ID)
                ),
                "specification": spec
            }

        # Check target displacement
        uy = float(data.get("target_uy_mm", 0.0))
        if abs(uy - BASELINE_UY_MM) > 1e-12:
            return {
                "eligible_for_submission": False,
                "status": "NO_SUBMISSION_FALLBACK",
                "block_reason": "CHECKPOINT_02_LOAD_MISMATCH",
                "explanation": "Found checkpoint at uy=%r, expected baseline %r" % (uy, BASELINE_UY_MM),
                "specification": spec
            }

        # Check discretization invariants (C5: 13278 nodes, 51984 history points)
        nodes_data = data.get("nodal_displacements", {}) or data.get("nodes", {})
        gps_data = data.get("integration_point_history", {}) or data.get("history_variables", {})
        if nodes_data and len(nodes_data) != TOTAL_C5_NODES:
            return {
                "eligible_for_submission": False,
                "status": "NO_SUBMISSION_FALLBACK",
                "block_reason": "CHECKPOINT_02_NODE_COUNT_MISMATCH",
                "explanation": "Checkpoint 02 contains %d nodes, expected %d" % (len(nodes_data), TOTAL_C5_NODES),
                "specification": spec
            }
        if gps_data and len(gps_data) != TOTAL_C5_GPS:
            return {
                "eligible_for_submission": False,
                "status": "NO_SUBMISSION_FALLBACK",
                "block_reason": "CHECKPOINT_02_GP_COUNT_MISMATCH",
                "explanation": "Checkpoint 02 contains %d integration points, expected %d" % (len(gps_data), TOTAL_C5_GPS),
                "specification": spec
            }

        # Verify R3 Physical Acceptance Report
        r3_report_path = None
        if r3_report_override is not None:
            r3_report_path = Path(r3_report_override)
        elif R3_ACCEPTANCE_REPORT_PRIMARY.exists():
            r3_report_path = R3_ACCEPTANCE_REPORT_PRIMARY
        elif R3_ACCEPTANCE_REPORT_FALLBACK.exists():
            r3_report_path = R3_ACCEPTANCE_REPORT_FALLBACK

        if r3_report_path is None or not r3_report_path.exists():
            return {
                "eligible_for_submission": False,
                "status": "NO_SUBMISSION_FALLBACK",
                "block_reason": "R3_ACCEPTANCE_REPORT_MISSING",
                "explanation": (
                    "Checkpoint 02 exists on disk but Package 163-R3 physical acceptance report "
                    "has not been generated. Submission is withheld until evaluate_package163_c5_continuation_acceptance.py "
                    "certifies PHYSICAL_ACCEPTANCE_PASS."
                ),
                "checkpoint_02_path": str(chkpt_path),
                "specification": spec
            }

        r3_report = json.loads(r3_report_path.read_text(encoding="utf-8"))
        if r3_report.get("acceptance_decision") != "PHYSICAL_ACCEPTANCE_PASS" and not r3_report.get("verification_passed", False):
            return {
                "eligible_for_submission": False,
                "status": "NO_SUBMISSION_FALLBACK",
                "block_reason": "R3_PHYSICAL_ACCEPTANCE_FAILED",
                "explanation": "Package 163-R3 acceptance report recorded non-passing decision: %s" % r3_report.get("acceptance_decision"),
                "specification": spec
            }

        # Verify C4-R8 Reference Acceptance Report
        r8_report_path = None
        if r8_report_override is not None:
            r8_report_path = Path(r8_report_override)
        elif C4_R8_ACCEPTANCE_REPORT_PRIMARY.exists():
            r8_report_path = C4_R8_ACCEPTANCE_REPORT_PRIMARY
        elif C4_R8_ACCEPTANCE_REPORT_FALLBACK.exists():
            r8_report_path = C4_R8_ACCEPTANCE_REPORT_FALLBACK

        if r8_report_path is None or not r8_report_path.exists():
            return {
                "eligible_for_submission": False,
                "status": "NO_SUBMISSION_FALLBACK",
                "block_reason": "C4_R8_REFERENCE_REPORT_MISSING",
                "explanation": (
                    "Stage C2-2 requires authentic independent C4-R8 reference at uy = 0.0018703125442191958 mm "
                    "(Job 1419490.mmaster02). While Job 1419490 is running or its acceptance report is missing, "
                    "Stage C2-2 submission is withheld."
                ),
                "checkpoint_02_path": str(chkpt_path),
                "r3_acceptance_report": str(r3_report_path),
                "running_reference_job_id": ACTIVE_REFERENCE_JOB_ID,
                "specification": spec
            }

        r8_report = json.loads(r8_report_path.read_text(encoding="utf-8"))
        if r8_report.get("acceptance_decision") != "PHYSICAL_ACCEPTANCE_PASS" and not r8_report.get("verification_passed", False):
            return {
                "eligible_for_submission": False,
                "status": "NO_SUBMISSION_FALLBACK",
                "block_reason": "C4_R8_REFERENCE_ACCEPTANCE_FAILED",
                "explanation": "Package 157-R8 acceptance report recorded non-passing decision: %s" % r8_report.get("acceptance_decision"),
                "specification": spec
            }

        # Both predecessors fully pass physical acceptance!
        return {
            "eligible_for_submission": True,
            "status": "ELIGIBLE_FOR_ASSEMBLY_AND_PREFLIGHT",
            "checkpoint_02_path": str(chkpt_path),
            "r3_acceptance_report": str(r3_report_path),
            "c4_r8_acceptance_report": str(r8_report_path),
            "specification": spec
        }

    except Exception as e:
        return {
            "eligible_for_submission": False,
            "status": "NO_SUBMISSION_FALLBACK",
            "block_reason": "CHECKPOINT_02_READ_ERROR: " + str(e),
            "specification": spec
        }


if __name__ == "__main__":
    result = evaluate_c2_2_submission_eligibility()
    print(json.dumps(result, indent=2))

