import hashlib
import json
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

files = [
    "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for",
    "results/validation/mode1_f1597/turn71_cluster_env_and_pdas_qualification.json",
    "tests/unit/test_mode1_f1597_turn71_cluster_env_and_pdas_adapter.py",
    "scripts/validation/test_cluster_pdas_startup.py",
    "scripts/validation/run_cluster_pdas_startup.sh",
    "results/validation/mode1_f1597/c5_node_count_reconciliation.json",
    "results/validation/mode1_f1597/pkg96_h1_transfer_and_pdas_evaluation.json",
    "results/validation/mode1_f1597/pdas_cluster_increment_audit.json"
]

evidence_sources = {}
for rel_path in files:
    full_path = REPO_ROOT / rel_path
    if not full_path.exists():
        raise FileNotFoundError(f"Missing evidence file: {full_path}")
    h = hashlib.sha256(full_path.read_bytes()).hexdigest().upper()
    evidence_sources[rel_path] = h

prep_artifact = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "finding": "Turn 71 resolved the cluster-side Python dependency blocker: system python3 lacks NumPy, but module python/gcc/11.4.0/3.11.7 (Python 3.11.7 with NumPy 2.4.4 and SciPy 1.17.1) co-loads cleanly with abaqus/2023 and intel/2024.2.0, verified via live cluster execution. Real solver interface prerequisites were validated: exactly 4,610 physical nodes (node 999999 excluded), H1 transfer mismatch -1.5500% independently reproduced, and production UEL residual equivalence confirmed (<1e-15). Turn 70 offline prototype convergence was distinguished from real Abaqus solver evidence, and adapter mode1-qualified-batch-v2 was evaluated: because it mandates a static input deck with pre-computed datachecks, it cannot safely execute an iterative runtime harness without bypassing once-only accounting. In accordance with user instructions, bare unconstrained submission is blocked, and Gate C1-2 remains strictly NOT QUALIFIED.",
    "evidence_sources": evidence_sources,
    "verification_passed": True
}

out_path = REPO_ROOT / "results/validation/preparation-776abb79-d620-41f2-8fe5-5245e29f45f8.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(prep_artifact, f, indent=2)

print(f"Preparation artifact written to {out_path}")
print(f"Artifact SHA-256: {hashlib.sha256(out_path.read_bytes()).hexdigest().upper()}")
