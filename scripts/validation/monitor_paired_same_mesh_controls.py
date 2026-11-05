#!/usr/bin/env python3
"""
scripts/validation/monitor_paired_same_mesh_controls.py
Compares live or terminal telemetry between Arm 1 (Package 172 / Old Control)
and Arm 2 (Package 173 / Corrected Control) under Task F1626.
"""

import json
from pathlib import Path

RUNS_DIR = Path("/scratch9/pr21vyci/runs")
P172_DIR = RUNS_DIR / "mode1_c5_package172_old_control"
P173_DIR = RUNS_DIR / "mode1_c5_package173_corrected_control"


def find_latest_eq_dir(pkg_dir: Path):
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
    eq172 = find_latest_eq_dir(P172_DIR)
    eq173 = find_latest_eq_dir(P173_DIR)

    t172 = load_telemetry(eq172)
    t173 = load_telemetry(eq173)

    s172 = check_terminal_status(eq172)
    s173 = check_terminal_status(eq173)

    print("=" * 115)
    print(f"{'TASK F1626 PAIRED SAME-MESH CONTROL TELEMETRY COMPARISON':^115}")
    print("=" * 115)
    print(f"Arm 1 (Package 172 / Old Control):       Dir = {eq172.name if eq172 else 'None'} | Status = {s172} | Iterations = {len(t172)}")
    print(f"Arm 2 (Package 173 / Corrected Control): Dir = {eq173.name if eq173 else 'None'} | Status = {s173} | Iterations = {len(t173)}")
    print("-" * 115)
    print(f"{'Outer':>5} | {'Arm 1 (Old Control / Averaged)':^52} | {'Arm 2 (Corrected Control / Isoparametric)':^52}")
    print(f"{'':>5} | {'Stg':>3} {'|A|':>5} {'|dA|':>4} {'+A':>3} {'Delta_d':>11} {'Delta_u [mm]':>11} {'Delta_H':>10} | {'Stg':>3} {'|A|':>5} {'|dA|':>4} {'+A':>3} {'Delta_d':>11} {'Delta_u [mm]':>11} {'Delta_H':>10}")
    print("-" * 115)

    max_iters = max(len(t172), len(t173))
    # Sample every 5 iterations plus recent tail
    recent_tail = set(range(max(0, max_iters - 8), max_iters))
    sample_indices = sorted(list(set(list(range(0, max_iters, 5)) + list(recent_tail) + [max(0, len(t172) - 1), max(0, len(t173) - 1)])))

    for idx in sample_indices:
        row1 = t172[idx] if idx < len(t172) else None
        row2 = t173[idx] if idx < len(t173) else None

        outer_num = (row1["outer"] if row1 else row2["outer"]) if (row1 or row2) else idx + 1

        if row1:
            stg1 = row1.get("stage", 1)
            act1 = row1.get("pdas_active_count", 0)
            sym1 = row1.get("delta_active_symmetric", "-")
            add1 = row1.get("added_nodes_count", "-")
            sym1_s = f"{sym1:>4}" if sym1 is not None else "   -"
            add1_s = f"{add1:>3}" if add1 is not None else "  -"
            dd1 = row1.get("delta_d", 0.0)
            du1 = row1.get("delta_u", 0.0) or 0.0
            dh1 = row1.get("delta_h", 0.0) or 0.0
            s1_str = f"{stg1:>3} {act1:>5} {sym1_s} {add1_s} {dd1:>11.4e} {du1:>11.4e} {dh1:>10.3e}"
        else:
            s1_str = f"{'--':>3} {'--':>5} {'--':>4} {'--':>3} {'--':>11} {'--':>11} {'--':>10}"

        if row2:
            stg2 = row2.get("stage", 1)
            act2 = row2.get("pdas_active_count", 0)
            sym2 = row2.get("delta_active_symmetric", "-")
            add2 = row2.get("added_nodes_count", "-")
            sym2_s = f"{sym2:>4}" if sym2 is not None else "   -"
            add2_s = f"{add2:>3}" if add2 is not None else "  -"
            dd2 = row2.get("delta_d", 0.0)
            du2 = row2.get("delta_u", 0.0) or 0.0
            dh2 = row2.get("delta_h", 0.0) or 0.0
            s2_str = f"{stg2:>3} {act2:>5} {sym2_s} {add2_s} {dd2:>11.4e} {du2:>11.4e} {dh2:>10.3e}"
        else:
            s2_str = f"{'--':>3} {'--':>5} {'--':>4} {'--':>3} {'--':>11} {'--':>11} {'--':>10}"

        print(f"{outer_num:>5} | {s1_str} | {s2_str}")

    print("=" * 115)


if __name__ == "__main__":
    main()
