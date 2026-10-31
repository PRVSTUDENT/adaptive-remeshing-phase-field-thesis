# -*- coding: utf-8 -*-
"""
test_repaired_extractor.py
Test the repaired extract_package148_iteration.py against authentic ODBs on the cluster.
Verifies:
1. Authentic extraction on Package 150 Step 1 mechanical ODB (Job 1418949)
2. Backward-compatible extraction on Package 148 C1-1 authentic ODB (Job 1418939)
3. Strict error rejection on invalid step identity
"""

import os
import sys
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SSH_CONFIG = Path.home() / ".ssh/codex_config"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c4_package150_c1_2_continuation"
REMOTE_R8_DIR = "/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r8"


def run_guarded_ssh(cmd, timeout=180):
    ps_cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(REPO_ROOT / ".agents/scripts/Invoke-GuardedSsh.ps1"),
        "-RemoteCommand",
        cmd,
        "-TimeoutSeconds",
        str(timeout),
    ]
    res = subprocess.run(ps_cmd, cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError("Guarded SSH failed (exit %d): %s\n%s" % (res.returncode, res.stderr, res.stdout))
    return res.stdout


def scp_file(local_path, remote_path):
    cmd = [
        "scp.exe",
        "-F",
        str(SSH_CONFIG),
        "-B",
        "-o",
        "BatchMode=yes",
        str(local_path),
        "tu_freiberg:%s" % remote_path,
    ]
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError("SCP failed (exit %d): %s\n%s" % (res.returncode, res.stderr, res.stdout))


def test_repaired_extractor():
    print("Step 1: Uploading repaired extractor to cluster runtime...")
    local_extractor = REPO_ROOT / "scripts/validation/extract_package148_iteration.py"
    remote_extractor = "%s/runtime/scripts/validation/extract_package148_iteration.py" % REMOTE_RUN_DIR
    scp_file(local_extractor, remote_extractor)

    print("Step 2: Executing extraction on authentic Package 150 mechanical ODB (Job 1418949)...")
    p150_mech_dir = "%s/continuation_1418949.mmaster02/P150_S1_01_00_mechanical" % REMOTE_RUN_DIR
    p150_odb = "%s/P150_S1_01_00_mechanical.odb" % p150_mech_dir
    p150_test_out = "%s/test_endpoint_repaired.json" % p150_mech_dir

    module_init = "source /etc/profile.d/lmod.sh 2>/dev/null || true; module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 2>/dev/null || true; "

    extract_cmd = (
        module_init +
        "rm -f %s && "
        "abaqus python %s "
        "--odb %s "
        "--output %s "
        "--physical-nodes 7265 "
        "--physical-elements 7056"
    ) % (p150_test_out, remote_extractor, p150_odb, p150_test_out)
    
    out = run_guarded_ssh(extract_cmd, timeout=120)
    print("Extraction output:", out.strip())

    print("Step 3: Validating extracted Package 150 endpoint...")
    cat_cmd = "cat %s" % p150_test_out
    endpoint_json_str = run_guarded_ssh(cat_cmd, timeout=60)
    # Parse json (stripping any openssh warning lines)
    json_lines = [l for l in endpoint_json_str.splitlines() if not l.startswith("**")]
    endpoint_data = json.loads("\n".join(json_lines))

    assert endpoint_data["schema"] == 1, "Schema mismatch"
    assert endpoint_data["step_name"] == "C1_2_Step1", "Step name mismatch: %s" % endpoint_data.get("step_name")
    assert len(endpoint_data["nodes"]) == 7265, "Expected 7265 nodes, got %d" % len(endpoint_data["nodes"])
    assert "rf2_kN" in endpoint_data, "Missing rf2_kN"
    assert "rp_u2" in endpoint_data, "Missing rp_u2"
    assert "elastic_kNmm" in endpoint_data, "Missing elastic_kNmm"
    assert "fracture_kNmm" in endpoint_data, "Missing fracture_kNmm"
    
    print("P150 Extracted Physical Properties:")
    print("  Step Name:       %s" % endpoint_data["step_name"])
    print("  Prescribed uy:   %.9f mm" % endpoint_data["rp_u2"])
    print("  Reaction Force:  %.6f kN" % endpoint_data["rf2_kN"])
    print("  Elastic Energy:  %.6e kN-mm" % endpoint_data["elastic_kNmm"])
    print("  Fracture Energy: %.6e kN-mm" % endpoint_data["fracture_kNmm"])
    print("  Node Count:      %d" % len(endpoint_data["nodes"]))

    print("Step 4: Testing backward compatibility on Package 148 C1-1 ODB...")
    r8_odb = "%s/coupled_1418939.mmaster02/P148_01_00_mechanical/P148_01_00_mechanical.odb" % REMOTE_R8_DIR
    r8_out = "/tmp/test_r8_endpoint.json"
    r8_extract_cmd = (
        module_init +
        "rm -f %s && "
        "abaqus python %s "
        "--odb %s "
        "--output %s "
        "--physical-nodes 7265 "
        "--physical-elements 7056"
    ) % (r8_out, remote_extractor, r8_odb, r8_out)
    r8_out_res = run_guarded_ssh(r8_extract_cmd, timeout=120)
    print("R8 Backward Compatibility Output:", r8_out_res.strip())
    r8_cat = run_guarded_ssh("cat %s && rm -f %s" % (r8_out, r8_out), timeout=60)
    r8_json_lines = [l for l in r8_cat.splitlines() if not l.startswith("**")]
    r8_data = json.loads("\n".join(r8_json_lines))
    assert r8_data["step_name"] == "C1-1-ReEquil", "R8 step name mismatch: %s" % r8_data.get("step_name")
    print("R8 Backward Compatibility PASS: Step = %s, RF2 = %.6f kN" % (r8_data["step_name"], r8_data["rf2_kN"]))

    print("Step 5: Testing strict error rejection on invalid step identity...")
    invalid_step_cmd = (
        module_init +
        "abaqus python %s "
        "--odb %s "
        "--output /tmp/should_fail.json "
        "--physical-nodes 7265 "
        "--physical-elements 7056 "
        "--step NonExistentStep 2>&1 || true"
    ) % (remote_extractor, p150_odb)
    invalid_res = run_guarded_ssh(invalid_step_cmd, timeout=60)
    print("Invalid step rejection test output:\n", invalid_res.strip())
    assert "Specified step not found in ODB" in invalid_res, "Failed to reject invalid step"
    print("Invalid Step Rejection PASS")

    # Record verified test evidence locally
    evidence_file = REPO_ROOT / "results/validation/package150_repaired_extractor_evidence.json"
    evidence_data = {
        "schema": 1,
        "status": "EXTRACTOR_REPAIR_VERIFIED",
        "p150_mechanical_step1": {
            "odb_path": p150_odb,
            "step_name": endpoint_data["step_name"],
            "increment": endpoint_data["increment"],
            "step_time": endpoint_data["step_time"],
            "rp_u2_mm": endpoint_data["rp_u2"],
            "rf2_kN": endpoint_data["rf2_kN"],
            "elastic_kNmm": endpoint_data["elastic_kNmm"],
            "fracture_kNmm": endpoint_data["fracture_kNmm"],
            "nodes_extracted": len(endpoint_data["nodes"]),
            "odb_sha256": endpoint_data["odb_sha256"],
            "extractor_sha256": endpoint_data["extractor_sha256"]
        },
        "backward_compatibility": "PASS_C1_1_ReEquil",
        "error_rejection": "PASS_STRICT_STEP_VALIDATION",
        "timestamp": "2026-10-31T08:35:00Z"
    }
    evidence_file.write_text(json.dumps(evidence_data, indent=2) + "\n")
    print("Test evidence recorded at:", evidence_file)
    return evidence_data


if __name__ == "__main__":
    test_repaired_extractor()
