#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package157_r8_acceptance.py
=================================
Unit tests verifying the authentic Package 157 Revision 8 results (Job 1419490.mmaster02)
and physical acceptance evaluation.

Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ACCEPTANCE_JSON = REPO_ROOT / "results" / "validation" / "package157_r8_physical_acceptance.json"
EVIDENCE_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "157_c4_package157_c1_2_continuation_r8" / "evidence" / "1419490.mmaster02"


def test_package157_r8_evidence_integrity():
    assert EVIDENCE_DIR.is_dir(), f"Missing evidence dir: {EVIDENCE_DIR}"
    assert (EVIDENCE_DIR / "converged_checkpoint_01.json").is_file()
    assert (EVIDENCE_DIR / "runtime_report.json").is_file()
    assert (EVIDENCE_DIR / "retrieval_manifest.json").is_file()


def test_package157_r8_acceptance_json():
    assert ACCEPTANCE_JSON.is_file(), f"Missing acceptance JSON: {ACCEPTANCE_JSON}"
    data = json.loads(ACCEPTANCE_JSON.read_text(encoding="utf-8"))

    assert data["schema"] == 1
    assert data["job_id"] == "1419490.mmaster02"
    assert pytest.approx(data["target_uy_mm"], abs=1e-9) == 0.0018703125442191958

    # Coupled convergence
    cc = data["coupled_convergence"]
    assert cc["passed"] is True
    assert cc["converged_outer_iteration"] == 156
    assert cc["final_delta_d"] <= 1.0e-5
    assert cc["final_delta_u_mm"] <= 1.0e-9
    assert cc["final_delta_h_MPa"] <= 1.0e-6

    # State preservation
    sp = data["state_preservation"]
    assert sp["passed"] is True
    assert sp["nodes_checked"] == 7265
    assert sp["gps_checked"] == 28224
    assert sp["min_delta_d"] >= -1.0e-6

    # Physical acceptance gates
    pa = data["physical_acceptance_vs_donor"]
    assert pa["rf2_gate_pass"] is True
    assert pytest.approx(pa["delta_rf2_rel"], rel=1e-3) == 0.019776  # 1.98% <= 5%
    assert pa["energy_gate_pass"] is False
    assert pytest.approx(pa["delta_energy_rel"], rel=1e-3) == 0.038634  # 3.86% > 2%
    assert data["overall_verdict"] == "COUPLED_CONVERGED__PHYSICAL_ACCEPTANCE_FAIL"
