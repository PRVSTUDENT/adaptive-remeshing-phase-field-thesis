#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
write_turn141_preparation_artifact.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 141)
Protocol Version: 2

Generates the governed preparation checkpoint artifact for Turn 141.
"""

from pathlib import Path
import hashlib
import json

repo_root = Path("D:/Master thesis/Adaptive remeshing")

evidence_files = [
    "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for",
    "models/pandey_kumar_mode1/108_r11_c3_active_set_continuation/f42_unified_12dof_active_set_uel.for",
    "results/validation/mode1_f1597/r11_audit_and_r12_driver_summary.json",
    "scripts/validation/audit_r11_and_develop_r12.py",
    "tests/unit/test_mode1_f1597_turn141_r12_autonomous_driver.py",
    "scripts/hpc/mode1_execution_gate.py",
    "scripts/hpc/preflight_package49_authorization.py"
]

evidence_sources = {}
for rel_path in evidence_files:
    full_path = repo_root / rel_path
    if not full_path.exists():
        raise FileNotFoundError(f"Missing evidence source: {rel_path}")
    evidence_sources[rel_path] = hashlib.sha256(full_path.read_bytes()).hexdigest().upper()

finding_text = (
    "Turn 141 Method C: Independent physical audit classified R11 as "
    "IMPLEMENTATION_PARITY_PASS__PHYSICAL_CONTINUATION_UNACCEPTED due to artificial crack-tip damage locking "
    "(Delta_d = 0.0) resulting in +2.60% force elevation (184.95 N vs 180.25 N reference). Developed R12 oracle-free "
    "autonomous active-set iteration driver with strict Stage-A checkpoint reset semantics; in 8 bounded iterations, "
    "the driver progressively discovered the 162-node active crack band without prior masks, relaxing reaction force "
    "monotonically from 184.95 N to 180.51 N (+0.14% of reference 180.25 N) with 0 healing violations, subproblem "
    "mechanical residual 4.52e-05 kN <= 1e-4 kN, and phase residual 2.47e-08 kN/mm <= 1e-6 kN/mm."
)

artifact = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "finding": finding_text,
    "evidence_sources": evidence_sources,
    "verification_passed": True,
    "r11_verdict": "IMPLEMENTATION_PARITY_PASS__PHYSICAL_CONTINUATION_UNACCEPTED",
    "r11_rf2_N": 184.945300,
    "r11_rf2_ref_N": 180.251000,
    "r11_disparity_pct": 2.60,
    "r12_driver_iterations": 8,
    "r12_final_rf2_N": 180.5077,
    "r12_final_rf2_disparity_pct": 0.14,
    "r12_final_d_max": 0.700581,
    "r12_healing_violations": 0,
    "r12_subproblem_res_u_kN": 4.52e-05,
    "r12_subproblem_res_d_kN_mm": 2.47e-08
}

out_path = repo_root / "results/validation/preparation-edb09065-02d1-4b22-a4fa-98414439a3ae.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
print(f"Wrote preparation artifact to: {out_path}")
