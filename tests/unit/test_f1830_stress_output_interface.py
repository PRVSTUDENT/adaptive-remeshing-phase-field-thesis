# -*- coding: utf-8 -*-
"""
tests/unit/test_f1830_stress_output_interface.py
================================================
Unit and regression test suite for Task F1830:
Qualification of the Smallest Stress-Output Interface Candidate
Enabling Native Abaqus MISESERI While Preserving the Frozen Isotropic UEL.

Verifies:
  1. Bitwise preservation of frozen production UEL (CE8D5EDC...) and framework (80B41AA2...).
  2. Candidate interface f42_native_miseseri_interface_v1.for existence, registration, and isotropic formulation.
  3. Cutback buffer architecture (committed/trial dual-stage arrays with Fortran SAVE).
  4. Multi-element mechanical neutrality on 4-element patch (0.0000% reaction force discrepancy).
  5. Negative control verification (unscaled Cauchy stress causes +100.00% RF doubling).
  6. Integration-point stress fidelity and mathematical scale-invariance of relative error eta.
  7. Governance invariants: max_new_pbs = 0, cumulative_pbs = 35, MASTER_GOAL_STATUS = OPEN.
"""

import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

HASH_FROZEN_PRODUCTION_UEL = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
HASH_SHARED_FRAMEWORK       = "80B41AA253E5B36B2BCF5D716B88843D29355141171C60AFF6E7134A0312932C"

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_01_bitwise_preservation_and_candidate_existence():
    """Verify bitwise preservation of frozen UEL and framework, and candidate existence."""
    p_frozen = os.path.join(REPO_ROOT, "runs", "f1708_job2_frozen_uel_datacheck", "f42_mixed_uel.for")
    p_framework = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
    p_candidate = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "271_f1830_stress_output_interface", "f42_native_miseseri_interface_v1.for")

    assert os.path.exists(p_frozen), f"Frozen UEL missing at {p_frozen}"
    assert os.path.exists(p_framework), f"Framework missing at {p_framework}"
    assert os.path.exists(p_candidate), f"Candidate interface missing at {p_candidate}"

    assert compute_sha256(p_frozen) == HASH_FROZEN_PRODUCTION_UEL
    assert compute_sha256(p_framework) == HASH_SHARED_FRAMEWORK


def test_02_constitutive_isotropic_fidelity():
    """Verify candidate interface preserves Isotropic Degradation formulation."""
    p_candidate = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "271_f1830_stress_output_interface", "f42_native_miseseri_interface_v1.for")
    with open(p_candidate, "r") as f:
        content = f.read()

    # Isotropic stiffness tensor degradation
    assert "C11_MECH = C11_0 * DEG" in content
    assert "C12_MECH = C12_0 * DEG" in content
    assert "C33_MECH = C33_0 * DEG" in content

    # Absence of Amor volumetric-deviatoric split
    assert "AMOR VOLUMETRIC-DEVIATORIC STIFFNESS TENSOR" not in content
    assert "Volumetric Compression: bulk undegraded" not in content


def test_03_cutback_buffer_architecture():
    """Verify committed and trial stress buffer architecture with SAVE attribute."""
    p_candidate = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "271_f1830_stress_output_interface", "f42_native_miseseri_interface_v1.for")
    with open(p_candidate, "r") as f:
        content = f.read()

    # Dual-stage buffer declaration
    assert "DOUBLE PRECISION SV_STRESS_COMMITTED(N_CAPACITY, 4, 4)" in content
    assert "DOUBLE PRECISION SV_STRESS_TRIAL(N_CAPACITY, 4, 4)" in content
    assert "COMMON /CB_F1830_STRESS/ SV_STRESS_COMMITTED, SV_STRESS_TRIAL" in content
    assert "SAVE /CB_F1830_STRESS/" in content

    # LOP=1 cutback trial reset
    assert "SV_STRESS_TRIAL(I, K, C) = SV_STRESS_COMMITTED(I, K, C)" in content

    # LOP=2 increment commitment
    assert "SV_STRESS_COMMITTED(I, K, C) = SV_STRESS_TRIAL(I, K, C)" in content


def test_04_multi_element_mechanical_neutrality():
    """Verify multi-element mechanical neutrality on 4-element patch."""
    p_results = os.path.join(REPO_ROOT, "results", "validation", "f1830_patch_check_results.json")
    assert os.path.exists(p_results), f"Patch check results missing at {p_results}"

    with open(p_results, "r") as f:
        data = json.load(f)

    mn = data["mechanical_neutrality"]
    rf_ref = mn["rf_ref_kN"]
    rf_coupled = mn["rf_coupled_kN"]
    diff = mn["diff_kN"]
    rel_diff = mn["rel_diff_pct"]

    # Verify unrounded machine precision neutrality
    assert abs(rf_ref - 0.4576188921928406) < 1e-12
    assert abs(rf_coupled - 0.4576188921928406) < 1e-12
    assert diff == 0.0
    assert rel_diff == 0.0

    # Verify unscaled control causes force doubling
    rf_unscaled = mn["unscaled_rf_kN"]
    assert abs(rf_unscaled - 0.9152377843856812) < 1e-12
    assert abs(mn["unscaled_rel_diff_pct"] - 100.0) < 1e-6


def test_05_stress_fidelity_and_scale_invariance():
    """Verify element/IP stress fidelity and scale-invariance of error indicator."""
    p_results = os.path.join(REPO_ROOT, "results", "validation", "f1830_patch_check_results.json")
    with open(p_results, "r") as f:
        data = json.load(f)

    comp_stresses = data["companion_stresses"]
    assert len(comp_stresses) == 4  # 4 elements

    # Verify all 16 integration points match analytical stress
    for el_lbl, ips in comp_stresses.items():
        assert len(ips) == 4
        for ip_idx, s_data in ips.items():
            assert abs(s_data["S_unscaled_22"] - 0.2288094460964203) < 1e-6

    # Verify scale-invariance of relative error eta
    inv = data["scale_invariance"]
    assert inv["is_invariant"] is True
    assert inv["max_eta_diff_pct"] < 1e-10


def test_06_governance_invariants():
    """Verify task and session governance constraints."""
    p_task = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(p_task, "r") as f:
        task = json.load(f)

    assert task["max_new_pbs_submissions"] == 0
    assert task["submissions_consumed"] == 0
    assert task["cumulative_pbs_submissions"] == 35
    assert task["master_goal_status"] == "OPEN"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
