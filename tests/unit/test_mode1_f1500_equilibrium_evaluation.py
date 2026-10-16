#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1500_equilibrium_evaluation.py
===========================================
Unit tests for evaluate_mode1_stage_c1_1_equilibrium.py and Gate 6C
acceptance review logic for Package 49 Stage C1-1 nonmatching equilibrium.

Protocol Version: 2
Author: Gemini Antigravity
Task: F1500
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.evaluate_mode1_stage_c1_1_equilibrium import (
    parse_sta_file,
    parse_dat_file,
    parse_energy_csv,
    evaluate_equilibrium_results,
    AUTHENTIC_DONOR,
    ACCEPTANCE_THRESHOLDS
)


class TestMode1F1500EquilibriumEvaluation:
    """Tests for Stage C1-1 equilibrium review and acceptance criteria."""

    def test_donor_benchmark_constants_and_thresholds(self):
        """Verify authentic donor values and Gate 6C thresholds are mathematically sound."""
        assert AUTHENTIC_DONOR["num_elements"] == 2906
        assert AUTHENTIC_DONOR["u_rp_mm"] == 0.005000
        assert AUTHENTIC_DONOR["rf_rp_N"] == pytest.approx(653.0886, rel=1e-4)
        assert AUTHENTIC_DONOR["e_elas_mJ"] == pytest.approx(1.632721, rel=1e-4)
        assert AUTHENTIC_DONOR["e_frac_mJ"] == pytest.approx(0.030663, rel=1e-4)
        assert AUTHENTIC_DONOR["e_tot_mJ"] == pytest.approx(1.663384, rel=1e-4)
        assert AUTHENTIC_DONOR["d_max"] == pytest.approx(0.092105, abs=1e-5)
        
        # Verify strict threshold limits
        assert ACCEPTANCE_THRESHOLDS["delta_rf_max_N"] == 5.00
        assert ACCEPTANCE_THRESHOLDS["delta_d_max"] == 0.0200
        assert ACCEPTANCE_THRESHOLDS["delta_e_elas_rel_pct"] == 0.50
        assert ACCEPTANCE_THRESHOLDS["delta_e_frac_rel_pct"] == 0.50
        assert ACCEPTANCE_THRESHOLDS["delta_e_tot_rel_pct"] == 0.10
        assert ACCEPTANCE_THRESHOLDS["delta_book_ratio_pct"] == 2.00
        assert ACCEPTANCE_THRESHOLDS["max_cutbacks"] == 0

    def test_parse_sta_file_synthetic(self, tmp_path):
        """Verify .sta file parser correctly detects increments and cutbacks."""
        sta_file = tmp_path / "test.sta"
        sta_content = (
            "   STEP   INC  ATT  SEVERE  EQUIL  TOTAL     TOTAL       STEP       INC OF\n"
            "                    DISCON  ITERS  ITERS   TIME/FREQ   TIME/LPF    TIME/LPF\n"
            "      1     1    1       0      3      3  0.0100000   0.0100000   0.0100000\n"
            "      1     2    1       0      3      3  0.0500000   0.0500000   0.0400000\n"
            "      1     3    2       0      4      4  0.0700000   0.0700000   0.0200000\n"
            "      1     4    1       0      3      3  1.0000000   1.0000000   0.9300000\n"
            " THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n"
        )
        sta_file.write_text(sta_content, encoding="utf-8")
        
        parsed = parse_sta_file(str(sta_file))
        assert parsed["exists"] is True
        assert parsed["total_increments"] == 4
        assert parsed["total_cutbacks"] == 1  # Increment 3 had ATT=2 (1 cutback)
        assert parsed["step1_completed"] is True
        assert parsed["last_increment"]["increment"] == 4
        assert parsed["last_increment"]["step_time"] == 1.0

    def test_parse_dat_file_synthetic(self, tmp_path):
        """Verify .dat file parser correctly detects completion and times."""
        dat_file = tmp_path / "test.dat"
        dat_content = (
            "   ABAQUS VERSION 2023\n"
            "   ANALYSIS DATACHECK COMPLETE\n"
            "   THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n"
            "   JOB TIME SUMMARY\n"
            "     TOTAL CPU TIME (SEC) =     12.34\n"
            "     WALLCLOCK TIME (SEC) =        14\n"
        )
        dat_file.write_text(dat_content, encoding="utf-8")
        
        parsed = parse_dat_file(str(dat_file))
        assert parsed["exists"] is True
        assert parsed["analysis_complete"] is True
        assert parsed["datacheck_complete"] is True
        assert parsed["cpu_time_s"] == 12.34
        assert parsed["wallclock_time_s"] == 14.0

    def test_parse_energy_csv_synthetic(self, tmp_path):
        """Verify energy CSV parser extracts final energies correctly."""
        csv_file = tmp_path / "uel_energy_balance.csv"
        csv_content = (
            "Step,Increment,StepTime,TotalTime,E_elas,E_frac,E_tot,W_ext,Delta_book\n"
            "1,1,0.5,0.5,0.800000,0.015000,0.815000,0.815050,0.000050\n"
            "1,2,1.0,1.0,1.632700,0.030660,1.663360,1.663400,0.000040\n"
        )
        csv_file.write_text(csv_content, encoding="utf-8")
        
        parsed = parse_energy_csv(str(csv_file))
        assert parsed["exists"] is True
        assert parsed["rows_count"] == 2
        last = parsed["last_row"]
        assert last["step"] == 1
        assert last["increment"] == 2
        assert last["e_elas_mJ"] == pytest.approx(1.632700)
        assert last["e_frac_mJ"] == pytest.approx(0.030660)
        assert last["e_tot_mJ"] == pytest.approx(1.663360)
        assert last["delta_book_mJ"] == pytest.approx(0.000040)

    def test_evaluate_equilibrium_results_pass_scenario(self, tmp_path):
        """Verify full evaluation pipeline returns PASS when within acceptance thresholds."""
        # Create mock run directory
        sta_file = tmp_path / "M1_MC_STAGE_C1_1_EQUIL.sta"
        sta_file.write_text(
            "   STEP   INC  ATT  SEVERE  EQUIL  TOTAL     TOTAL       STEP       INC OF\n"
            "      1     1    1       0      3      3  1.0000000   1.0000000   1.0000000\n"
            " THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n"
        )
        
        dat_file = tmp_path / "M1_MC_STAGE_C1_1_EQUIL.dat"
        dat_file.write_text(
            " THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n"
            " TOTAL CPU TIME (SEC) = 5.2\n"
            " WALLCLOCK TIME (SEC) = 6\n"
        )
        
        energy_file = tmp_path / "uel_energy_balance.csv"
        energy_file.write_text(
            "Step,Increment,StepTime,TotalTime,E_elas,E_frac,E_tot,W_ext,Delta_book\n"
            "1,1,1.0,1.0,1.632800,0.030670,1.663470,1.663500,0.000030\n"
        )
        
        rf_file = tmp_path / "reaction_force.csv"
        rf_file.write_text(
            "Increment,Time,RF2\n"
            "1,1.0,653.1500\n"
        )
        
        result = evaluate_equilibrium_results(str(tmp_path))
        assert result["status"] == "PASS"
        assert result["all_criteria_passed"] is True
        assert result["checks"]["criterion_1_rf_continuity"]["passed"] is True
        assert result["checks"]["criterion_2_peak_damage"]["passed"] is True
        assert result["checks"]["criterion_3_elastic_energy"]["passed"] is True
        assert result["checks"]["criterion_4_fracture_energy"]["passed"] is True
        assert result["checks"]["criterion_5_total_energy"]["passed"] is True
        assert result["checks"]["criterion_6_energy_residual"]["passed"] is True
        assert result["checks"]["criterion_7_convergence"]["passed"] is True
