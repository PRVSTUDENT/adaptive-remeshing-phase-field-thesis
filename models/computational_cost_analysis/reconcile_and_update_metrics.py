#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
models/computational_cost_analysis/reconcile_and_update_metrics.py
Generates reconciled, fully-attributed, and audited JSON and CSV metrics for
Cases 1, 2, 3, and 5 under Goal METHOD_C_COST_ANALYSIS_V1.
Addresses Gaps GAP-1 through GAP-9 from Independent Structured Review HND-METHOD-C-COST-ANALYSIS-003.
"""

import os
import json
import csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def update_case1():
    c1_dir = os.path.join(BASE_DIR, "case1")
    
    # Per-cycle data from METHOD_C_CASE1_FULL_RUN_SUMMARY.json
    per_cycle = [
        {"cycle": 0, "job_name": "PK_METHOD_C_CASE1_COARSE_JOB1", "wall_time_s": 413.0, "cpu_time_s": 385.0, "increments": 550, "iterations": 2761, "elements": 2906, "nodes": 2988, "d_max": 0.140479, "rf2_kn": 0.765856},
        {"cycle": 1, "job_name": "PK_METHOD_C_CASE1_CYCLE1", "wall_time_s": 56.4, "cpu_time_s": 46.0, "increments": 30, "iterations": 188, "elements": 5417, "nodes": 5464, "d_max": 0.968745, "rf2_kn": 0.824695, "gate_delta_rf2_pct": -0.8738, "gate_pass": True},
        {"cycle": 2, "job_name": "PK_METHOD_C_CASE1_CYCLE2", "wall_time_s": 70.3, "cpu_time_s": 60.0, "increments": 40, "iterations": 241, "elements": 5417, "nodes": 5464, "d_max": 0.996358, "rf2_kn": 0.708187, "gate_delta_rf2_pct": -0.4969, "gate_pass": True},
        {"cycle": 3, "job_name": "PK_METHOD_C_CASE1_CYCLE3", "wall_time_s": 271.2, "cpu_time_s": 259.0, "increments": 142, "iterations": 763, "elements": 6513, "nodes": 6545, "d_max": 0.998743, "rf2_kn": 0.425545, "gate_delta_rf2_pct": -0.5113, "gate_pass": True},
        {"cycle": 4, "job_name": "PK_METHOD_C_CASE1_CYCLE4", "wall_time_s": 233.7, "cpu_time_s": 221.0, "increments": 95, "iterations": 501, "elements": 8553, "nodes": 8548, "d_max": 1.000000, "rf2_kn": 0.010084, "gate_delta_rf2_pct": -4.2914, "gate_pass": True}
    ]

    c1_json = {
        "case_id": 1,
        "benchmark": "Pandey & Kumar (2025) Section 4.1 Mode-I Edge-Cracked Plate (Case 1)",
        "provenance": "NEW_1CPU_HPC_EXECUTION_UNDER_THIS_GOAL",
        "hpc_execution": True,
        "metrics": {
            "wall_time_s": {"normal": 1369.0, "method_c": 1044.6, "speedup": 1.3106, "reduction_pct": 23.70},
            "cpu_time_s": {"normal": 1360.0, "method_c": 971.0, "speedup": 1.4006, "reduction_pct": 28.60},
            "increments": {"normal": 568, "method_c": 857, "ratio_mc_to_normal": 1.5088},
            "iterations": {"normal": 2937, "method_c": 4454, "ratio_mc_to_normal": 1.5165},
            "elements": {"normal_fixed": 9714, "method_c_initial": 2906, "method_c_terminal": 8553, "ratio_terminal_to_normal": 0.8805, "reduction_pct": 11.95},
            "dofs": {"normal_fixed": 29177, "method_c_peak": 25670, "ratio_mc_to_normal": 0.8798, "reduction_pct": 12.02},
            "peak_memory_mb": {"normal": 2048.0, "method_c": 2048.0, "ratio_mc_to_normal": 1.0},
            "peak_rf2_kn": {"normal": 0.770876, "method_c": 0.824695, "diff_pct": 6.98},
            "terminal_rf2_kn": {"normal": 0.000843, "method_c": 0.010084},
            "terminal_u2_mm": {"normal": 0.008401, "method_c": 0.009951},
            "load_drop_pct": {"normal": 99.89, "method_c": 98.78},
            "transfer_gates": {
                "cycles_evaluated": 4,
                "cycles_passed": 4,
                "pass_rate_pct": 100.0,
                "max_delta_rf2_pct": 4.2914,
                "gate_threshold_pct": 5.0,
                "zero_healing_pass": True,
                "per_cycle_delta_rf2_pct": [-0.8738, -0.4969, -0.5113, -4.2914]
            },
            "disk_output": {
                "retained_size_mb": {"normal": 7.00, "method_c": 21.50},
                "pre_purge_scratch_total_mb": {"normal": 7.00, "method_c": 4710.89},
                "pre_purge_breakdown_method_c": {
                    "raw_odb_mb": 869.75,
                    "logs_and_summaries_mb": 3.61,
                    "temporary_solver_scratch_purged_mb": 3837.53
                },
                "accounting_note": "Table 3.3 in report presents retained post-purge outputs (21.50 MB Method C vs 7.00 MB normal). Raw temporary scratch before cleanup on /scratchtemp reached 4,710.89 MB across 5 solver cycles."
            }
        },
        "normal_raw": {
            "pbs_job_id": "1425060.mmaster02",
            "job_name": "PK_COST_C1_NORM",
            "analysis_type": "NORMAL_BASELINE",
            "wall_time_s": 1369.0,
            "cpu_time_s": 1360.0,
            "total_increments": 568,
            "total_iterations": 2937,
            "cutbacks": 0,
            "physical_elements": 9714,
            "active_dofs": 29177,
            "peak_rf2_kn": 0.770876,
            "terminal_rf2_kn": 0.000843,
            "terminal_u2_mm": 0.008401,
            "output_size_retained_mb": 7.00,
            "output_size_logs_mb": 2.29
        },
        "method_c_raw": {
            "pbs_job_id": "1425061.mmaster02",
            "job_name": "PK_COST_C1_MC",
            "analysis_type": "METHOD_C_ADAPTIVE",
            "total_cycles": 5,
            "wall_time_s": 1044.6,
            "cpu_time_s": 971.0,
            "total_increments": 857,
            "total_iterations": 4454,
            "initial_elements": 2906,
            "terminal_elements": 8553,
            "peak_elements": 8553,
            "peak_active_dofs": 25670,
            "peak_rf2_kn": 0.824695,
            "terminal_rf2_kn": 0.010084,
            "terminal_u2_mm": 0.009951,
            "output_size_retained_mb": 21.50,
            "output_size_pre_purge_mb": 4710.89,
            "per_cycle_metrics": per_cycle
        }
    }

    with open(os.path.join(c1_dir, "case1_cost_comparison.json"), "w", encoding="utf-8") as f:
        json.dump(c1_json, f, indent=2)

    c1_csv_rows = [
        ["Metric", "Normal_Baseline_Job_1425060", "Method_C_Adaptive_Job_1425061", "Comparison_Ratio_or_Speedup"],
        ["Wall Time (s)", "1369.00", "1044.60", "1.31x Speedup (23.70% reduction)"],
        ["CPU Time (s)", "1360.00", "971.00", "1.40x Speedup (28.60% reduction)"],
        ["Increments", "568", "857", "1.51x"],
        ["Iterations", "2937", "4454", "1.52x"],
        ["Physical Elements", "9714 (fixed)", "8553 (terminal)", "11.95% Element Reduction"],
        ["Active DOFs", "29177 (fixed)", "25670 (peak)", "12.02% DOF Reduction"],
        ["Peak Memory (MB)", "2048.0", "2048.0", "1.00x"],
        ["Peak Force RF2 (kN)", "0.770876", "0.824695", "+6.98%"],
        ["Terminal Force RF2 (kN)", "0.000843", "0.010084", "Full Severance (<1.3% peak)"],
        ["Terminal Disp u2 (mm)", "0.008401", "0.009951", "Consistent Fracture Endpoint"],
        ["Force Continuity Gates", "N/A", "4/4 PASS (max 4.29% <= 5%)", "100% Pass Rate"],
        ["Damage Monotonicity", "Monotonic", "Zero Healing Verified", "Pass"],
        ["Retained Output Size (MB)", "7.00", "21.50", "Post-purge committed size"],
        ["Pre-Purge Scratch Size (MB)", "7.00", "4710.89", "Raw solver scratch on /scratchtemp"]
    ]

    with open(os.path.join(c1_dir, "case1_cost_comparison.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(c1_csv_rows)
    print("Updated Case 1 JSON and CSV.")


def update_case2():
    c2_dir = os.path.join(BASE_DIR, "case2")

    per_cycle = [
        {"cycle": 0, "job_name": "PK_METHOD_C_CASE2_COARSE_JOB1", "wall_time_s": 40.0, "cpu_time_s": 37.0, "increments": 50, "iterations": 258, "elements": 2906, "nodes": 3010, "d_max": 0.145976, "rf2_kn": 0.542411},
        {"cycle": 1, "job_name": "PK_METHOD_C_CASE2_CYCLE1", "wall_time_s": 94.1, "cpu_time_s": 83.0, "increments": 29, "iterations": 183, "elements": 9959, "nodes": 9970, "d_max": 0.658910, "rf2_kn": 0.619999, "gate_delta_rf2_pct": -1.0945, "gate_pass": True},
        {"cycle": 2, "job_name": "PK_METHOD_C_CASE2_CYCLE2", "wall_time_s": 103.2, "cpu_time_s": 92.0, "increments": 33, "iterations": 204, "elements": 9959, "nodes": 9970, "d_max": 0.984949, "rf2_kn": 0.566304, "gate_delta_rf2_pct": -0.2533, "gate_pass": True},
        {"cycle": 3, "job_name": "PK_METHOD_C_CASE2_CYCLE3", "wall_time_s": 87.0, "cpu_time_s": 76.0, "increments": 28, "iterations": 168, "elements": 9959, "nodes": 9970, "d_max": 0.993154, "rf2_kn": 0.523149, "gate_delta_rf2_pct": -1.1832, "gate_pass": True},
        {"cycle": 4, "job_name": "PK_METHOD_C_CASE2_CYCLE4", "wall_time_s": 324.9, "cpu_time_s": 312.0, "increments": 112, "iterations": 593, "elements": 9959, "nodes": 9970, "d_max": 0.997803, "rf2_kn": 0.011462, "gate_delta_rf2_pct": -0.3068, "gate_pass": True}
    ]

    c2_json = {
        "case_id": 2,
        "benchmark": "Master Thesis Mode-I Edge-Notched Plate with Off-Axis Hole (Case 2)",
        "provenance": "NEW_1CPU_HPC_EXECUTION_UNDER_THIS_GOAL",
        "hpc_execution": True,
        "metrics": {
            "wall_time_s": {
                "normal": 1693.0,
                "method_c_successful_job_1425064": 649.2,
                "speedup_successful_job": 2.6078,
                "reduction_successful_job_pct": 61.65,
                "failed_cycle0_job_1425063_s": 42.0,
                "method_c_total_investment_s": 691.2,
                "speedup_total_investment": 2.4494,
                "reduction_total_investment_pct": 59.17
            },
            "cpu_time_s": {
                "normal": 1690.0,
                "method_c_successful_job_1425064": 600.0,
                "speedup_successful_job": 2.8167,
                "reduction_successful_job_pct": 64.50,
                "failed_cycle0_job_1425063_s": 40.0,
                "method_c_total_investment_s": 640.0,
                "speedup_total_investment": 2.6406,
                "reduction_total_investment_pct": 62.13
            },
            "increments": {"normal": 598, "method_c": 252, "ratio_mc_to_normal": 0.4214, "reduction_pct": 57.86},
            "iterations": {"normal": 3053, "method_c": 1406, "ratio_mc_to_normal": 0.4605, "reduction_pct": 53.95},
            "elements": {"normal_fixed": 12334, "method_c_initial": 2906, "method_c_terminal": 9959, "ratio_terminal_to_normal": 0.8074, "reduction_pct": 19.26},
            "dofs": {"normal_fixed": 37046, "method_c_peak": 29936, "ratio_mc_to_normal": 0.8081, "reduction_pct": 19.19},
            "peak_memory_mb": {"normal": 2048.0, "method_c": 2048.0, "ratio_mc_to_normal": 1.0},
            "peak_rf2_kn": {"normal": 0.612450, "method_c": 0.619999, "diff_pct": 1.23},
            "terminal_rf2_kn": {"normal": 0.008500, "method_c": 0.011462},
            "terminal_u2_mm": {"normal": 0.009395, "method_c": 0.009153, "endpoint_diff_pct": 2.58},
            "terminal_displacement_note": "Method C halted automatically when residual load dropped below 5% of peak (RF2 = 0.0115 kN < 0.0310 kN) at u2 = 0.009153 mm, while the fixed mesh ran to u2 = 0.009395 mm. Both runs captured full post-peak load drop (>98%).",
            "transfer_gates": {
                "cycles_evaluated": 4,
                "cycles_passed": 4,
                "pass_rate_pct": 100.0,
                "max_delta_rf2_pct": 1.1832,
                "gate_threshold_pct": 5.0,
                "zero_healing_pass": True,
                "per_cycle_delta_rf2_pct": [-1.0945, -0.2533, -1.1832, -0.3068]
            },
            "disk_output": {
                "retained_size_mb": {"normal": 8.38, "method_c": 21.14},
                "pre_purge_scratch_total_mb": {"normal": 33.99, "method_c": 602.32},
                "pre_purge_breakdown_method_c": {
                    "raw_odb_mb": 249.90,
                    "logs_and_summaries_mb": 1.47,
                    "temporary_solver_scratch_purged_mb": 350.95
                },
                "accounting_note": "Table 3.3 in report presents retained post-purge outputs (21.14 MB Method C vs 8.38 MB normal). Raw temporary scratch before cleanup on /scratchtemp reached 602.32 MB across 5 solver cycles."
            }
        },
        "normal_raw": {
            "pbs_job_id": "1425062.mmaster02",
            "job_name": "PK_COST_C2_NORM",
            "analysis_type": "NORMAL_BASELINE",
            "wall_time_s": 1693.0,
            "cpu_time_s": 1690.0,
            "total_increments": 598,
            "total_iterations": 3053,
            "cutbacks": 0,
            "physical_elements": 12334,
            "active_dofs": 37046,
            "peak_rf2_kn": 0.612450,
            "terminal_rf2_kn": 0.008500,
            "terminal_u2_mm": 0.009395,
            "output_size_retained_mb": 8.38,
            "output_size_logs_mb": 2.37
        },
        "method_c_raw": {
            "pbs_job_id": "1425064.mmaster02",
            "failed_cycle0_job_id": "1425063.mmaster02",
            "job_name": "PK_COST_C2_MC",
            "analysis_type": "METHOD_C_ADAPTIVE",
            "total_cycles": 5,
            "wall_time_s": 649.2,
            "wall_time_including_failed_job_s": 691.2,
            "cpu_time_s": 600.0,
            "cpu_time_including_failed_job_s": 640.0,
            "total_increments": 252,
            "total_iterations": 1406,
            "initial_elements": 2906,
            "terminal_elements": 9959,
            "peak_elements": 9959,
            "peak_active_dofs": 29936,
            "peak_rf2_kn": 0.619999,
            "terminal_rf2_kn": 0.011462,
            "terminal_u2_mm": 0.009153,
            "output_size_retained_mb": 21.14,
            "output_size_pre_purge_mb": 602.32,
            "per_cycle_metrics": per_cycle
        }
    }

    with open(os.path.join(c2_dir, "case2_cost_comparison.json"), "w", encoding="utf-8") as f:
        json.dump(c2_json, f, indent=2)

    c2_csv_rows = [
        ["Metric", "Normal_Baseline_Job_1425062", "Method_C_Adaptive_Job_1425064", "Comparison_Ratio_or_Speedup"],
        ["Wall Time (s) [Successful Run]", "1693.00", "649.20", "2.61x Speedup (61.65% reduction)"],
        ["Wall Time (s) [Incl Failed Job 1425063]", "1693.00", "691.20", "2.45x Speedup (59.17% reduction)"],
        ["CPU Time (s) [Successful Run]", "1690.00", "600.00", "2.82x Speedup (64.50% reduction)"],
        ["CPU Time (s) [Incl Failed Job 1425063]", "1690.00", "640.00", "2.64x Speedup (62.13% reduction)"],
        ["Increments", "598", "252", "57.86% Reduction"],
        ["Iterations", "3053", "1406", "53.95% Reduction"],
        ["Physical Elements", "12334 (fixed)", "9959 (terminal)", "19.26% Element Reduction"],
        ["Active DOFs", "37046 (fixed)", "29936 (peak)", "19.19% DOF Reduction"],
        ["Peak Memory (MB)", "2048.0", "2048.0", "1.00x"],
        ["Peak Force RF2 (kN)", "0.612450", "0.619999", "+1.23%"],
        ["Terminal Force RF2 (kN)", "0.008500", "0.011462", "Full Severance (>98% load drop)"],
        ["Terminal Disp u2 (mm)", "0.009395", "0.009153", "Method C stopped at 5% threshold"],
        ["Force Continuity Gates", "N/A", "4/4 PASS (max 1.18% <= 5%)", "100% Pass Rate"],
        ["Damage Monotonicity", "Monotonic", "Zero Healing Verified", "Pass"],
        ["Retained Output Size (MB)", "8.38", "21.14", "Post-purge committed size"],
        ["Pre-Purge Scratch Size (MB)", "33.99", "602.32", "Raw solver scratch on /scratchtemp"]
    ]

    with open(os.path.join(c2_dir, "case2_cost_comparison.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(c2_csv_rows)
    print("Updated Case 2 JSON and CSV.")


def update_case3():
    c3_dir = os.path.join(BASE_DIR, "case3")

    c3_json = {
        "case_id": 3,
        "benchmark": "Pandey & Kumar (2025) Section 4.3 (Case 3: Mode-I Cracked Plate with Holes)",
        "provenance_summary": "Case 3 Normal Baseline is a new 1-CPU HPC execution (Job 1425066). Case 3 Method C was NOT executed on HPC under this goal (Job 1425067 failed due to script error, PBS budget exhausted); data is cited from verified local Windows framework re-evaluation.",
        "hpc_execution_normal_only": True,
        "metrics": {
            "wall_time_s": {
                "normal_hpc_job_1425066": 2289.0,
                "method_c_local_workstation_reference": 2500.0,
                "note": "Not directly comparable as speedup because Normal locked prematurely at u2=0.058 mm (33% load drop) whereas Method C traversed both ligaments to complete specimen severance across 54 cycles."
            },
            "cpu_time_s": {
                "normal_hpc_job_1425066": 2280.0,
                "method_c_local_workstation_reference": 2450.0
            },
            "increments": {
                "normal_authoritative_job_1425066": 234,
                "normal_combined_including_failed_job_1425065": 307,
                "method_c_local_workstation_54_cycles": 5514,
                "increment_explanation": "Authoritative solve of Job 1425066 solved 234 increments (58 Step 1 displacement-controlled + 176 Step 2 RIKS). Earlier un-regularized job 1425065 solved 73 increments before cutback failure (234 + 73 = 307 total increments across both attempts)."
            },
            "iterations": {
                "normal_authoritative_job_1425066": 1102,
                "normal_combined_including_failed_job_1425065": 1582,
                "method_c_local_workstation_54_cycles": 16343
            },
            "elements": {
                "normal_fixed_mesh": 26431,
                "method_c_initial": 2906,
                "method_c_terminal": 28697,
                "method_c_peak": 28710
            },
            "dofs": {
                "normal_fixed_mesh": 79184,
                "method_c_active_corridor_peak": 27645,
                "method_c_global_peak": 86130,
                "corridor_dof_reduction_pct": 65.09
            },
            "physical_outcome": {
                "normal_hpc_job_1425066": "LOCKED_PREMATURELY (at u2=0.05816 mm, RF2=2.441 kN, 33% load drop due to severe unadapted mesh distortion; failed to reach central hole)",
                "method_c_local_reference": "COMPLETE_SEVERANCE (traversed both ligaments: notch to hole to far boundary, s=63.23 mm, RF2=0.00169 kN, 99.96% load drop)"
            },
            "disk_output": {
                "retained_size_mb": {"normal": 56.93, "method_c_reference": 39.56},
                "normal_odb_mb": 44.42,
                "normal_logs_mb": 1.32
            }
        },
        "normal_raw": {
            "pbs_job_id": "1425066.mmaster02",
            "failed_predecessor_job_id": "1425065.mmaster02",
            "job_name": "PK_COST_C3_COMB",
            "analysis_type": "NORMAL_BASELINE_HPC_RUN",
            "machine": "TU Freiberg HPC (1 CPU, 8 GB, normal_imfdfkmq)",
            "wall_time_s": 2289.0,
            "cpu_time_s": 2280.0,
            "total_increments": 234,
            "total_iterations": 1102,
            "cutbacks": 0,
            "physical_elements": 26431,
            "active_dofs": 79184,
            "peak_rf2_kn": 4.3318,
            "terminal_rf2_kn": 2.4410,
            "terminal_u2_mm": 0.05816,
            "output_size_retained_mb": 56.93
        },
        "method_c_raw": {
            "hpc_execution_status": "NOT_EXECUTED_ON_HPC_BUDGET_EXHAUSTED",
            "unexecuted_reason": "Job 1425067 (PK_COST_FINAL) failed after 520 s due to script syntax error during cleanup; PBS cumulative budget ceiling of 81 was reached, prohibiting further HPC submissions.",
            "reference_citation": "models/pandey_kumar_mode1/290_method_c_case3_rerun/METHOD_C_CASE3_RERUN_SUMMARY.json",
            "reference_machine": "Local Windows Workstation (4 CPUs)",
            "analysis_type": "LOCAL_WORKSTATION_METHOD_C_RE_EVALUATION",
            "total_cycles": 54,
            "wall_time_s": 2500.0,
            "cpu_time_s": 2450.0,
            "total_increments": 5514,
            "total_iterations": 16343,
            "initial_elements": 2906,
            "terminal_elements": 28697,
            "peak_elements": 28710,
            "peak_active_dofs": 27645,
            "peak_rf2_kn": 4.331822,
            "terminal_rf2_kn": 0.001694,
            "terminal_load_drop_pct": 99.96,
            "output_size_retained_mb": 39.56
        }
    }

    with open(os.path.join(c3_dir, "case3_cost_comparison.json"), "w", encoding="utf-8") as f:
        json.dump(c3_json, f, indent=2)

    # Also update case3_normal_metrics.json to reflect 234 authoritative increments
    c3_norm_metrics = {
        "job_name": "PK_COST_C3_COMB (HPC Job 1425066)",
        "analysis_type": "NORMAL_BASELINE",
        "wall_time_s": 2289.0,
        "cpu_time_s": 2280.0,
        "total_increments": 234,
        "total_iterations": 1102,
        "total_increments_including_failed_job_1425065": 307,
        "total_iterations_including_failed_job_1425065": 1582,
        "cutbacks": 0,
        "peak_memory_mb": 2048.0,
        "physical_elements": 26431,
        "total_elements": 79293,
        "nodes": 26395,
        "active_dofs": 79184,
        "output_size_total_mb": 56.93,
        "output_size_odb_mb": 44.42,
        "output_size_logs_mb": 1.32
    }
    with open(os.path.join(c3_dir, "normal", "case3_normal_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(c3_norm_metrics, f, indent=2)

    c3_csv_rows = [
        ["Metric", "Normal_Baseline_Job_1425066_HPC", "Method_C_Adaptive_Local_Reference", "Context_and_Significance"],
        ["Execution Machine", "TU Freiberg HPC (1 CPU)", "Local Workstation (4 CPU Reference)", "Not a direct 1-CPU HPC comparison"],
        ["Wall Time (s)", "2289.00", "2500.00 (approx)", "Normal locked prematurely; MC finished full path"],
        ["CPU Time (s)", "2280.00", "2450.00 (approx)", "Normal locked at u2=0.058 mm"],
        ["Increments (Authoritative)", "234 (58 Step 1 + 176 Step 2)", "5514 (across 54 cycles)", "307 incs across both normal attempts (incl job 1425065)"],
        ["Iterations (Authoritative)", "1102", "16343", "1582 iters across both normal attempts"],
        ["Physical Elements", "26431 (fixed grid)", "28697 (terminal)", "Fixed mesh suffered severe grid distortion"],
        ["Active System DOFs", "79184 (fixed)", "27645 (corridor peak)", "65.09% Reduction in Active System DOFs"],
        ["Physical Fracture Outcome", "LOCKED at u2=0.058 mm (33% drop)", "FULL SEVERANCE (99.96% drop, s=63.2 mm)", "Fixed unadapted mesh fails to complete fracture"],
        ["Retained Output Size (MB)", "56.93", "39.56", "Committed post-purge files"]
    ]

    with open(os.path.join(c3_dir, "case3_cost_comparison.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(c3_csv_rows)
    print("Updated Case 3 JSON and CSV.")


def update_case5():
    c5_dir = os.path.join(BASE_DIR, "case5")

    c5_json = {
        "case_id": 5,
        "benchmark": "Pandey & Kumar (2025) Section 4.5 (Case 5: Plate with Seven Holes)",
        "provenance_summary": "PRIOR-WORK CROSS-PLATFORM CONTEXT ONLY. Neither run was executed as a new 1-CPU HPC job under this goal (Job 1425067 failed before Part 2/3, exhausting the PBS budget). Normal is historical HPC job 1424423 (F1859_REF_C5); Method C is local Windows workstation run R2.",
        "hpc_execution_under_this_goal": False,
        "metrics": {
            "wall_time_s": {
                "normal_historical_hpc_job_1424423": 14467.0,
                "method_c_local_workstation_r2": 959.5,
                "speedup_cross_platform": 15.0776,
                "reduction_cross_platform_pct": 93.37,
                "cross_platform_warning": "This 15.08x speedup is a CROSS-PLATFORM comparison between the historical cluster reference run (14,467 s) and the local Windows workstation Method C run (959.5 s, 4 CPUs). It is NOT a 1-CPU HPC result under this goal."
            },
            "cpu_time_s": {
                "normal_historical_hpc_job_1424423": 14400.0,
                "method_c_local_workstation_r2": 910.0,
                "speedup_cross_platform": 15.8242
            },
            "increments": {"normal": 411, "method_c": 412, "ratio_mc_to_normal": 1.0024},
            "iterations": {"normal": 2150, "method_c": 1850, "ratio_mc_to_normal": 0.8605},
            "elements": {"normal_fixed": 15708, "method_c_initial": 2566, "method_c_terminal": 15708, "initial_mesh_reduction_pct": 83.66},
            "dofs": {"normal_fixed": 47124, "method_c_peak": 47124},
            "peak_rf2_kn": {"normal": 0.732, "method_c": 0.728, "diff_pct": 0.55},
            "terminal_rf2_kn": {"normal": 0.125, "method_c": 0.078},
            "fracture_path": "Traversed all 5 circular voids (h1 -> h4 -> h2 -> h5 -> h3) to far plate boundary (xtip = 1.000 mm, dmax = 0.9994, 89.3% load drop)",
            "transfer_gates": {
                "cycles_evaluated": 10,
                "cycles_passed": 10,
                "pass_rate_pct": 100.0,
                "max_delta_rf2_pct": 1.82,
                "gate_threshold_pct": 5.0,
                "zero_healing_pass": True
            },
            "disk_output": {
                "retained_size_mb": {"normal": 82.50, "method_c": 0.54}
            }
        },
        "normal_raw": {
            "hpc_execution_under_this_goal": False,
            "job_name": "F1859_REF_C5 (HPC Job 1424423)",
            "analysis_type": "HISTORICAL_HPC_REFERENCE",
            "machine": "TU Freiberg HPC cluster (prior F1859 campaign)",
            "submission_date": "2026-11-20",
            "wall_time_s": 14467.0,
            "cpu_time_s": 14400.0,
            "total_increments": 411,
            "total_iterations": 2150,
            "physical_elements": 15708,
            "active_dofs": 47124,
            "peak_rf2_kn": 0.732,
            "output_size_retained_mb": 82.50
        },
        "method_c_raw": {
            "hpc_execution_under_this_goal": False,
            "unexecuted_reason": "Job 1425067 failed at Part 1, exhausting the 8-job PBS budget ceiling (cumulative 81); no new PBS jobs permitted under this review.",
            "job_name": "METHOD_C_CASE5_LOCAL_FULL_RUN_REPORT_R2",
            "analysis_type": "LOCAL_WORKSTATION_METHOD_C",
            "machine": "Local Windows Workstation (4 CPUs, commit 56546d9ac)",
            "total_cycles": 11,
            "wall_time_s": 959.5,
            "cpu_time_s": 910.0,
            "total_increments": 412,
            "total_iterations": 1850,
            "initial_elements": 2566,
            "terminal_elements": 15708,
            "peak_elements": 15708,
            "peak_active_dofs": 47124,
            "peak_rf2_kn": 0.728,
            "terminal_rf2_kn": 0.078,
            "output_size_retained_mb": 0.54
        }
    }

    with open(os.path.join(c5_dir, "case5_cost_comparison.json"), "w", encoding="utf-8") as f:
        json.dump(c5_json, f, indent=2)

    c5_csv_rows = [
        ["Metric", "Normal_Historical_HPC_Job_1424423", "Method_C_Local_Workstation_R2", "Cross_Platform_Context_Note"],
        ["Execution Machine", "HPC cluster (historical F1859 job)", "Local Workstation (4 CPUs)", "NOT a 1-CPU HPC result under this goal"],
        ["Wall Time (s)", "14467.00 (241.1 min)", "959.50 (15.99 min)", "15.08x Cross-Platform Speedup (93.37% reduction)"],
        ["CPU Time (s)", "14400.00", "910.00", "15.82x CPU Speedup"],
        ["Increments", "411", "412", "1.00x"],
        ["Iterations", "2150", "1850", "13.95% Reduction"],
        ["Physical Elements", "15708 (fixed reference)", "2566 initial / 15708 terminal", "83.66% Initial Mesh Reduction"],
        ["Active DOFs", "47124 (fixed)", "47124 (terminal peak)", "Same resolution across multi-void corridor"],
        ["Peak Force RF2 (kN)", "0.732", "0.728", "-0.55% (excellent physical agreement)"],
        ["Fracture Trajectory", "Multi-void snap-through", "Traversed all 5 voids to far boundary", "dmax = 0.9994, 89.3% load drop"],
        ["Force Continuity Gates", "N/A", "10/10 PASS (max 1.82% <= 5%)", "100% Pass Rate"],
        ["Retained Output Size (MB)", "82.50", "0.54", "Committed report outputs"]
    ]

    with open(os.path.join(c5_dir, "case5_cost_comparison.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(c5_csv_rows)
    print("Updated Case 5 JSON and CSV.")

if __name__ == "__main__":
    update_case1()
    update_case2()
    update_case3()
    update_case5()
    print("All four benchmark metrics files updated successfully.")
