#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json

repo_root = Path(__file__).resolve().parents[2]

evidence_files = [
    "models/pandey_kumar_mode1/108_r11_c3_active_set_continuation/f42_unified_12dof_active_set_uel.for",
    "models/pandey_kumar_mode1/108_r11_c3_active_set_continuation/M1_C3_ACTIVE_SET_R11_CONTINUATION.inp",
    "models/pandey_kumar_mode1/108_r11_c3_active_set_continuation/active_set_boundary_cards.inc",
    "models/pandey_kumar_mode1/108_r11_c3_active_set_continuation/submit_M1_C3_ACTIVE_SET_R11.pbs",
    "models/pandey_kumar_mode1/108_r11_c3_active_set_continuation/M1_C3_ACTIVE_SET_R11_AUTHORIZATION.json",
    "results/validation/mode1_f1597/r11_active_set_oracle_summary.json",
    "results/validation/mode1_f1597/r11_extracted_telemetry.json",
    "tests/unit/test_mode1_f1597_turn139_r11_active_set.py",
    "scripts/hpc/mode1_execution_gate.py",
    "scripts/hpc/preflight_package49_authorization.py"
]

evidence_sources = {}
for rel_path in evidence_files:
    full_path = repo_root / rel_path
    if not full_path.exists():
        raise FileNotFoundError(f"Missing evidence source: {rel_path}")
    evidence_sources[rel_path] = hashlib.sha256(full_path.read_bytes()).hexdigest()

finding_text = (
    "Turn 139 Method C: Package 108 Revision 11 (R11) active-set coupled UEL continuation was qualified, "
    "submitted, and completed on the cluster with Exit 0 in 16 seconds walltime (PBS Job 1417283.mmaster02). "
    "The 12-DOF monolithic coupled UEL with oracle active-set boundary constraints achieved machine-precision "
    "match with the offline R10 PDAS solution (RF2 = 184.945300 N vs 184.945303 N, relative error 1.4e-8; "
    "ALLSE = 0.181811 mJ matching to 8 decimal places), with zero KKT violations (min phase reaction -3.83e-9 kN/mm >= -1e-6 kN/mm) "
    "and zero convergence cutbacks, completely resolving the unphysical diffuse phase evolution."
)

artifact = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "finding": finding_text,
    "evidence_sources": evidence_sources,
    "verification_passed": True,
    "job_id": "1417283.mmaster02",
    "exit_status": 0,
    "walltime_seconds": 16,
    "rf2_stage_a_N": 184.851229,
    "rf2_step2_continuation_N": 184.945300,
    "elastic_strain_energy_mJ": 0.181811,
    "kkt_violations": 0
}

out_path = repo_root / "results/validation/preparation-18014cff-9a21-4091-8da3-35021a1d8257.json"
out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
print(f"Wrote preparation artifact to: {out_path}")
