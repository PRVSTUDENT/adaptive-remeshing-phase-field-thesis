# -*- coding: utf-8 -*-
"""Update TASK_LEDGER.csv for F1641 completion and F1642 registration."""
import csv
from pathlib import Path

p = Path("project_coordination/TASK_LEDGER.csv")
lines = p.read_text(encoding="utf-8").splitlines()

new_lines = []
for line in lines:
    if line.startswith('"F1641-METHOD-A-HOLE-INDICATOR-PILOT-QUALIFICATION"') and '"ready"' in line:
        new_lines.append('"F1641-METHOD-A-HOLE-INDICATOR-PILOT-QUALIFICATION","Mode-I","Qualify one indicator-driven Method A hole mesh and bounded serial pilot","completed","codex","9a1f53aa26b6a8a9bea0fe2944ab56076aac54ca","d04a699b662fe213cbfbc61737be74a62174c81a","project_coordination;scripts/remeshing;scripts/validation;tests/unit;results/validation;models/pandey_kumar_mode1/176_method_a_plate_with_hole","","C_PHYSICAL_DOMAIN_ASSESSED_ADVANCE_TO_EXECUTION_PILOT","F1642-METHOD-A-HOLE-PHYSICAL-STATE-PILOT-EXECUTION","2026-11-06T20:42:10.2982140+00:00"')
    else:
        new_lines.append(line)

f1642_entry = '"F1642-METHOD-A-HOLE-PHYSICAL-STATE-PILOT-EXECUTION","Mode-I","Qualify and execute one real Abaqus 2023 HPC diagnostic physical-state-acquisition pilot for off-axis hole model","ready","gemini-antigravity","d04a699b662fe213cbfbc61737be74a62174c81a","","project_coordination;models/pandey_kumar_mode1/176_method_a_plate_with_hole;scripts/hpc;scripts/validation;tests/unit","","TECHNICAL_PREFLIGHT_PASS_READY_FOR_SUBMISSION","","2026-11-06T21:15:00.0000000+00:00"'
if not any(l.startswith('"F1642-METHOD-A-HOLE-PHYSICAL-STATE-PILOT-EXECUTION"') for l in new_lines):
    new_lines.append(f1642_entry)

p.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
print("TASK_LEDGER.csv updated successfully.")
