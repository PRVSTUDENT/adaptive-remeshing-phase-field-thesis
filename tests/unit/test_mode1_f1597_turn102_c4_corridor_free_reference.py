#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn102_c4_corridor_free_reference.py
Unit tests verifying the Turn 102 C4 predecessor audit, corridor deconstruction,
and corridor-free vs corridor-clamped reference findings.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
AUDIT_JSON = REPO_ROOT / "results/validation/mode1_f1597/turn102_c4_corridor_free_reference_audit.json"

def test_audit_json_exists():
    assert AUDIT_JSON.exists(), f"Audit file not found: {AUDIT_JSON}"

def test_predecessor_lineage():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    lineage = data["predecessor_corridor_lineage"]
    assert lineage["Package_89_C2"]["step4_dof3_bcs"] == 0
    assert lineage["Package_90_C3"]["step4_dof3_bcs"] == 0
    assert lineage["Package_90_R1_C3"]["step4_dof3_bcs"] == 2221
    assert lineage["Package_93_C3"]["step4_dof3_bcs"] == 2221
    assert lineage["Package_94_C4"]["step4_dof3_bcs"] == 3845

def test_initial_checkpoint_metrics():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    init_audit = data["initial_checkpoint_audit"]
    assert init_audit["u0_mm"] == pytest.approx(0.00203669304, rel=1e-6)
    assert init_audit["rf2_init_N"] == pytest.approx(158.9868, rel=1e-3)
    assert init_audit["norm_res_d_init"] > 1.0e-6

def test_case_comparisons_and_conclusions():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    comp = data["comparison_vs_pkg94"]
    concl = data["scientific_conclusions"]
    assert comp["tearing_drop_in_corridor_free_N"] > 0
    assert concl["donor_defect_proven"] is True
    assert concl["package94_classification"] == "BENCHMARK-REPRODUCTION-ONLY"
    assert concl["gate_c1_2_status"] == "NOT_QUALIFIED"
    assert concl["hpc_decision"] == "WITHHELD_BY_POLICY_UNQUALIFIED_PREDECESSOR"
