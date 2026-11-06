# -*- coding: utf-8 -*-
"""Register F1644 simulation, extraction, and comparison artifacts in ARTIFACT_REGISTRY.csv."""
import hashlib
from pathlib import Path

artifacts = [
    ("F1644-extracted-summary", "results/validation/f1644_adapted_extracted_summary.json", "EVIDENCE", "COMPLETED", "F1644 adapted simulation extracted physical summary JSON"),
    ("F1644-energy-balance-csv", "results/validation/f1644_adapted_uel_energy_balance.csv", "EVIDENCE", "COMPLETED", "F1644 adapted simulation UEL energy balance CSV"),
    ("F1644-pbs-execution-log", "results/validation/f1644_adapted_pbs_execution.log", "EVIDENCE", "COMPLETED", "F1644 adapted simulation PBS execution log (Exit Code 0)"),
    ("F1644-sta-file", "results/validation/f1644_adapted_PK_HOLE_METHOD_A_ADAPT.sta", "EVIDENCE", "COMPLETED", "F1644 adapted simulation Abaqus STA file (50 increments completed)"),
    ("F1644-rf-displacement-csv", "results/validation/f1644_adapted_rf_displacement.csv", "EVIDENCE", "COMPLETED", "F1644 adapted simulation reaction force vs displacement CSV"),
    ("F1644-comparison-metrics", "results/validation/f1644_comparison_metrics.json", "EVIDENCE", "COMPLETED", "F1644 matched comparison metrics between adapted and pilot models"),
    ("F1644-comparison-report", "results/validation/f1644_adapted_vs_pilot_comparison_report.md", "REPORT", "COMPLETED", "F1644 adapted vs pilot scientific comparison report"),
    ("F1644-extractor-script", "scripts/postprocessing/extract_method_a_hole_adapted.py", "SCRIPT", "READY", "F1644 Abaqus Python physical state extraction script"),
    ("F1644-comparison-script", "scripts/validation/compare_adapted_vs_pilot.py", "SCRIPT", "READY", "F1644 matched comparison evaluation script"),
    ("F1644-unit-test-suite", "tests/unit/test_f1644_adapted_solve_comparison.py", "TEST", "READY", "F1644 unit tests for simulation completion, bounds, and parity")
]

registry_path = Path("project_coordination/ARTIFACT_REGISTRY.csv")
lines_to_append = []

for art_id, rel_path, cat, status, desc in artifacts:
    p = Path(rel_path)
    if p.exists():
        h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
        line = f"{art_id},Mode-I,{rel_path},{cat},{status},gemini-antigravity,07db281e,{h},,{desc}\n"
        lines_to_append.append(line)
        print(f"Registered {art_id}: {h[:12]}...")

with open(registry_path, "a", encoding="utf-8") as f:
    f.writelines(lines_to_append)

print(f"Appended {len(lines_to_append)} entries to ARTIFACT_REGISTRY.csv")
