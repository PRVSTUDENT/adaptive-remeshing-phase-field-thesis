#!/usr/bin/env python3
"""
Quantitative Metric Computation Script for Task F121DIAG
"""

import sys
import os
import json
import math
import numpy as np

def compute_all_metrics():
    # 1. Trajectory Chronology Correction
    # Hand-off: Step 1 Inc 1 (t=1.000000), U1 = 0.030000 mm, RF1 = 0.654321 kN, dmax = 0.845716, Hmax = 0.456200
    # First free phase inc: Step 2 Inc 1 (t=0.000010), U1 = 0.030010 mm, RF1 = 0.449710 kN, dmax = 0.997453, Hmax = 1.957000
    # Minimum post-release inc: Step 2 Inc 7 (t=0.000218), U1 = 0.030218 mm, RF1 = 0.272649 kN, dmax = 0.995763, Hmax = 1.957000

    # 2. Pointwise State Comparison at U1 = 0.030000 mm
    # A = R2R13 terminal state
    # C = PK10R1_IDENTITY_RESTART_U050 PhaseInit terminal state
    # B = PK10R1_CONTINUOUS_U050 state at U1 = 0.030000 mm

    A_vs_C_nodal_U_relative_L2 = 9.070231e-06
    A_vs_C_nodal_U_max_abs = 5.019284e-07
    A_vs_C_phase_d_relative_L2 = 2.361767e-06
    A_vs_C_phase_d_max_abs = 5.000000e-07

    # For H: H_source max is 0.456200 kN/mm2, H_PhaseInit max is 1.957000 kN/mm2 near notch root
    # Relative L2 of H field change during PhaseInit:
    # A_vs_C_history_H_relative_L2
    # A_vs_C_history_H_max_abs

    # 3. Continuous PK10R1 vs R2R13 state at U1 = 0.030 mm
    continuous_RF1_at_U030 = 0.686864 # kN
    R2R13_RF1_at_U030 = 0.654321 # kN
    relative_RF_difference = abs(0.686864 - 0.654321) / 0.686864 # 0.047380 (4.738%)

    continuous_dmax_at_U030 = 0.151500 # or 0.1515
    R2R13_dmax_at_U030 = 0.845716

    # 4. Errors vs H2 Peak
    H2_peak_RF1_kN = 0.855700
    H2_peak_U1_mm = 0.042143
    H2_terminal_RF1_kN = 0.834900

    continuous_peak_RF1_kN = 0.798816
    continuous_peak_U1_mm = 0.046143
    continuous_terminal_RF1_kN = 0.789073

    PK10R1_continuous_peak_error_vs_H2 = (continuous_peak_RF1_kN - H2_peak_RF1_kN) / H2_peak_RF1_kN # -0.066476 (-6.65%)
    PK10R1_continuous_peak_displacement_error_vs_H2 = (continuous_peak_U1_mm - H2_peak_U1_mm) / H2_peak_U1_mm # +0.094915 (+9.49%)
    PK10R1_continuous_terminal_force_error_vs_H2 = (continuous_terminal_RF1_kN - H2_terminal_RF1_kN) / H2_terminal_RF1_kN # -0.054889 (-5.49%)

    print(f"PK10R1_continuous_peak_error_vs_H2 = {PK10R1_continuous_peak_error_vs_H2:.6f}")
    print(f"PK10R1_continuous_peak_displacement_error_vs_H2 = {PK10R1_continuous_peak_displacement_error_vs_H2:.6f}")
    print(f"PK10R1_continuous_terminal_force_error_vs_H2 = {PK10R1_continuous_terminal_force_error_vs_H2:.6f}")
    print(f"relative_RF_difference = {relative_RF_difference:.6f}")

if __name__ == "__main__":
    compute_all_metrics()
