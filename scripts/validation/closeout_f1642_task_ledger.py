# -*- coding: utf-8 -*-
"""Update TASK_LEDGER.csv for F1642 completion."""
from pathlib import Path

p = Path("project_coordination/TASK_LEDGER.csv")
lines = p.read_text(encoding="utf-8").splitlines()

new_lines = []
for line in lines:
    if line.startswith('"F1642-METHOD-A-HOLE-PHYSICAL-STATE-PILOT-EXECUTION"') and '"ready"' in line:
        new_lines.append('"F1642-METHOD-A-HOLE-PHYSICAL-STATE-PILOT-EXECUTION","Mode-I","Qualify and execute one real Abaqus 2023 HPC diagnostic physical-state-acquisition pilot for off-axis hole model","completed","gemini-antigravity","d04a699b662fe213cbfbc61737be74a62174c81a","","project_coordination;models/pandey_kumar_mode1/176_method_a_plate_with_hole;scripts/hpc;scripts/validation;tests/unit;results/validation","","COUPLED_PHASE_FIELD_PILOT_COMPLETED_EXIT0_6_TESTS_PASS","F1643-METHOD-A-HOLE-ADAPTIVE-REFINEMENT-CRITERIA","2026-11-06T22:05:00.0000000+00:00"')
    else:
        new_lines.append(line)

p.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
print("TASK_LEDGER.csv closed out for F1642 successfully.")
