import hashlib
from pathlib import Path

repo = Path("D:/Master thesis/Adaptive remeshing")
artifacts = [
    "results/validation/mode1_f1597/turn90_initial_pkg102_reconciliation.json",
    "results/validation/mode1_f1597/turn90_pkg102_detailed_diagnosis.json",
    "results/validation/mode1_f1597/turn90_pkg102_kkt_stationarity.json",
    "results/validation/preparation-0bd3ca6e-839f-4b73-b6da-3f44d871a235.json",
    "project_coordination/sessions/2026-10-24_gemini-antigravity_F1597_0bd3ca6e-839f-4b73-b6da-3f44d871a235.md"
]

registry_path = repo / "project_coordination/ARTIFACT_REGISTRY.csv"
with open(registry_path, "a", encoding="utf-8") as f:
    for a in artifacts:
        p = repo / a
        h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
        f.write(f'"{Path(a).stem}","Mode-I","{a}","verified_diagnostic_evidence","verified","gemini-antigravity","7713e875fc66e8c87d9c2501310c0478386cd20e","{h}","","Turn 90 Package 102 coupled-state validation evidence"\n')
print(f"Appended {len(artifacts)} records to ARTIFACT_REGISTRY.csv")
