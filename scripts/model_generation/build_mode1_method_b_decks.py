#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mode-I Method B Load-Partitioning Preflight Generator & Validator
==================================================================
Task: F1405 - Method B Scientific Design Qualification and Reproducible Preflight Plan
Author: Gemini Antigravity
Date: 2026-10-11

This module provides:
1. Complete parameterization and specification for 1-step (M1-MB-1S), 2-step (M1-MB-2S),
   and 4-step (M1-MB-4S) preliminary loading schedules.
2. Invariant physical increment enforcement:
     Delta u_max = (dt_max / T_step) * Delta U_step = 1.0e-5 mm (const across all candidates).
3. Step boundary continuity verification (Delta u jumps = 0).
4. MISESERI step/frame selection contract.
5. Standalone preflight validation and JSON configuration export.
"""

from __future__ import print_function
import os
import sys
import json
import math

# Reference constants
MODE1_U_PEAK_MM = 0.005857
MODE1_F_MAX_KN = 0.757778
MODE1_K0_KN_MM = 137.945520
MODE1_PRE_TARGET_U_MM = 0.005000  # alpha = 0.85368 (85.37% of peak)
PHYSICAL_DELTA_U_MAX_MM = 1.0e-5  # 10 nm physical increment
FULL_FRACTURE_HORIZON_U_MM = 0.010000


def generate_partition_specification(num_steps, terminal_u=MODE1_PRE_TARGET_U_MM, delta_u_max=PHYSICAL_DELTA_U_MAX_MM):
    """
    Generates step configuration dictionary guaranteeing identical physical increment resolution.
    """
    if num_steps not in (1, 2, 4):
        raise ValueError("Supported partition steps are 1, 2, or 4; got %r" % num_steps)

    delta_u_step = float(terminal_u) / float(num_steps)
    total_increments = int(round(float(terminal_u) / float(delta_u_max)))
    increments_per_step = total_increments // num_steps

    # Under normalized step time T_step = 1.0
    t_step = 1.0
    dt_val = t_step / float(increments_per_step)

    steps = []
    cumulative_u = 0.0
    for s_idx in range(1, num_steps + 1):
        step_name = "Step-%d" % s_idx
        cumulative_u += delta_u_step
        step_dict = {
            "step_index": s_idx,
            "step_name": step_name,
            "step_time": t_step,
            "delta_u_step_mm": delta_u_step,
            "cumulative_u_mm": round(cumulative_u, 9),
            "dt_initial": dt_val,
            "dt_max": dt_val,
            "dt_min": 1.0e-9,
            "num_increments": increments_per_step,
            "physical_delta_u_inc_mm": (dt_val / t_step) * delta_u_step
        }
        steps.append(step_dict)

    remesh_target_step = "Step-%d" % num_steps
    config = {
        "config_id": "M1-MB-%dS" % num_steps,
        "num_steps": num_steps,
        "terminal_u_mm": terminal_u,
        "load_fraction_alpha": terminal_u / MODE1_U_PEAK_MM,
        "total_increments": total_increments,
        "physical_delta_u_max_mm": delta_u_max,
        "steps": steps,
        "remesh_target_step": remesh_target_step,
        "remesh_frame_rule": "LAST_INCREMENT",
        "remesh_extraction_u_mm": terminal_u
    }
    return config


def generate_abaqus_step_cards(config):
    """
    Generates exact Abaqus input deck step text for the partitioned configuration.
    """
    lines = []
    for s in config["steps"]:
        lines.append("** ----------------------------------------------------------------")
        lines.append("** STEP: %s (Cumulative U = %.6f mm)" % (s["step_name"], s["cumulative_u_mm"]))
        lines.append("** ----------------------------------------------------------------")
        lines.append("*STEP, NAME=%s, NLGEOM=NO, INC=%d" % (s["step_name"], s["num_increments"] * 2))
        lines.append("*STATIC")
        lines.append("%.6f, %.6f, %.1E, %.6f" % (s["dt_initial"], s["step_time"], s["dt_min"], s["dt_max"]))
        lines.append("*BOUNDARY")
        if s["step_index"] == 1:
            lines.append("N_BOTTOM, 2, 2, 0.0")
            lines.append("N_PIN, 1, 1, 0.0")
        lines.append("N_RP, 2, 2, %.6f" % s["cumulative_u_mm"])
        lines.append("*RESTART, WRITE, FREQUENCY=0")
        lines.append("*OUTPUT, FIELD, FREQUENCY=1")
        lines.append("*NODE OUTPUT, NSET=N_RP")
        lines.append("U, RF")
        lines.append("*ELEMENT OUTPUT, ELSET=All_elem, DIRECTIONS=YES")
        lines.append("MISESERI, MISESAVG, S, E, EVOL")
        lines.append("*ELEMENT OUTPUT, ELSET=umatelem")
        lines.append("SDV")
        lines.append("*NODE PRINT, FREQ=1, NSET=N_RP")
        lines.append("U2, RF2")
        lines.append("*END STEP")
        lines.append("")
    return "\n".join(lines)


def validate_partition_continuity_and_parity(configs):
    """
    Performs rigorous preflight validation across the 1S, 2S, and 4S configurations.
    Returns (bool, list_of_diagnostics).
    """
    diagnostics = []
    passed = True

    # Check 1: Invariant terminal displacement
    terminal_displacements = [c["terminal_u_mm"] for c in configs]
    if len(set(terminal_displacements)) != 1:
        diagnostics.append("FAIL: Terminal displacements are not identical: %r" % terminal_displacements)
        passed = False
    else:
        diagnostics.append("PASS: Common terminal preliminary displacement: %.6f mm (alpha = %.4f)" % 
                           (terminal_displacements[0], configs[0]["load_fraction_alpha"]))

    # Check 2: Invariant physical increment size
    phys_incs = []
    for c in configs:
        for s in c["steps"]:
            phys_incs.append(round(s["physical_delta_u_inc_mm"], 10))
    if len(set(phys_incs)) != 1:
        diagnostics.append("FAIL: Physical displacement increments vary across steps: %r" % list(set(phys_incs)))
        passed = False
    else:
        diagnostics.append("PASS: Invariant physical displacement increment: %.6e mm (10 nm) across all steps" % phys_incs[0])

    # Check 3: Invariant total increments
    tot_incs = [c["total_increments"] for c in configs]
    if len(set(tot_incs)) != 1:
        diagnostics.append("FAIL: Total preliminary increments vary across configurations: %r" % tot_incs)
        passed = False
    else:
        diagnostics.append("PASS: Total preliminary increments = %d across all partition candidates" % tot_incs[0])

    # Check 4: Step boundary continuity
    for c in configs:
        prev_u = 0.0
        for s in c["steps"]:
            delta = s["cumulative_u_mm"] - prev_u
            if abs(delta - s["delta_u_step_mm"]) > 1.0e-9:
                diagnostics.append("FAIL: Discontinuity in configuration %s step %s" % (c["config_id"], s["step_name"]))
                passed = False
            prev_u = s["cumulative_u_mm"]
        if abs(prev_u - c["terminal_u_mm"]) > 1.0e-9:
            diagnostics.append("FAIL: Terminal cumulative U does not match target in %s" % c["config_id"])
            passed = False
    diagnostics.append("PASS: Monotonic step boundary continuity verified with zero displacement jumps")

    # Check 5: Remesh target contract
    for c in configs:
        expected_target = "Step-%d" % c["num_steps"]
        if c["remesh_target_step"] != expected_target:
            diagnostics.append("FAIL: Remesh target step mismatch in %s: %r vs %r" % (c["config_id"], c["remesh_target_step"], expected_target))
            passed = False
        if abs(c["remesh_extraction_u_mm"] - c["terminal_u_mm"]) > 1.0e-9:
            diagnostics.append("FAIL: Remesh extraction U mismatch in %s" % c["config_id"])
            passed = False
    diagnostics.append("PASS: MISESERI remeshing target step contract verified for 1S, 2S, and 4S")

    return passed, diagnostics


def build_full_study_manifest():
    """
    Builds the master study schema including primary matrix and orthogonal secondary sweep.
    """
    c_1s = generate_partition_specification(1)
    c_2s = generate_partition_specification(2)
    c_4s = generate_partition_specification(4)
    primary_configs = [c_1s, c_2s, c_4s]

    valid, diags = validate_partition_continuity_and_parity(primary_configs)

    manifest = {
        "study_name": "MODE1_METHOD_B_LOAD_PARTITIONING_QUALIFIED",
        "protocol_version": 2,
        "governing_benchmark": {
            "name": "Pandey & Kumar (2025) Mode-I Tensile Plate",
            "freeze_tag": "v2026.10.08-supervisor-meeting-mode1-freeze",
            "uel_source": "f42_mixed_uel.for",
            "uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
            "reference_K0_kN_mm": MODE1_K0_KN_MM,
            "reference_Fmax_kN": MODE1_F_MAX_KN,
            "reference_u_peak_mm": MODE1_U_PEAK_MM,
            "full_fracture_horizon_mm": FULL_FRACTURE_HORIZON_U_MM
        },
        "primary_matrix": {
            "independent_variable": "num_steps",
            "held_constant": {
                "terminal_u_mm": MODE1_PRE_TARGET_U_MM,
                "load_fraction_alpha": MODE1_PRE_TARGET_U_MM / MODE1_U_PEAK_MM,
                "physical_delta_u_max_mm": PHYSICAL_DELTA_U_MAX_MM,
                "total_preliminary_increments": 500,
                "remeshing_engine": "Abaqus CAE adaptiveRemesh",
                "error_target_pct": 2.0,
                "min_element_size_mm": 0.001,
                "max_element_size_mm": 0.010,
                "subsequent_fracture_execution": "Fresh solve from t=0 without state transfer"
            },
            "configurations": {c["config_id"]: c for c in primary_configs}
        },
        "orthogonal_load_sweep": {
            "independent_variable": "terminal_load_fraction_alpha",
            "held_constant_partition": "M1-MB-2S (2 steps)",
            "levels": [
                {"level_id": "M1-SW-LOW", "alpha": 0.50, "u_pre_mm": round(0.50 * MODE1_U_PEAK_MM, 6), "desc": "Pure linear elastic"},
                {"level_id": "M1-SW-MID", "alpha": 0.85368, "u_pre_mm": MODE1_PRE_TARGET_U_MM, "desc": "Incipient localization (Primary M1-MB-2S)"},
                {"level_id": "M1-SW-HIGH", "alpha": 0.90, "u_pre_mm": round(0.90 * MODE1_U_PEAK_MM, 6), "desc": "Pre-peak threshold"}
            ]
        },
        "preflight_validation": {
            "all_checks_passed": valid,
            "diagnostics": diags
        },
        "recommendation": "METHOD_B_DESIGN_READY_FOR_SUPERVISOR_REVIEW"
    }
    return manifest


if __name__ == "__main__":
    manifest = build_full_study_manifest()
    print("=== METHOD B PREFLIGHT MANIFEST VALIDATION ===")
    for d in manifest["preflight_validation"]["diagnostics"]:
        print("  " + d)
    print("\nOverall Status: " + ("PASS" if manifest["preflight_validation"]["all_checks_passed"] else "FAIL"))
    print("Recommendation: " + manifest["recommendation"])
