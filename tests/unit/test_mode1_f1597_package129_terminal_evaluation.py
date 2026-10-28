#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package129_terminal_evaluation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Tests and verifies the terminal evaluation of Package 129 Candidate C4 Increment-86->87
same-mesh forward continuation under Hypothesis H9:
1. Verifies authentic PBS completion receipts (Exit 0, walltime 366s, Job 1418398.mmaster02).
2. Verifies genuine continuation execution basis (P127 R1 checkpoint consumed, 17.8 nm loading applied, 17,688 GPs consumed).
3. Verifies zero healing violations across all 25 cycles.
4. Verifies reaction force continuity within 5% of authentic C3 donor reference.
5. Verifies total energy continuity within 2.0% of authentic C3 donor reference (+1.8876%).
6. Verifies incremental external work and energy balance consistency.
7. Verifies nonstationarity classification (H9_FAILED_NONSTATIONARY) due to Delta d = 0.001451 > 0.001000 at cycle cap 25.
8. Verifies retention of STAGE_C1_2_STEP2_ENERGY_GATE_FAILED governance binding.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_PATH = REPO_ROOT / "results/validation/package129_h9_terminal_evaluation.json"

@pytest.fixture(scope="module")
def eval_data():
    assert EVAL_PATH.is_file(), f"Evaluation report not found: {EVAL_PATH}"
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_schema_and_job_receipts(eval_data):
    assert eval_data["schema"] == 1
    assert eval_data["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert eval_data["package"] == "129_c4_inc87_h9_continuation"
    assert eval_data["pbs_job_id"] == "1418398.mmaster02"
    assert eval_data["exit_code"] == 0
    assert eval_data["execution_host"] == "mnode100"
    assert 300 < eval_data["walltime_seconds"] < 400
    assert eval_data["scientific_classification"] == "H9_FAILED_NONSTATIONARY"
    assert eval_data["governance_gate_retained"] == "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED"

def test_genuine_continuation_basis(eval_data):
    cv = eval_data["continuation_verification"]
    assert "Package 127 R1" in cv["source_checkpoint"]
    assert cv["mesh_elements"] == 4422
    assert cv["mesh_nodes"] == 4588
    assert cv["mesh_gauss_points"] == 17688
    assert abs(cv["incremental_loading_nm"] - 17.797924) < 1e-4
    assert cv["uel_hash_verified"] == "AB0A5A71335ECB445E91EC13A645E280FF3310B561A5E78ABA4A49C8E81DD8AC"
    assert cv["healing_nodes"] == 0

def test_physical_criteria_satisfied(eval_data):
    pce = eval_data["predeclared_criteria_evaluation"]
    # Zero healing strictly preserved
    assert pce["damage_healing"]["status"] == "PASS"
    assert pce["damage_healing"]["observed_healing_nodes"] == 0
    # KKT optimality satisfied
    assert pce["kkt_free_residual"]["status"] == "PASS"
    assert pce["kkt_min_active_multiplier"]["status"] == "PASS"
    # Load drift criterion passed
    assert pce["stationarity_delta_rf2"]["status"] == "PASS"
    assert pce["stationarity_delta_rf2"]["observed_N"] < 0.1
    # RF2 continuity within 5%
    assert pce["rf2_continuity_vs_donor"]["status"] == "PASS"
    assert abs(pce["rf2_continuity_vs_donor"]["discrepancy_pct"]) <= 5.0
    # Energy continuity within 2%
    assert pce["energy_continuity_vs_donor"]["status"] == "PASS"
    assert 1.80 < pce["energy_continuity_vs_donor"]["discrepancy_pct"] < 1.95

def test_nonstationarity_cause(eval_data):
    pce = eval_data["predeclared_criteria_evaluation"]
    # Stationarity failed at cycle 25 cap
    assert pce["stationarity_delta_d"]["status"] == "FAIL"
    assert pce["stationarity_delta_d"]["observed"] > 0.0010
    cd = eval_data["convergence_dynamics"]
    assert cd["cycles_completed"] == 25
    assert cd["monotonic_contraction_verified"] is True
    assert 0.90 < cd["average_contraction_factor"] < 0.98

def test_energy_balance_consistency(eval_data):
    eb = eval_data["energy_balance_analysis"]
    assert 0.0030 < eb["delta_w_ext_mJ"] < 0.0035
    assert 0.0030 < eb["delta_e_frac_mJ"] < 0.0035
    assert eb["delta_e_elas_mJ"] < 0 # Elastic relaxation during softening
    assert abs(eb["rel_energy_residual_vs_etot_pct"]) < 0.05
    assert eb["turn265_predicted_error_vs_actual_pct"] < 0.01 # Within 0.01% of prediction
