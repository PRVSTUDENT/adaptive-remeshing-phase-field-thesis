import os

ledger_path = os.path.join("project_coordination", "TASK_LEDGER.csv")
with open(ledger_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith("F1747-CASE3-CONTRAST-TRANSFORMATION-PROTOTYPE"):
        new_lines.append(
            'F1747-CASE3-CONTRAST-TRANSFORMATION-PROTOTYPE,Method-A,"Task F1747: Case 3 (Sec 4.3) Geometry-Independent Nonlinear Indicator-Contrast Transformation Forensic Correction and Stress-Recovery Limitation Analysis: Reconciled Sizing Discrepancy (secondary h_min 0.67mm), Restored Spatial Gates, Identified 4.5mm Midspan Barrier and Outer Secondary Suppression, Zero PBS",completed_forensic_correction,gemini-antigravity,HEAD,HEAD,models/pandey_kumar_mode1/232_f1747_case3_contrast_prototype;scripts/remeshing;tests/unit;results/validation;results/figures;docs/validation;project_coordination;.agents,,HND_F1747_CASE3_AUTH_001_REJECT_EVALUATED_DISCREPANCY_RECONCILED_METHOD_A_LIMITATION_DEMONSTRATED_ZERO_PBS,CASE3_METHOD_A_LIMITATION_DEMONSTRATED,2026-11-14T21:30:00.0000000+01:00\n'
        )
    else:
        new_lines.append(line)

with open(ledger_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Updated TASK_LEDGER.csv successfully.")
