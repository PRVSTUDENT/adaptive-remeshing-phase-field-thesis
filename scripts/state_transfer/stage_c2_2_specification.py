# -*- coding: utf-8 -*-
"""
stage_c2_2_specification.py
Mode-I Method C Cycle 2: Stage C2-2 (+5 nm Forward Continuation) Specification and Predecessor Guard.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2

Defines the mathematical, physical, and computational specifications for Stage C2-2
forward continuation on the Candidate C5 mesh, resolves the C2-2 preparation ambiguity,
and implements the mandatory no-submission fallback when Predecessor Checkpoint 02 is pending.

Ambiguity Resolution:
1. Predecessor State: Strictly bound to Checkpoint 02 (converged at uy = 0.0018653125442191958 mm
   from Job 1419489.mmaster02 / Package 163-R2). Never starts from Checkpoint 01 or synthetic state.
2. Step Scope: In-mesh forward continuation on existing C5 mesh (12,996 CPE4 elements, 13,278 nodes,
   51,984 integration points). No spatial interpolation or remeshing in this stage.
3. Stepping Schedule:
   - Initial displacement: uy_initial = 0.0018653125442191958 mm
   - Forward increment:    Delta_uy   = +0.0000050000000000000 mm (+5.0 nm)
   - Target displacement:  uy_target  = 0.0018703125442191958 mm
4. Staggered PDAS Solver:
   - Max outer iterations: 200 (preserving the contraction headroom established in Package 163-R2)
   - Tolerances: Delta_d <= 1e-5, Delta_u <= 1e-9 mm, Delta_H <= 1e-4 MPa
   - KKT tolerances: dual error <= 1e-6 kN*mm, free residual <= 1e-6 kN
   - Invariants: strict zero healing (healing >= -1e-6), monotone history (Delta_H >= 0.0)
   - Frozen UEL: SHA-256 CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6
5. No-Submission Fallback:
   - If Checkpoint 02 is absent or unverified on disk (e.g. while Job 1419489 is computing),
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
CHECKPOINT_02_EXPECTED_PATH = REPO_ROOT / "models/pandey_kumar_mode1/163_c5_package163_r2_c2_1_continuation/evidence/1419489.mmaster02/converged_checkpoint_02.json"
CHECKPOINT_02_FALLBACK_PATH = REPO_ROOT / "models/pandey_kumar_mode1/163_c5_package163_r2_c2_1_continuation/converged_checkpoint_02.json"


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
        "frozen_uel_sha256": FROZEN_UEL_SHA256,
        "resource_allocation": {
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "queue": "entry_imfdfkmq"
        }
    }


def evaluate_c2_2_submission_eligibility():
    """
    Evaluate whether Stage C2-2 is eligible for PBS submission.
    Implements the strict Predecessor Guard:
    Returns (eligible: bool, status: str, details: dict).
    """
    spec = get_c2_2_specification()

    # Check for Checkpoint 02
    chkpt_path = None
    if CHECKPOINT_02_EXPECTED_PATH.exists():
        chkpt_path = CHECKPOINT_02_EXPECTED_PATH
    elif CHECKPOINT_02_FALLBACK_PATH.exists():
        chkpt_path = CHECKPOINT_02_FALLBACK_PATH

    if chkpt_path is None:
        return {
            "eligible_for_submission": False,
            "status": "NO_SUBMISSION_FALLBACK",
            "block_reason": "PREDECESSOR_CHECKPOINT_02_MISSING",
            "explanation": (
                "Stage C2-2 forward continuation strictly requires physically accepted Checkpoint 02 "
                "(uy = 0.0018653125442191958 mm) from Job 1419489.mmaster02. "
                "Because Job 1419489 is currently actively computing on mnode097, "
                "Checkpoint 02 does not yet exist. In accordance with project protocol, "
                "submission is withheld under the no-submission fallback until authentic R2 results are terminal."
            ),
            "running_predecessor_job_id": "1419489.mmaster02",
            "specification": spec
        }

    # If file exists, check contents
    try:
        data = json.loads(chkpt_path.read_text(encoding="utf-8"))
        uy = float(data.get("target_uy_mm", 0.0))
        if abs(uy - BASELINE_UY_MM) > 1e-12:
            return {
                "eligible_for_submission": False,
                "status": "NO_SUBMISSION_FALLBACK",
                "block_reason": "CHECKPOINT_02_LOAD_MISMATCH",
                "explanation": "Found checkpoint at uy=%r, expected %r" % (uy, BASELINE_UY_MM),
                "specification": spec
            }
        # Predecessor exists and matches load
        return {
            "eligible_for_submission": True,
            "status": "ELIGIBLE_FOR_ASSEMBLY_AND_PREFLIGHT",
            "checkpoint_02_path": str(chkpt_path),
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
