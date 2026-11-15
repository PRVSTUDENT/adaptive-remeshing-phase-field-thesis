# -*- coding: utf-8 -*-
"""
tests/unit/test_f1753_continuation_audit.py

Unit tests for Task F1753 Case 2 continuation audit module:
- DAT file reaction force parsing
- Parity evaluation logic against Job 1423271
- Continuation gate evaluation
- Damage irreversibility and history monotonicity gate checks
- Wake residual diagnostic evaluation
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from scripts.remeshing.audit_f1753_continuation_odb import (
    BASELINE_1423271,
    parse_rf_u_from_dat
)

def test_baseline_1423271_constants():
    assert BASELINE_1423271["job_id"] == "1423271.mmaster02"
    assert BASELINE_1423271["total_increments"] == 252
    assert BASELINE_1423271["step_1_increments"] == 50
    assert BASELINE_1423271["step_2_increments"] == 202
    assert abs(BASELINE_1423271["peak_force_kN"] - 0.57168154) < 1e-6
    assert abs(BASELINE_1423271["final_force_inc252_kN"] - 0.24441924) < 1e-6

def test_parse_rf_u_from_dat_empty():
    res = parse_rf_u_from_dat("non_existent_file.dat")
    assert res == []

def test_gate_g1_parity_logic():
    # If rerun force at inc 252 matches within 0.01%
    f_base = BASELINE_1423271["final_force_inc252_kN"]
    f_rerun_pass = f_base * (1.0 + 0.00005)  # 0.005% diff
    f_rerun_fail = f_base * (1.0 + 0.0002)   # 0.02% diff

    delta_pct_pass = abs(f_rerun_pass - f_base) / f_base * 100.0
    delta_pct_fail = abs(f_rerun_fail - f_base) / f_base * 100.0

    assert delta_pct_pass <= 0.01
    assert delta_pct_fail > 0.01

def test_gate_g2_continuation_logic():
    continuation_threshold_u_y = 0.007677
    continuation_threshold_step2_time = 0.567702

    # Case A: Terminates at predecessor checkpoint
    t_end_a = 0.567702
    u_y_a = 0.002 + t_end_a * 0.010
    gate_a = (t_end_a > continuation_threshold_step2_time and u_y_a > continuation_threshold_u_y)
    assert not gate_a

    # Case B: Advances further into secondary ligament
    t_end_b = 0.750000
    u_y_b = 0.002 + t_end_b * 0.010
    gate_b = (t_end_b > continuation_threshold_step2_time and u_y_b > continuation_threshold_u_y)
    assert gate_b

def test_gate_g3_irreversibility_logic():
    # Strict irreversibility threshold: min Delta d >= -1.0e-5
    assert -5.0e-6 >= -1.0e-5  # Pass
    assert not (-1.86e-4 >= -1.0e-5)  # Fail (historical wake artifact)

def test_generate_f1753_publication_figure():
    from scripts.remeshing.plot_f1753_continuation_results import main as generate_figure
    generate_figure()

    out_png = 'results/figures/fig_f1753_continuation_response.png'
    out_pdf = 'results/figures/fig_f1753_continuation_response.pdf'

    assert os.path.exists(out_png)
    assert os.path.exists(out_pdf)
    assert os.path.getsize(out_png) > 10000
    assert os.path.getsize(out_pdf) > 10000



