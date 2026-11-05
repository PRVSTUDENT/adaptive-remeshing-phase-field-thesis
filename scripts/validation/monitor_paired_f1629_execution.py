#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
monitor_paired_f1629_execution.py
=================================
Compares live and terminal telemetry between Arm A (Package 174 / M1_C6_R12_PICARD_BASELINE)
and Arm B (Package 175 / M1_C6_R12_ANDERSON_M2) under Task F1629.
"""

import json
import sys
from pathlib import Path

RUNS_DIR = Path("/scratch9/pr21vyci/runs")
P174_DIR = RUNS_DIR / "mode1_c6_r12_picard_baseline"
P175_DIR = RUNS_DIR / "mode1_c6_r12_anderson_m2"


def find_latest_eq_dir(pkg_dir: Path):
    if not pkg_dir.is_dir():
        return None
    candidates = sorted(pkg_dir.glob("equilibration_*"))
    return candidates[-1] if candidates else None


def load_telemetry(eq_dir: Path):
    if not eq_dir:
        return []
    telem_file = eq_dir / "live_iteration_telemetry.json"
    if not telem_file.is_file():
        return []
    try:
        with open(telem_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def check_terminal_status(eq_dir: Path):
    if not eq_dir:
        return "NOT_STARTED"
    ckpt = eq_dir / "converged_checkpoint.json"
    if ckpt.is_file():
        return "CONVERGED_CHECKPOINT_ACCEPTED"
    eval_summary = eq_dir / "evaluation_summary.json"
    if eval_summary.is_file():
        return "COMPLETED_EVALUATED"
    return "RUNNING"


def main():
    eq174 = find_latest_eq_dir(P174_DIR)
    eq175 = find_latest_eq_dir(P175_DIR)

    t174 = load_telemetry(eq174)
    t175 = load_telemetry(eq175)

    s174 = check_terminal_status(eq174)
    s175 = check_terminal_status(eq175)

    print("=" * 125)
    print(f"{'TASK F1629 PAIRED C6 R12 CONTROLLED OVERNIGHT EXECUTION MONITOR':^125}")
    print("=" * 125)
    print(f"Arm A (Package 174 / Picard Baseline): Dir = {eq174.name if eq174 else 'None'} | Status = {s174} | Iterations = {len(t174)}")
    print(f"Arm B (Package 175 / Anderson M2):     Dir = {eq175.name if eq175 else 'None'} | Status = {s175} | Iterations = {len(t175)}")
    print("-" * 125)
    print(f"{'Outer':>5} | {'Arm A (Picard Baseline)':^56} | {'Arm B (Anderson M2)':^56}")
    print(f"{'':>5} | {'Stg':>3} {'|A|':>5} {'|dA|':>4} {'+A':>3} {'Delta_d':>11} {'Delta_u [mm]':>11} {'Delta_H':>10} | {'Stg':>3} {'|A|':>5} {'|dA|':>4} {'+A':>3} {'Delta_d':>11} {'Delta_u [mm]':>11} {'Delta_H':>10}")
    print("-" * 125)

    max_iters = max(len(t174), len(t175))
    if max_iters == 0:
        print(f"{'No iteration telemetry generated yet':^125}")
        print("=" * 125)
        return

    # Sample every 5 iterations plus recent tail
    recent_tail = set(range(max(0, max_iters - 10), max_iters))
    sample_indices = sorted(list(set(list(range(0, max_iters, 5)) + list(recent_tail) + [max(0, len(t174) - 1), max(0, len(t175) - 1)])))

    for idx in sample_indices:
        row1 = t174[idx] if idx < len(t174) else None
        row2 = t175[idx] if idx < len(t175) else None

        outer_num = (row1["outer"] if row1 else row2["outer"]) if (row1 or row2) else idx + 1

        if row1:
            stg1 = row1.get("stage", 1)
            act1 = row1.get("pdas_active_count", 0)
            sym1 = row1.get("delta_active_symmetric", "-")
            add1 = row1.get("newly_activated_nodes", "-")
            dd1 = f"{row1.get('delta_d', 0.0):.4e}"
            du1 = f"{row1.get('delta_u', 0.0):.4e}"
            dh1 = f"{row1.get('delta_history', 0.0):.4e}"
            txt1 = f"{stg1:>3} {act1:>5} {sym1:>4} {add1:>3} {dd1:>11} {du1:>11} {dh1:>10}"
        else:
            txt1 = f"{'--':^56}"

        if row2:
            stg2 = row2.get("stage", 1)
            act2 = row2.get("pdas_active_count", 0)
            sym2 = row2.get("delta_active_symmetric", "-")
            add2 = row2.get("newly_activated_nodes", "-")
            dd2 = f"{row2.get('delta_d', 0.0):.4e}"
            du2 = f"{row2.get('delta_u', 0.0):.4e}"
            dh2 = f"{row2.get('delta_history', 0.0):.4e}"
            txt2 = f"{stg2:>3} {act2:>5} {sym2:>4} {add2:>3} {dd2:>11} {du2:>11} {dh2:>10}"
        else:
            txt2 = f"{'--':^56}"

        print(f"{outer_num:>5} | {txt1} | {txt2}")

    print("=" * 125)


if __name__ == "__main__":
    main()
