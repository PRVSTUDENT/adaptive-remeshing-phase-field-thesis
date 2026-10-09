"""
Unit test suite for Task F1385:
Mode-II Long-Walltime PBS Safeguard Submissions for Fixed-Mesh Convergence Study.
"""
import json
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def test_safeguard_manifests_consistency():
    fine_manifest_path = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode2", "07_fixed_mesh_convergence_suite",
        "04_fine_72k_h3p75um_72h", "manifest.json"
    )
    int_manifest_path = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode2", "07_fixed_mesh_convergence_suite",
        "03_intermediate_40k_h5um_48h", "manifest.json"
    )
    
    assert os.path.exists(fine_manifest_path), f"Missing fine safeguard manifest at {fine_manifest_path}"
    assert os.path.exists(int_manifest_path), f"Missing intermediate safeguard manifest at {int_manifest_path}"
    
    with open(fine_manifest_path, "r", encoding="utf-8") as f:
        fine_data = json.load(f)
    with open(int_manifest_path, "r", encoding="utf-8") as f:
        int_data = json.load(f)
        
    assert fine_data["job_name"] == "M2_FIX_FINE_72H"
    assert fine_data["requested_walltime"] == "72:00:00"
    assert fine_data["num_physical_quads"] == 71824
    assert fine_data["requested_cpus"] == 1
    assert fine_data["requested_memory"] == "16gb"
    assert fine_data["pbs_job_id"] == "1411557.mmaster02"
    assert fine_data["fortran_uel_sha256"] == "699B05D6C430FCE6242F8C603B45BB0783CF376451EFD52C56BC984B0CE71188"
    assert fine_data["submission_authorized"] is True

    assert int_data["job_name"] == "M2_FIX_INT_48H"
    assert int_data["requested_walltime"] == "48:00:00"
    assert int_data["num_physical_quads"] == 40000
    assert int_data["requested_cpus"] == 1
    assert int_data["requested_memory"] == "16gb"
    assert int_data["pbs_job_id"] == "1411558.mmaster02"
    assert int_data["fortran_uel_sha256"] == "699B05D6C430FCE6242F8C603B45BB0783CF376451EFD52C56BC984B0CE71188"
    assert int_data["submission_authorized"] is True

def test_hpc_job_ledger_safeguard_records():
    ledger_path = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")
    assert os.path.exists(ledger_path), f"Missing HPC ledger at {ledger_path}"
    
    with open(ledger_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "1411557.mmaster02" in content, "Job 1411557.mmaster02 missing from HPC_JOB_LEDGER.csv"
    assert "1411558.mmaster02" in content, "Job 1411558.mmaster02 missing from HPC_JOB_LEDGER.csv"
    assert "M2_FIX_FINE_72H" in content
    assert "M2_FIX_INT_48H" in content

def test_active_session_and_task_state():
    session_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_SESSION.json")
    task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    
    with open(session_path, "r", encoding="utf-8") as f:
        session_data = json.load(f)
    with open(task_path, "r", encoding="utf-8") as f:
        task_data = json.load(f)
        
    assert session_data["agent"] in ["gemini-antigravity", "codex"]
    assert "F1385" in task_data["task_id"] or "F1385" in session_data["task_id"]

def test_fixed_mesh_suite_governance_invariants():
    suite_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "07_fixed_mesh_convergence_suite")
    assert os.path.exists(suite_dir)
    
    expected_cases = [
        "01_coarse_2p5k_h20um",
        "02_medium_18k_h7p5um",
        "03_intermediate_40k_h5um",
        "04_fine_72k_h3p75um",
        "03_intermediate_40k_h5um_48h",
        "04_fine_72k_h3p75um_72h"
    ]
    for case in expected_cases:
        case_path = os.path.join(suite_dir, case)
        assert os.path.isdir(case_path), f"Missing case directory: {case_path}"
        manifest_file = os.path.join(case_path, "manifest.json")
        assert os.path.isfile(manifest_file), f"Missing manifest for {case}"

def test_mode1_baseline_freeze_integrity():
    mode1_uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.exists(mode1_uel_path)
    import hashlib
    with open(mode1_uel_path, "rb") as f:
        uel_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert uel_hash == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
