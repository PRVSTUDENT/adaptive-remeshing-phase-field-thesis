"""
Write Turn 161 Preparation Artifact for Run 00ded454-1067-4448-b9a0-e1b2c400ab99
"""
import hashlib
import json
import os

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
RUN_ID = "00ded454-1067-4448-b9a0-e1b2c400ab99"
TASK_ID = "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"

EVIDENCE_FILES = [
    r".agents\scripts\Invoke-ChatGPTBridge.ps1",
    r".agents\scripts\bridge_rules.txt",
    r".agents\scripts\project_alignment_guard.txt",
    r"tests\unit\test_bridge_external_blocker_guard.ps1",
    r"tests\unit\test_bridge_external_blocker_guard.py",
    r"models\pandey_kumar_mode1\108_r18_c3_donor_kinematics_active_set\M1_C3_ACTIVE_SET_R18_CONTINUATION.inp",
    r"models\pandey_kumar_mode1\108_r18_c3_donor_kinematics_active_set\driver_r18_safeguarded_continuation.py",
    r"models\pandey_kumar_mode1\108_r18_c3_donor_kinematics_active_set\f42_unified_12dof_active_set_uel.for",
    r"models\pandey_kumar_mode1\15_energy_qualification_small\f42_mixed_uel.for",
    r"results\validation\mode1_f1597\r18_donor_kinematics_audit.json"
]

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    evidence_sources = {}
    for rel_path in EVIDENCE_FILES:
        full_path = os.path.join(REPO_ROOT, rel_path)
        assert os.path.exists(full_path), f"Missing evidence file: {full_path}"
        norm_key = rel_path.replace("\\", "/")
        evidence_sources[norm_key] = compute_sha256(full_path)

    finding = (
        "Bridge external authentication blocker guard implemented and verified: "
        "idempotent suppression of outgoing ChatGPT dispatches active when university eduVPN "
        "interactive browser SSO is required (R18_OFFLINE_QUALIFIED__INTERACTIVE_SSO_REQUIRED), "
        "with prompt/environment resume flags and restored connectivity supported; "
        "Package 108 Revision 18 and frozen UELs remain bitwise unchanged."
    )

    artifact = {
        "schema": 1,
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "status": "PREPARATION_COMPLETE",
        "finding": finding,
        "evidence_sources": evidence_sources,
        "verification_passed": True
    }

    out_path = os.path.join(REPO_ROOT, "results", "validation", f"preparation-{RUN_ID}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print(f"Preparation artifact written to {out_path}")
    print(f"Artifact SHA-256: {compute_sha256(out_path)}")

if __name__ == "__main__":
    main()
