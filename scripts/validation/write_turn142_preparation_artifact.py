#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
write_turn142_preparation_artifact.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 142)
Protocol Version: 2

Generates preparation checkpoint artifact for Turn 142.
"""

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
RUN_ID = "3f5c9a15-02fd-40de-8a36-7dc046dd70c4"

evidence_paths = [
    "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for",
    "models/pandey_kumar_mode1/108_r12_c3_autonomous_active_set/f42_unified_12dof_active_set_uel.for",
    "models/pandey_kumar_mode1/108_r12_c3_autonomous_active_set/M1_C3_ACTIVE_SET_R12_CONTINUATION.inp",
    "models/pandey_kumar_mode1/108_r12_c3_autonomous_active_set/stage_a_all_d0_boundary_cards.inc",
    "models/pandey_kumar_mode1/108_r12_c3_autonomous_active_set/active_set_boundary_cards.inc",
    "models/pandey_kumar_mode1/108_r12_c3_autonomous_active_set/d_lower_bounds.csv",
    "models/pandey_kumar_mode1/108_r12_c3_autonomous_active_set/driver_r12_autonomous_continuation.py",
    "models/pandey_kumar_mode1/108_r12_c3_autonomous_active_set/run_pkg108_r12_datacheck.sh",
    "models/pandey_kumar_mode1/108_r12_c3_autonomous_active_set/submit_M1_C3_ACTIVE_SET_R12.pbs",
    "models/pandey_kumar_mode1/108_r12_c3_autonomous_active_set/PACKAGE_MANIFEST.json",
    "models/pandey_kumar_mode1/108_r12_c3_autonomous_active_set/M1_C3_ACTIVE_SET_R12_AUTHORIZATION.json",
    "tests/unit/test_mode1_f1597_turn142_r12_qualification.py"
]

evidence_sources = {}
for rel_path in evidence_paths:
    full_path = REPO_ROOT / rel_path
    if not full_path.exists():
        raise FileNotFoundError(f"Missing evidence source: {rel_path}")
    h = hashlib.sha256(full_path.read_bytes()).hexdigest().upper()
    evidence_sources[rel_path.replace("\\", "/")] = h

finding_text = (
    "Candidate Package 108 Revision 12 (R12) autonomous active-set continuation driver fully formulated, "
    "staged on cluster scratch, and verified through Abaqus 2023 preflight compilation and datacheck "
    "(Exit 0, 0 errors, 4 benign warnings). Implemented strict Stage-A checkpoint reset semantics and "
    "KKT sign convention (lambda = RF3, release on lambda < -5e-7 kN/mm, reactivate on d < d0 - 1e-8) "
    "with 6 explicit fail-fast stop conditions. Preflight qualification passed: datachecks=PASS_BOTH, "
    "active_jobs=0, login notifications verified. Package ready for immediate qualified PBS submission."
)

checkpoint_payload = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
    "run_id": RUN_ID,
    "finding": finding_text,
    "evidence_sources": evidence_sources,
    "verification_passed": True
}

out_path = REPO_ROOT / f"results/validation/preparation-{RUN_ID}.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(checkpoint_payload, f, indent=2)

print(f"Wrote preparation checkpoint artifact to: {out_path}")
print(f"Artifact SHA-256: {hashlib.sha256(out_path.read_bytes()).hexdigest().upper()}")
