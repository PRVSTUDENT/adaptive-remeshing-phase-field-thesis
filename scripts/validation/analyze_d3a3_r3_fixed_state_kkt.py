#!/usr/bin/env python3
"""Evaluate D3A3-R3 Step-2 (F1) fixed-state KKT using actual ODB H.

Reuses the exact D3A4 quadrature/assembly routines. Does not re-solve the
active-set projection: residual and multipliers are evaluated at the recovered
F1 compatible phase with the D3A4 active-set membership.
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.solve_d3a4_phase_compatibility import (  # noqa: E402
    assemble,
    load_mesh,
)

EXPECTED_NODES = 6601
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
    phase_path = target_dir / "D3A3_R3_PHASE_NODE_STATE_BY_FRAME.csv"
    if phase_path.exists():
        rows = read_csv(phase_path)
        return {int(row["node"]): float(row["d_F1"]) for row in rows}
    recovery_path = target_dir / "D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv"
    rows = [
        row
        for row in read_csv(recovery_path)
        if row["frame_tag"] == "F1_equilibrated"
    ]
    return {int(row["node"]): float(row["recovered_d_mean"]) for row in rows}


def load_f1_h(target_dir: Path):
    state_path = target_dir / "D3A3_STATE_BY_FRAME.csv"
    if not state_path.exists():
        state_path = target_dir / "D3A3_R3_STATE_BY_FRAME.csv"
    rows = [row for row in read_csv(state_path) if row["frame_tag"] == "F1_equilibrated"]
    h = {}
    for row in rows:
        key = (int(row["element"]), int(row["uel_integration_point"]))
        h[key] = float(row["odb_sdv16"])
    return h


def load_active_set(d3a4_dir: Path):
    rows = read_csv(d3a4_dir / "D3A4_ACTIVE_SET_BY_NODE.csv")
    active = {}
    lower = {}
    xy = {}
    for row in rows:
        node = int(row["node"])
        active[node] = bool_value(row["active_lower_bound"])
        lower[node] = float(row["d_lb"]) if "d_lb" in row and row["d_lb"] != "" else float(row.get("d_compatible", "nan"))
        xy[node] = (float(row["x"]), float(row["y"]))
    # Prefer package lower bound if present via phase-state file later.
    return active, lower, xy


def load_package_lower_bound(package_dir):
    # type: (Optional[Path]) -> dict
    if package_dir is None:
        return {}
    path = package_dir / "D3_LOWER_BOUND_NODAL_D.csv"
    if not path.exists():
        return {}
    return {int(row["node"]): float(row["d_lower_bound"]) for row in read_csv(path)}


def analyze(target_dir, d3a4_dir, model_dir, package_dir=None):
    nodes, elements = load_mesh(model_dir)
    d_by_node = load_recovered_f1_phase(target_dir)
    h_by_ip = load_f1_h(target_dir)
    active_map, d3a4_lb, xy = load_active_set(d3a4_dir)
    package_lb = load_package_lower_bound(package_dir)
    lb_by_node = {node: package_lb.get(node, d3a4_lb[node]) for node in active_map}

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
        residual_rows.append({
            "node": node,
            "x": x,
            "y": y,
            "active_lower_bound": bool(active[i]),
            "d_F1": float(d[i]),
            "d_lower_bound": float(lb[i]),
            "bound_error": float(d[i] - lb[i]),
            "residual_Kd_minus_f": float(residual[i]),
            "multiplier_if_active": float(residual[i]) if active[i] else "",
        })
    write_csv(
        target_dir / "D3A3_R3_F1_RESIDUAL_BY_NODE.csv",
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
    if len(d_by_node) != EXPECTED_NODES:
        failures.append("recovered F1 phase nodes = %s expected %s" % (len(d_by_node), EXPECTED_NODES))
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
            "stage_d3a3_r3_fixed_state_kkt_pass"
            if passed
            else "stage_d3a3_r3_fixed_state_needs_reprojection"
        ),
        "D3A3_R3_fixed_state_kkt_ok": passed,
        "failures": failures,
        "node_coverage": len(labels),
        "expected_nodes": EXPECTED_NODES,
        "active_node_count": int(np.count_nonzero(active)),
        "free_node_count": int(np.count_nonzero(free)),
        "free_set_residual_infinity_norm": free_residual_inf,
        "minimum_active_set_multiplier": min_active_multiplier,
        "active_node_bound_error": active_bound_error,
        "non_positive_detJ": int(assembly["non_positive_detJ"]),
        "integration_points": int(assembly["integration_points"]),
        "free_residual_tol": FREE_RESIDUAL_TOL,
        "active_multiplier_tol": ACTIVE_MULTIPLIER_TOL,
        "active_bound_error_tol": ACTIVE_BOUND_ERROR_TOL,
        "history_field": "F1_equilibrated odb_sdv16",
        "phase_field": "recovered F1 compatible phase",
        "active_set_source": "D3A4_ACTIVE_SET_BY_NODE.csv",
        "assembly": "scripts.state_transfer.solve_d3a4_phase_compatibility.assemble",
    }
    write_json(target_dir / "D3A3_R3_F1_KKT_METRICS.json", metrics)
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r3_compatible"),
    )
    parser.add_argument(
        "--d3a4-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/compatibility_projection_d3a4"),
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("models/state_transfer/d3_interrupted_transfer"),
    )
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r1"),
    )
    args = parser.parse_args()
    metrics = analyze(args.target_dir, args.d3a4_dir, args.model_dir, args.package_dir)
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0 if metrics["D3A3_R3_fixed_state_kkt_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
