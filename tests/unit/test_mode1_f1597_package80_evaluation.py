#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package80_evaluation.py

Unit tests verifying Package 80 evaluation metrics, Step 1 exact parity,
Step 2 force reduction vs Package 79, Step 3 cutback identification,
and Method C Gate C1-1 decision.
"""

import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_JSON = REPO_ROOT / "results/validation/mode1_f1597/f1597_turn28_package80_evaluation.json"
UEL_FILE = REPO_ROOT / "models/pandey_kumar_mode1/80_candidate_c2_peak_preserved_reequilibration/f42_mixed_uel.for"

class TestPackage80Evaluation:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        assert EVAL_JSON.exists(), f"Evaluation JSON not found: {EVAL_JSON}"
        with open(EVAL_JSON, "r", encoding="utf-8") as f:
            self.eval_data = json.load(f)

    def test_package80_step1_exact_parity(self):
        s1 = self.eval_data["step1_parity"]
        assert s1["verdict"] == "EXACT_PARITY_PASS"
        assert abs(s1["rf2_error_pct"]) < 0.1, f"RF2 error too high: {s1['rf2_error_pct']}%"
        assert abs(s1["e_frac_error_pct"]) < 2.0, f"E_frac error too high: {s1['e_frac_error_pct']}%"
        assert abs(s1["rf2_N"] - 3.2683) < 1e-3
        assert abs(s1["e_frac_uj"] - 295.4836) < 1e-2

    def test_package80_step2_spurious_force_reduction(self):
        s2 = self.eval_data["step2_frozen_relaxation"]
        assert s2["reduction_vs_pkg79_N"] > 4.0, f"Insufficient force reduction: {s2['reduction_vs_pkg79_N']} N"
        assert s2["terminal_rf2_N"] < 7.35, f"Terminal Step 2 RF2 unexpectedly high: {s2['terminal_rf2_N']} N"

    def test_package80_step3_cutback_identification(self):
        s3 = self.eval_data["step3_coupled_convergence"]
        assert s3["exit_code"] == 1
        assert s3["termination_reason"] == "TIME_INCREMENT_REQUIRED_LESS_THAN_MINIMUM"
        assert s3["limiting_node_u"] == 1192
        assert s3["limiting_node_d"] == 1239
        assert 0.035 < s3["terminal_time"] < 0.040

    def test_package80_gate_c1_1_failed_verdict(self):
        gate = self.eval_data["gate_c1_1_matrix"]
        assert gate["overall_gate_verdict"] == "FAILED"
        assert gate["step3_coupled_completion"]["status"] == "FAIL"
        assert gate["reaction_force_continuity"]["status"] == "FAIL"
        assert gate["fracture_energy_continuity"]["status"] == "PASS"

    def test_package80_uel_hash_integrity(self):
        assert UEL_FILE.exists(), f"UEL file missing: {UEL_FILE}"
        h = hashlib.sha256(UEL_FILE.read_bytes()).hexdigest().upper()
        assert h == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
