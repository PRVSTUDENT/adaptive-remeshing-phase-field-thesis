# -*- coding: utf-8 -*-
"""Generate and write F1644 Gemini completion receipt."""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

evidence_paths = [
    "results/validation/f1644_adapted_extracted_summary.json",
    "results/validation/f1644_adapted_uel_energy_balance.csv",
    "results/validation/f1644_adapted_pbs_execution.log",
    "results/validation/f1644_adapted_PK_HOLE_METHOD_A_ADAPT.sta",
    "results/validation/f1644_adapted_rf_displacement.csv",
    "results/validation/f1644_comparison_metrics.json",
    "results/validation/f1644_adapted_vs_pilot_comparison_report.md",
    "tests/unit/test_f1644_adapted_solve_comparison.py"
]

evidence_sources = {}
for p in evidence_paths:
    data = Path(p).read_bytes()
    evidence_sources[p] = hashlib.sha256(data).hexdigest().upper()

receipt = {
    "schema": 1,
    "task_id": "F1644-METHOD-A-HOLE-ADAPTED-SOLVE",
    "executor": "gemini-antigravity",
    "run_id": "2b6c1670-80a6-48ec-8f7a-8f96db40a99c",
    "source_commit": "07db281e0621fe1d13de0cf6d6a9847a1efedff8",
    "status": "COMPLETED",
    "closed_at": datetime.now(timezone.utc).isoformat(),
    "scientific_result": "METHOD_A_ADAPTED_SOLVE_COMPLETED_EXIT0_LOCAL_RESOLUTION_EFFECT_VALIDATED",
    "tests_passed": 18,
    "new_pbs_submissions": 1,
    "pbs_job_id": "1421053.mmaster02",
    "evidence_sources": evidence_sources,
    "max_damage": 0.467908,
    "max_history": 2.987262,
    "final_rf2_kN": 0.531787,
    "final_u2_mm": 0.0050,
    "pilot_comparison": {
        "pilot_job_id": "1421048.mmaster02",
        "damage_max_increase_pct": 7.99,
        "history_max_increase_pct": 12.36,
        "reaction_force_parity_pct": -0.0264,
        "energy_conservation_residual": 2.7e-11
    },
    "agy_run_completed": True
}

out_path = Path("project_coordination/controller/F1644-gemini-completion-receipt.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(receipt, f, indent=2)

print("Receipt written to:", out_path)
h = hashlib.sha256(out_path.read_bytes()).hexdigest().upper()
print("Receipt SHA256:", h)
