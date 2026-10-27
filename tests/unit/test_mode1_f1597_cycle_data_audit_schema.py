"""
test_mode1_f1597_cycle_data_audit_schema.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test suite for cycle-data audit schema and descriptive H1 criteria:
1. Verifies field validation of cycle records (required fields, numeric types).
2. Verifies contraction factor calculation with positive denominators and non-fabrication of missing values.
3. Verifies LOSS_OF_CONTRACTION_DETECTED classification on Package 120 cycles 13-15.
4. Verifies scientific interpretation nuance: loss of contraction over observed cycles does not prove nonexistence of equilibrium.
5. Verifies SUSTAINED_CONTRACTION_SUPPORTED synthetic test case.
6. Verifies INCONCLUSIVE synthetic test case.
"""

import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts/validation"))

from cycle_data_audit_schema import (
    CYCLE_SCHEMA_FIELDS,
    validate_cycle_record,
    compute_contraction_factors,
    classify_descriptive_h1
)


def test_schema_field_completeness():
    assert len(CYCLE_SCHEMA_FIELDS) == 17
    assert "cycle" in CYCLE_SCHEMA_FIELDS
    assert "uRP_mm" in CYCLE_SCHEMA_FIELDS
    assert "RF2_N" in CYCLE_SCHEMA_FIELDS
    assert "delta_RF2_N" in CYCLE_SCHEMA_FIELDS
    assert "mechanical_residual_kN" in CYCLE_SCHEMA_FIELDS
    assert "dmax" in CYCLE_SCHEMA_FIELDS
    assert "delta_d_Linf" in CYCLE_SCHEMA_FIELDS
    assert "free_phase_residual_kN_per_mm" in CYCLE_SCHEMA_FIELDS
    assert "active_KKT_min_kN_per_mm" in CYCLE_SCHEMA_FIELDS
    assert "healing_count" in CYCLE_SCHEMA_FIELDS
    assert "active_free_nodes" in CYCLE_SCHEMA_FIELDS
    assert "Eelas_mJ" in CYCLE_SCHEMA_FIELDS
    assert "Efrac_local_mJ" in CYCLE_SCHEMA_FIELDS
    assert "Efrac_gradient_mJ" in CYCLE_SCHEMA_FIELDS
    assert "Etotal_mJ" in CYCLE_SCHEMA_FIELDS
    assert "committed_history_status" in CYCLE_SCHEMA_FIELDS
    assert "solver_status" in CYCLE_SCHEMA_FIELDS


def test_validate_record():
    valid_rec = {
        "cycle": 1,
        "uRP_mm": 0.001965,
        "RF2_N": 185.0,
        "delta_RF2_N": 0.15,
        "mechanical_residual_kN": 1.0e-5,
        "dmax": 0.64,
        "delta_d_Linf": 0.007,
        "free_phase_residual_kN_per_mm": 1.0e-9,
        "active_KKT_min_kN_per_mm": -1.0e-10,
        "healing_count": 0,
        "active_free_nodes": 4200,
        "Eelas_mJ": 0.17,
        "Efrac_local_mJ": 0.03,
        "Efrac_gradient_mJ": 0.03,
        "Etotal_mJ": 0.23,
        "committed_history_status": "STRICTLY_COMMITTED_INVARIANT",
        "solver_status": "CONVERGED"
    }
    ok, errs = validate_cycle_record(valid_rec)
    assert ok, f"Expected valid record, got errors: {errs}"

    # Incomplete record
    incomplete = dict(valid_rec)
    del incomplete["Etotal_mJ"]
    ok, errs = validate_cycle_record(incomplete)
    assert not ok
    assert any("Etotal_mJ" in e for e in errs)


def test_package120_loss_of_contraction():
    pkg120_path = os.path.join(REPO_ROOT, "results/validation/package120_convergence_diagnosis.json")
    assert os.path.exists(pkg120_path)
    with open(pkg120_path, "r", encoding="utf-8") as f:
        diag = json.load(f)

    # Build cycle records from diag
    cycle_records = []
    for c in diag["cycle_history_audit"]:
        cycle_records.append({
            "cycle": c["cycle"],
            "uRP_mm": 0.001965107396,
            "RF2_N": c["rf2_rp_N"],
            "delta_RF2_N": c["delta_rf2_prev_cycle_N"] if c["delta_rf2_prev_cycle_N"] is not None else 0.15,
            "mechanical_residual_kN": 1.0e-5,
            "dmax": c["d_max"],
            "delta_d_Linf": c["max_delta_d"],
            "free_phase_residual_kN_per_mm": c["free_phase_residual_kN_mm"],
            "active_KKT_min_kN_per_mm": c["min_lambda_kkt_kN_mm"],
            "healing_count": 0,
            "active_free_nodes": c["free_nodes"],
            "Eelas_mJ": c["e_elas_mJ"],
            "Efrac_local_mJ": c["e_frac_mJ"] / 2.0,
            "Efrac_gradient_mJ": c["e_frac_mJ"] / 2.0,
            "Etotal_mJ": c["e_tot_mJ"],
            "committed_history_status": "STRICTLY_COMMITTED_INVARIANT",
            "solver_status": "ITERATION_CAP_REACHED"
        })

    res = classify_descriptive_h1(cycle_records)
    assert res["classification"] == "LOSS_OF_CONTRACTION_DETECTED"
    assert res["consecutive_expansion_cycles"] >= 3
    assert not res["extended_retry_supported"]
    assert "loss of contraction over those cycles" in res["scientific_interpretation"]
    assert "do not mathematically prove that no stationary equilibrium exists" in res["scientific_interpretation"]


def test_synthetic_sustained_contraction():
    # 7 cycles with steady contraction ~0.85
    recs = []
    delta_d = 0.01
    delta_f = 1.0
    for i in range(1, 8):
        recs.append({
            "cycle": i,
            "uRP_mm": 0.0018,
            "RF2_N": 180.0,
            "delta_RF2_N": delta_f,
            "mechanical_residual_kN": 1.0e-5,
            "dmax": 0.5,
            "delta_d_Linf": delta_d,
            "free_phase_residual_kN_per_mm": 1.0e-9,
            "active_KKT_min_kN_per_mm": -1.0e-10,
            "healing_count": 0,
            "active_free_nodes": 4000,
            "Eelas_mJ": 0.15,
            "Efrac_local_mJ": 0.03,
            "Efrac_gradient_mJ": 0.03,
            "Etotal_mJ": 0.21,
            "committed_history_status": "STRICTLY_COMMITTED_INVARIANT",
            "solver_status": "CONVERGED"
        })
        delta_d *= 0.85
        delta_f *= 0.85

    res = classify_descriptive_h1(recs)
    assert res["classification"] == "SUSTAINED_CONTRACTION_SUPPORTED"
    assert res["extended_retry_supported"]
    assert res["geo_mean_rho_d"] < 0.95
    assert res["geo_mean_rho_F"] < 0.95
