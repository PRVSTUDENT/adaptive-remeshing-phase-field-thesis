#!/usr/bin/env python3
"""Evaluate D3A3-R4 Step-2 (F1) fixed-state KKT using actual ODB H and D3A5 active set."""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.solve_d3a4_phase_compatibility import assemble, load_mesh  # noqa: E402

EXPECTED_NODES = 6601
EXPECTED_IPS = 25600
FREE_RESIDUAL_TOL = 1.0e-8
ACTIVE_MULTIPLIER_TOL = -1.0e-8
ACTIVE_BOUND_ERROR_TOL = 1.0e-10


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bool_value(value):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "1", "yes"):
        return True
    if text in ("false", "0", "no"):
        return False
    raise ValueError("cannot parse boolean: %r" % value)


def load_recovered_f1_phase(target_dir: Path):
    phase_path = target_dir / "D3A3_R4_PHASE_NODE_STATE_BY_FRAME.csv"
    if phase_path.exists():
        rows = read_csv(phase_path)
        return {int(row["node"]): float(row["d_F1"]) for row in rows}
    recovery_path = target_dir / "D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv"
    rows = [row for row in read_csv(recovery_path) if row["frame_tag"] == "F1_equilibrated"]
    return {int(row["node"]): float(row["recovered_d_mean"]) for row in rows}


def load_f1_h(target_dir: Path):
    state_path = target_dir / "D3A3_STATE_BY_FRAME.csv"
    if not state_path.exists():
        state_path = target_dir / "D3A3_R4_STATE_BY_FRAME.csv"
    rows = [row for row in read_csv(state_path) if row["frame_tag"] == "F1_equilibrated"]
    h = {}
    for row in rows:
        key = (int(row["element"]), int(row["uel_integration_point"]))
        h[key] = float(row["odb_sdv16"])
    return h


def load_active_set(active_set_csv: Path, lower_bound_csv: Path):
    active_rows = read_csv(active_set_csv)
    lower_rows = {int(row["node"]): float(row["d_lower_bound"]) for row in read_csv(lower_bound_csv)}
    active = {}
    lower = {}
    for row in active_rows:
        node = int(row["node"])
        active[node] = bool_value(row["active_lower_bound"])
        if "d_lb" in row and row["d_lb"] not in ("", None):
            lower[node] = float(row["d_lb"])
        else:
            lower[node] = lower_rows[node]
    return active, lower


def analyze(target_dir, active_set_csv, lower_bound_csv, model_dir):
    nodes, elements = load_mesh(model_dir)
    d_by_node = load_recovered_f1_phase(target_dir)
    h_by_ip = load_f1_h(target_dir)
    active_map, lb_by_node = load_active_set(active_set_csv, lower_bound_csv)

    labels, index, k, f, assembly = assemble(nodes, elements, h_by_ip)
    d = np.array([d_by_node[node] for node in labels], dtype=float)
    active = np.array([active_map[node] for node in labels], dtype=bool)
    lb = np.array([lb_by_node[node] for node in labels], dtype=float)
    residual = np.asarray(k.dot(d) - f, dtype=float)

    free = ~active
    free_residual_inf = float(np.max(np.abs(residual[free]))) if np.any(free) else 0.0
    min_active_multiplier = float(np.min(residual[active])) if np.any(active) else 0.0
    active_bound_error = float(np.max(np.abs(d[active] - lb[active]))) if np.any(active) else 0.0

    residual_rows = []
    for i, node in enumerate(labels):
        x, y = nodes[node]
        residual_rows.append(
            {
                "node": node,
                "x": x,
                "y": y,
                "active_lower_bound": bool(active[i]),
                "d_F1": float(d[i]),
                "d_lower_bound": float(lb[i]),
                "bound_error": float(d[i] - lb[i]),
                "residual_Kd_minus_f": float(residual[i]),
                "multiplier_if_active": float(residual[i]) if active[i] else "",
            }
        )
    write_csv(
        target_dir / "D3A3_R4_F1_RESIDUAL_BY_NODE.csv",
        [
            "node",
            "x",
            "y",
            "active_lower_bound",
            "d_F1",
            "d_lower_bound",
            "bound_error",
            "residual_Kd_minus_f",
            "multiplier_if_active",
        ],
        residual_rows,
    )

    failures = []
    if len(labels) != EXPECTED_NODES:
        failures.append("node coverage = %s expected %s" % (len(labels), EXPECTED_NODES))
    if len(h_by_ip) != EXPECTED_IPS:
        failures.append("integration-point coverage = %s expected %s" % (len(h_by_ip), EXPECTED_IPS))
    if assembly["non_positive_detJ"] != 0:
        failures.append("non-positive detJ = %s" % assembly["non_positive_detJ"])
    if free_residual_inf > FREE_RESIDUAL_TOL:
        failures.append("free residual infinity norm = %s > %s" % (free_residual_inf, FREE_RESIDUAL_TOL))
    if min_active_multiplier < ACTIVE_MULTIPLIER_TOL:
        failures.append("minimum active multiplier = %s < %s" % (min_active_multiplier, ACTIVE_MULTIPLIER_TOL))
    if active_bound_error > ACTIVE_BOUND_ERROR_TOL:
        failures.append("active-node bound error = %s > %s" % (active_bound_error, ACTIVE_BOUND_ERROR_TOL))

    passed = not failures
    metrics = {
        "classification": (
            "stage_d3a3_r4_fixed_state_kkt_pass"
            if passed
            else "stage_d3a3_r4_fixed_state_needs_reprojection"
        ),
        "D3A3_R4_fixed_state_kkt_ok": passed,
        "failures": failures,
        "node_coverage": len(labels),
        "integration_point_coverage": len(h_by_ip),
        "expected_nodes": EXPECTED_NODES,
        "expected_integration_points": EXPECTED_IPS,
        "active_node_count": int(np.count_nonzero(active)),
        "free_node_count": int(np.count_nonzero(free)),
        "free_set_residual_infinity_norm": free_residual_inf,
        "minimum_active_set_multiplier": min_active_multiplier,
        "active_node_bound_error": active_bound_error,
        "non_positive_detJ": int(assembly["non_positive_detJ"]),
        "integration_points": int(assembly["integration_points"]),
        "history_field": "R4 F1_equilibrated odb_sdv16",
        "phase_field": "recovered R4 F1 phase",
        "active_set_source": str(active_set_csv),
        "assembly": "scripts.state_transfer.solve_d3a4_phase_compatibility.assemble",
    }
    write_json(target_dir / "D3A3_R4_F1_KKT_METRICS.json", metrics)
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible"),
    )
    parser.add_argument(
        "--active-set-csv",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2/D3_ACTIVE_SET_BY_NODE.csv"),
    )
    parser.add_argument(
        "--lower-bound-csv",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2/D3_LOWER_BOUND_NODAL_D.csv"),
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("models/state_transfer/d3_interrupted_transfer"),
    )
    args = parser.parse_args()
    metrics = analyze(args.target_dir, args.active_set_csv, args.lower_bound_csv, args.model_dir)
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0 if metrics["D3A3_R4_fixed_state_kkt_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
