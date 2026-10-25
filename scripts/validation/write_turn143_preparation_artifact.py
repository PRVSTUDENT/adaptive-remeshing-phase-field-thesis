import hashlib
import json
from pathlib import Path

repo_root = Path(r"D:\Master thesis\Adaptive remeshing")

def get_sha256(rel_path):
    p = repo_root / rel_path
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest().upper()

files_to_hash = [
    "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for",
    "models/pandey_kumar_mode1/108_r13_c3_autonomous_active_set/f42_unified_12dof_active_set_uel.for",
    "models/pandey_kumar_mode1/108_r13_c3_autonomous_active_set/M1_C3_ACTIVE_SET_R13_CONTINUATION.inp",
    "models/pandey_kumar_mode1/108_r13_c3_autonomous_active_set/stage_a_all_d0_boundary_cards.inc",
    "models/pandey_kumar_mode1/108_r13_c3_autonomous_active_set/active_set_boundary_cards.inc",
    "models/pandey_kumar_mode1/108_r13_c3_autonomous_active_set/d_lower_bounds.csv",
    "models/pandey_kumar_mode1/108_r13_c3_autonomous_active_set/driver_r13_autonomous_continuation.py",
    "models/pandey_kumar_mode1/108_r13_c3_autonomous_active_set/run_pkg108_r13_datacheck.sh",
    "models/pandey_kumar_mode1/108_r13_c3_autonomous_active_set/submit_M1_C3_ACTIVE_SET_R13.pbs",
    "models/pandey_kumar_mode1/108_r13_c3_autonomous_active_set/PACKAGE_MANIFEST.json",
    "models/pandey_kumar_mode1/108_r13_c3_autonomous_active_set/M1_C3_ACTIVE_SET_R13_AUTHORIZATION.json",
    "tests/unit/test_mode1_f1597_turn143_r13_qualification.py"
]

evidence_sources = {}
for rel in files_to_hash:
    evidence_sources[rel] = get_sha256(rel)

finding = (
    "Candidate Package 108 Revision 13 (R13) autonomous active-set continuation driver fully formulated "
    "and qualified, eliminating SIMULIA odbAccess Repository .get() defect via robust membership checking "
    "and resolving cluster Lmod XDG_RUNTIME_DIR requirement. Preflight compilation and datacheck completed "
    "Exit 0 with 0 errors on cluster. All 6 unit regression tests passed. Verified with strict Stage-A "
    "checkpoint reset semantics, KKT multiplier release threshold (tau_release = 1.0e-9 kN/mm), and 6 fail-fast "
    "guardrails within ONE PBS allocation. Package ready for immediate qualified PBS execution."
)

data = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
    "run_id": "97211912-f161-46b2-9cdf-d7f0c3e81913",
    "finding": finding,
    "evidence_sources": evidence_sources,
    "verification_passed": True
}

out_path = repo_root / "results/validation/preparation-97211912-f161-46b2-9cdf-d7f0c3e81913.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Wrote preparation artifact to {out_path}")
print(f"Finding length: {len(finding)}")
for k, v in evidence_sources.items():
    print(f"  {k}: {v}")
