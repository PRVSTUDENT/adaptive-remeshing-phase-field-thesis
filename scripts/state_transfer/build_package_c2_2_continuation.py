# -*- coding: utf-8 -*-
"""
build_package_c2_2_continuation.py
Builder and Preflight for Mode-I Method C Stage C2-2 (+5 nm Continuation on C5 Mesh).
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2

Prepares candidate Package 167 (Stage C2-2 Forward Continuation):
- Mesh: C5 (12,996 elements, 13,278 nodes, 51,984 integration points)
- Load increment: Advancing uy from 0.0018653125442191958 mm to 0.0018703125442191958 mm (+5.0 nm)
- Enforces strict authentic Checkpoint 02 binding from Package 163-R3 (Job 1419499.mmaster02)
- Rejects all disqualified Package 163-R2 artifacts (Job 1419489.mmaster02)
- Implements explicit Predecessor Guard: If Checkpoint 02 or C4 reference is absent, records NO_SUBMISSION_FALLBACK
"""

from __future__ import print_function, division
import json
import hashlib
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.stage_c2_2_specification import (
    get_c2_2_specification,
    evaluate_c2_2_submission_eligibility,
    BASELINE_UY_MM, TARGET_UY_MM, INCREMENT_UY_MM,
    FROZEN_UEL_SHA256, TOTAL_C5_NODES, TOTAL_C5_ELEMENTS,
    R3_RUN_DIR, ACTIVE_PREDECESSOR_JOB_ID, DISQUALIFIED_PREDECESSOR_JOB_IDS
)

PKG_167_DIR = REPO_ROOT / "models/pandey_kumar_mode1/167_c5_package167_c2_2_continuation"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c5_package167_c2_2_continuation"


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def build_c2_2_package(dry_run=True, checkpoint_override=None, r3_report_override=None, r8_report_override=None):
    """
    Attempt to build Package 167.
    Evaluates Dual Predecessor Guard first:
    If Checkpoint 02 is absent, unverified, or from R2, returns clean NO_SUBMISSION_FALLBACK status.
    """
    eligibility = evaluate_c2_2_submission_eligibility(
        checkpoint_override=checkpoint_override,
        r3_report_override=r3_report_override,
        r8_report_override=r8_report_override
    )
    if not eligibility["eligible_for_submission"]:
        return {
            "success": False,
            "status": "NO_SUBMISSION_FALLBACK",
            "reason": eligibility["block_reason"],
            "explanation": eligibility["explanation"],
            "package_path": str(PKG_167_DIR)
        }

    # If Checkpoint 02 and C4 reference are physically accepted, assemble package
    PKG_167_DIR.mkdir(parents=True, exist_ok=True)
    chkpt_path = Path(eligibility["checkpoint_02_path"])
    chkpt_data = json.loads(chkpt_path.read_text(encoding="utf-8"))

    # Sourced from Package 163-R3 active directory
    uel_src = R3_RUN_DIR / "f42_mixed_uel.for"
    uel_dst = PKG_167_DIR / "f42_mixed_uel.for"
    shutil.copyfile(uel_src, uel_dst)
    uel_hash = sha256_file(uel_dst)
    if uel_hash != FROZEN_UEL_SHA256:
        raise ValueError("UEL SHA-256 mismatch in C2-2 builder: " + uel_hash)

    # Copy notifications from R3
    notif_src = R3_RUN_DIR / "job_notifications.sh"
    notif_dst = PKG_167_DIR / "job_notifications.sh"
    shutil.copyfile(notif_src, notif_dst)

    return {
        "success": True,
        "status": "PACKAGE_ASSEMBLED_READY_FOR_PREFLIGHT",
        "package_path": str(PKG_167_DIR),
        "predecessor_checkpoint": str(chkpt_path),
        "predecessor_job_id": ACTIVE_PREDECESSOR_JOB_ID,
        "uel_sha256": uel_hash
    }


if __name__ == "__main__":
    res = build_c2_2_package()
    print(json.dumps(res, indent=2))

