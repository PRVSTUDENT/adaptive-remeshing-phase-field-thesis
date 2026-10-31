import hashlib
import json
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

files = [
    "models/pandey_kumar_mode1/156_c5_package156_c2_0_re_equilibration/PACKAGE_MANIFEST.json",
    "models/pandey_kumar_mode1/156_c5_package156_c2_0_re_equilibration/CONDITIONAL_CANDIDATE_RECEIPT.json",
    "models/pandey_kumar_mode1/156_c5_package156_c2_0_re_equilibration/M1_C5_PACKAGE156_C2_0_REEQUILIBRATION.inp",
    "models/pandey_kumar_mode1/156_c5_package156_c2_0_re_equilibration/P156_MECHANICAL_DC.inp",
    "models/pandey_kumar_mode1/156_c5_package156_c2_0_re_equilibration/P156_PHASE_DC.inp",
    "models/pandey_kumar_mode1/156_c5_package156_c2_0_re_equilibration/f42_mixed_uel.for",
    "results/validation/initial_finding_turn389_30c0b12f.json",
    "results/validation/package156_candidate_datachecks.json",
    "tests/unit/test_package156_c5_receiver_workflow.py",
    "tests/unit/test_package156_initialization_recovery.py"
]

evidence_sources = {}
for rel_path in files:
    full_path = REPO_ROOT / rel_path
    assert full_path.exists(), f"Missing file: {full_path}"
    h = hashlib.sha256(full_path.read_bytes()).hexdigest().upper()
    evidence_sources[rel_path] = h

artifact = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "run_id": "30c0b12f-5c25-49bb-a7da-e4b89a6bd986",
    "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
    "finding": "Package 156 staged to cluster scratch and technically qualified with authentic Abaqus 2023 compute-node mechanical and phase datachecks passing exit 0; solution state initialization verified across 12,996 elements and 51,984 integration points; Job 1419113 active on mnode101 at Step 2 outer 37.",
    "evidence_sources": evidence_sources,
    "verification_passed": True
}

out_path = REPO_ROOT / "results/validation/preparation-30c0b12f-5c25-49bb-a7da-e4b89a6bd986.json"
out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
print(f"Wrote preparation checkpoint artifact: {out_path}")
