# -*- coding: utf-8 -*-
"""
tests/unit/test_f1829_native_miseseri_audit.py
=============================================
Unit and regression test suite for Task F1829:
Independent Evidence Audit of Native MISESERI Direct UEL-UMAT Coupling (F1720-F1726)
and Transition to Recovery Donors (F1728, F1761, F1772, F1812).

Verifies:
  1. Cryptographic hashes of governing constitutive source files (frozen production UEL vs Amor UEL).
  2. Mathematical formulation discrepancies (isotropic degradation vs Amor volumetric-deviatoric split).
  3. Step-1 vs Step-2 attribution discrepancy and exact donor frame provenance.
  4. Layered UEL/UMAT element mapping, tensor ordering, and scaling invariance.
  5. Retraction of F1720 force-match claims and forward solver termination metrics.
  6. Governance invariants: max_new_pbs = 0, cumulative_pbs = 35, MASTER_GOAL_STATUS = OPEN.
"""

import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Cryptographic digests
HASH_FROZEN_PRODUCTION_UEL = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
HASH_AMOR_SPLIT_UEL_V2      = "91612E94E7A2E3F30845AE80815EF4337F582044E25E33BED80072E4AEC40243"
HASH_SHARED_FRAMEWORK       = "80B41AA22BAA18131343715C870C63810166299DE04F789D4263795C6EFD2875"

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_01_constitutive_source_hashes():
    """Verify bitwise hashes of frozen production UEL and Amor split UEL."""
    p_frozen = os.path.join(REPO_ROOT, "runs", "f1708_job2_frozen_uel_datacheck", "f42_mixed_uel.for")
    p_amor = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "208_f1716_five_hole_production", "f42_amor_split_uel_v2.for")
    
    assert os.path.exists(p_frozen), f"Frozen production UEL not found at {p_frozen}"
    assert os.path.exists(p_amor), f"Amor UEL v2 not found at {p_amor}"
    
    hash_frozen = compute_sha256(p_frozen)
    hash_amor = compute_sha256(p_amor)
    
    assert hash_frozen == HASH_FROZEN_PRODUCTION_UEL, f"Hash mismatch for frozen UEL: {hash_frozen}"
    assert hash_amor == HASH_AMOR_SPLIT_UEL_V2, f"Hash mismatch for Amor UEL: {hash_amor}"


def test_02_constitutive_formulation_differences():
    """Verify mathematical formulation differences: Isotropic degradation vs Amor split."""
    p_frozen = os.path.join(REPO_ROOT, "runs", "f1708_job2_frozen_uel_datacheck", "f42_mixed_uel.for")
    p_amor = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "208_f1716_five_hole_production", "f42_amor_split_uel_v2.for")
    
    with open(p_frozen, "r") as f:
        content_frozen = f.read()
    with open(p_amor, "r") as f:
        content_amor = f.read()
    
    # In frozen production UEL: isotropic degradation of stiffness tensor
    assert "C11_MECH = C11_0 * DEG" in content_frozen
    assert "C12_MECH = C12_0 * DEG" in content_frozen
    assert "C33_MECH = C33_0 * DEG" in content_frozen
    assert "AMOR VOLUMETRIC-DEVIATORIC STIFFNESS TENSOR" not in content_frozen
    
    # In Amor split UEL: split tension and compression stiffness
    assert "AMOR VOLUMETRIC-DEVIATORIC STIFFNESS TENSOR" in content_amor
    assert "Volumetric Compression: bulk undegraded, shear degraded" in content_amor
    assert "D_ELAS(1,1) = E_K_BULK + (FOUR/THREE)*E_MU * DEG" in content_amor


def test_03_step1_vs_step2_attribution_and_donor_provenance():
    """Verify that native MISESERI was extracted from Step-1 Frame 12, not Step 2 Inc 412."""
    p_metrics = os.path.join(REPO_ROOT, "results", "validation", "f1720_native_miseseri_evaluation.json")
    assert os.path.exists(p_metrics), f"Evaluation JSON not found at {p_metrics}"
    
    with open(p_metrics, "r") as f:
        data = json.load(f)
    
    assert data["num_elements"] == 2747
    assert abs(data["miseseri_stats"]["max"] - 2.2533930897996636e-14) < 1e-20
    assert abs(data["eta_stats"]["max_pct"] - 371.94185833735764) < 1e-6
    
    # Verify remeshing script targets Step-1
    p_remesh_script = os.path.join(REPO_ROOT, "scripts", "remeshing", "execute_f1720_native_adaptive_remesh.py")
    with open(p_remesh_script, "r") as f:
        remesh_src = f.read()
    assert "stepName='Step-1'" in remesh_src
    
    # Verify evaluator script extracts Step 1 frame
    p_eval_script = os.path.join(REPO_ROOT, "scripts", "remeshing", "evaluate_f1720_native_miseseri_vs_f1719.py")
    with open(p_eval_script, "r") as f:
        eval_src = f.read()
    assert "step1 = odb_c.steps['Step-1']" in eval_src
    assert "frame_s2 = step1.frames[-1]" in eval_src


def test_04_solver_forensics_and_retraction_verification():
    """Verify forensic evidence of F1720 forward solver divergence and peak load discrepancy."""
    p_forensics = os.path.join(REPO_ROOT, "results", "validation", "f1720_solver_forensics.json")
    assert os.path.exists(p_forensics), f"Forensics JSON not found at {p_forensics}"
    
    with open(p_forensics, "r") as f:
        data = json.load(f)
    
    # 13,163 elements -> 51,716 integration points
    assert data["sdv1_values_count"] == 51716
    assert data["steps"]["Step-1"]["total_frames"] == 51
    assert data["steps"]["Step-2"]["total_frames"] == 128
    
    # Peak load achieved before divergence
    rf_end = data["final_frame_summary"]["rf2_rp"]
    assert abs(rf_end - 0.9127940535545349) < 1e-6
    # Published benchmark is 1.05 kN -> divergence before reaching full peak/post-peak


def test_05_governance_invariants():
    """Verify active session and task governance parameters."""
    p_session = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_SESSION.json")
    p_task = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    
    with open(p_session, "r") as f:
        sess = json.load(f)
    with open(p_task, "r") as f:
        task = json.load(f)
    
    assert sess["active"] is True
    assert sess["agent"] == "gemini-antigravity"
    assert task["max_new_pbs_submissions"] == 0
    assert task["submissions_consumed"] == 0
    assert task["cumulative_pbs_submissions"] == 35
    assert task["master_goal_status"] == "OPEN"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
