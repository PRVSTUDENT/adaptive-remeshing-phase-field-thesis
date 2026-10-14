"""
Unit tests for Task F1448 Genuine Continuation Extractor and Evaluator
(scripts/postprocessing/extract_mode1_f1448_genuine_continuation_results.py)
"""

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.postprocessing.extract_mode1_f1448_genuine_continuation_results import (
    parse_sta_file,
    parse_dat_file,
    parse_energy_csv,
    compute_external_work,
    evaluate_genuine_continuation
)

def test_parse_sta_synthetic(tmp_path):
    sta_file = tmp_path / "M1_MC_GENUINE_CONTINUATION.sta"
    sta_content = (
        "   1     1   1     0     2     2  1.00       1.00       1.0000000 \n"
        "   2     1   1     0     3     3  1.00       0.000200   0.0002000 \n"
        "   2     2   1     0     3     3  1.00       0.000400   0.0002000 \n"
        "   2     3   1U    0     4     4  1.00       0.000400   0.0001000 \n"
        "   2     3   2     0     3     3  1.00       0.000500   0.0001000 \n"
    )
    sta_file.write_text(sta_content, encoding="utf-8")
    
    summary = parse_sta_file(sta_file)
    assert summary["status"] == "PARSED"
    assert summary["total_increments"] == 4
    assert summary["step1_increments"] == 1
    assert summary["step2_increments"] == 3
    assert summary["cutbacks"] == 1
    assert summary["final_step"] == 2

def test_parse_dat_synthetic(tmp_path):
    dat_file = tmp_path / "M1_MC_GENUINE_CONTINUATION.dat"
    dat_content = (
        " S T E P  1\n"
        "   THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET N_RP\n"
        "    999999      5.0000000E-03  6.7472000E-01 \n"
        " S T E P  2\n"
        "   THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET N_RP\n"
        "    999999      5.0010000E-03  6.5316940E-01 \n"
        "    999999      5.0020000E-03  6.5400000E-01 \n"
    )
    dat_file.write_text(dat_content, encoding="utf-8")
    
    records = parse_dat_file(dat_file)
    assert len(records) == 3
    assert records[0]["step"] == 1
    assert pytest.approx(records[0]["u2_mm"], rel=1e-6) == 0.0050
    assert pytest.approx(records[0]["rf2_n"], rel=1e-5) == 674.72
    assert records[1]["step"] == 2
    assert pytest.approx(records[1]["rf2_n"], rel=1e-5) == 653.1694

def test_parse_energy_csv_synthetic(tmp_path):
    csv_file = tmp_path / "uel_energy_balance.csv"
    # Columns in Fortran: KSTEP, KINC, TotalTime, StepTime, TOT_E_ELAS, TOT_E_FRAC, TOT_E_INT
    csv_content = (
        "Step, Increment, TotalTime, StepTime, E_elastic_kNmm, E_fracture_kNmm, E_total_kNmm\n"
        "   1,     1,  0.10000000E+01,  0.10000000E+01,  0.00000000E+00,  0.16898560E-02,  0.16898560E-02\n"
        "   2,     1,  0.10002000E+01,  0.20000000E-03,  0.10000000E-04,  0.16900000E-02,  0.17000000E-02\n"
        "   2,     2,  0.10004000E+01,  0.40000000E-03,  0.20000000E-04,  0.17000000E-02,  0.17200000E-02\n"
    )
    csv_file.write_text(csv_content, encoding="utf-8")
    
    records = parse_energy_csv(csv_file)
    assert len(records) == 3
    assert records[0]["step"] == 1
    assert pytest.approx(records[0]["e_total_mj"], rel=1e-5) == 1.689856
    assert pytest.approx(records[1]["e_elastic_mj"], rel=1e-5) == 0.010
    assert pytest.approx(records[1]["e_fracture_mj"], rel=1e-5) == 1.690
    assert pytest.approx(records[1]["e_total_mj"], rel=1e-5) == 1.700

def test_compute_external_work():
    rf_pts = [
        {"u2_mm": 0.0050, "rf2_kn": 0.653},
        {"u2_mm": 0.0060, "rf2_kn": 0.750},
        {"u2_mm": 0.0070, "rf2_kn": 0.850},
    ]
    w_ext = compute_external_work(rf_pts)
    assert pytest.approx(w_ext, rel=1e-4) == 1.5015

def test_evaluate_genuine_continuation_synthetic(tmp_path):
    sta_file = tmp_path / "M1_MC_GENUINE_CONTINUATION.sta"
    sta_file.write_text(
        "   1     1   1     0     2     2  1.00       1.00       1.0000000 \n"
        "   2     1   1     0     3     3  1.00       0.000200   0.0002000 \n",
        encoding="utf-8"
    )
    dat_file = tmp_path / "M1_MC_GENUINE_CONTINUATION.dat"
    dat_file.write_text(
        " S T E P  1\n"
        "    999999      5.0000000E-03  6.7472000E-01 \n"
        " S T E P  2\n"
        "    999999      5.0010000E-03  6.5316940E-01 \n",
        encoding="utf-8"
    )
    csv_file = tmp_path / "uel_energy_balance.csv"
    csv_file.write_text(
        "Step, Increment, TotalTime, StepTime, E_elastic, E_fracture, E_total\n"
        "   1,     1,  1.0,  1.0,  0.0,  0.1689856E-02,  0.1689856E-02\n"
        "   2,     1,  1.0002,  0.0002,  0.0001,  0.1690000E-02,  0.1700000E-02\n",
        encoding="utf-8"
    )
    
    evaluation = evaluate_genuine_continuation(tmp_path, donor_rf_handoff_n=653.09, donor_energy_handoff_mj=1.6911)
    
    handoff = evaluation["handoff_evaluation"]
    assert pytest.approx(handoff["step1_rf_end_n"], rel=1e-4) == 674.72
    assert pytest.approx(handoff["step2_entry_rf_n"], rel=1e-4) == 653.1694
    assert pytest.approx(handoff["step2_entry_delta_rf_n"], abs=1e-3) == 0.0794
    assert handoff["criterion_5_verdict"] == "PASS"
    assert pytest.approx(handoff["step1_energy_error_pct"], abs=1e-2) == 0.0736
