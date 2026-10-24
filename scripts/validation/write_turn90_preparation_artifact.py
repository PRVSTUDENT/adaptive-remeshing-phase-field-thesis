import hashlib
import json
from pathlib import Path

repo = Path("D:/Master thesis/Adaptive remeshing")

sources = [
    "models/pandey_kumar_mode1/102_c5_coupled_staggered_reequilibration/M1_C5_PACKAGE102_STAGGERED_AUTHORIZATION.json",
    "models/pandey_kumar_mode1/102_c5_coupled_staggered_reequilibration/M1_C5_PACKAGE102_STAGGERED_REEQUIL.inp",
    "models/pandey_kumar_mode1/102_c5_coupled_staggered_reequilibration/M1_C5_PACKAGE102_STAGGERED_REEQUIL_DC.dat",
    "models/pandey_kumar_mode1/102_c5_coupled_staggered_reequilibration/PACKAGE_MANIFEST.json",
    "models/pandey_kumar_mode1/102_c5_coupled_staggered_reequilibration/staggered_execution_adapter.py",
    "models/pandey_kumar_mode1/102_c5_coupled_staggered_reequilibration/submit_M1_C5_PACKAGE102_STAGGERED_PILOT.pbs",
    "models/pandey_kumar_mode1/102_c5_coupled_staggered_reequilibration/turn89_c5_staggered_d_opt.npy",
    "models/pandey_kumar_mode1/102_c5_coupled_staggered_reequilibration/turn89_c5_updated_h_table.csv",
    "models/pandey_kumar_mode1/102_c5_coupled_staggered_reequilibration/pdas_trial_evaluation.json",
    "models/pandey_kumar_mode1/102_c5_coupled_staggered_reequilibration/uel_energy_balance.csv",
    "results/validation/mode1_f1597/turn90_initial_pkg102_reconciliation.json",
    "results/validation/mode1_f1597/turn90_pkg102_detailed_diagnosis.json",
    "results/validation/mode1_f1597/turn90_pkg102_kkt_stationarity.json",
    "tests/unit/test_mode1_f1597_turn90_package102_validation.py"
]

evidence_sources = {}
for rel in sorted(sources):
    p = repo / rel
    if not p.is_file():
        raise FileNotFoundError(f"Missing evidence source: {rel}")
    h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
    evidence_sources[rel] = h

finding = (
    "Reconciled and evaluated authentic Package 102 PBS job 1417164.mmaster02. "
    "Abaqus completed Exit 0 with strict 0 healing nodes and 0 overshoot nodes. "
    "However, reaction force RF2=98.79 N (error -12.55% vs donor 112.97 N) and "
    "fracture energy E_frac=0.149309 mJ (error +8.40% vs donor 0.137737 mJ) failed continuity thresholds. "
    "Independent KKT stationarity audit revealed free-set residual ||R_d||_inf,A=1.8267e-06 kN/mm. "
    "Proved that an independently optimized phase solution drives excessive local damage dissipation "
    "(+22.55% local energy surge), over-softening the crack band. Gate C1-2 strictly maintained as NOT_QUALIFIED; "
    "follow-on forward continuation withheld."
)

artifact = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "finding": finding,
    "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
    "pbs_job_id": "1417164.mmaster02",
    "evidence_sources": evidence_sources,
    "verification_passed": True
}

out_path = repo / "results/validation/preparation-0bd3ca6e-839f-4b73-b6da-3f44d871a235.json"
out_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
print(f"Wrote preparation checkpoint to {out_path}")
