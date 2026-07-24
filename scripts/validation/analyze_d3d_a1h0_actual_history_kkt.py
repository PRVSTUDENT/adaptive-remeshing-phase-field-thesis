#!/usr/bin/env python3
"""Assemble D3D-A1H0 endpoint KKT metrics using actual equilibrated SDV16."""

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.state_transfer.solve_d3a4_phase_compatibility import assemble, load_mesh


def read(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-dir", type=Path, required=True)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer"))
    args = parser.parse_args()
    nodes, elements = load_mesh(args.model_dir)
    labels = sorted(nodes)
    state = [r for r in read(args.target_dir / "D3D_A1H0_STATE_BY_FRAME.csv") if r["frame_tag"] == "F1_equilibrated"]
    phase = [r for r in read(args.target_dir / "D3D_A1H0_PHASE_NODE_STATE_BY_FRAME.csv") if r["frame_tag"] == "F1_equilibrated"]
    h = {(int(r["element"]), int(r["uel_integration_point"])): float(r["odb_sdv16"]) for r in state}
    dmap = {int(r["node"]): float(r["recovered_d_mean"]) for r in phase}
    active_rows = read(args.package_dir / "D3_ACTIVE_SET_BY_NODE.csv")
    active_map = {int(r["node"]): str(r["active_lower_bound"]).lower() in ("true", "1", "yes") for r in active_rows}
    lb = {int(r["node"]): float(r["d_lower_bound"]) for r in read(args.package_dir / "D3_LOWER_BOUND_NODAL_D.csv")}
    failures = []
    phase_keys = [int(r["node"]) for r in phase]
    history_keys = [(int(r["element"]), int(r["uel_integration_point"])) for r in state]
    active_count = sum(active_map.values())
    free_count = len(active_map) - active_count
    if len(nodes) != 6601: failures.append("mesh_nodes")
    if len(set(phase_keys)) != 6601 or len(phase_keys) != 6601: failures.append("phase_coverage_or_duplicates")
    if len(set(history_keys)) != 25600 or len(history_keys) != 25600: failures.append("history_coverage_or_duplicates")
    if (active_count, free_count) != (6374, 227): failures.append("active_free_counts")
    try:
        _, _, k, f, audit = assemble(nodes, elements, h)
    except Exception as exc:
        metrics = {"classification":"stage_d3d_a1h0_actual_history_kkt_incomplete","analysis_complete":False,"failures":failures+["assembly:"+str(exc)]}
        (args.target_dir / "D3D_A1H0_ACTUAL_HISTORY_KKT.json").write_text(json.dumps(metrics,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps(metrics,indent=2,sort_keys=True)); return 1
    d = np.array([dmap[n] for n in labels])
    mask = np.array([active_map[n] for n in labels], dtype=bool)
    residual = np.asarray(k.dot(d) - f)
    finite = bool(np.all(np.isfinite(d)) and np.all(np.isfinite(list(h.values()))) and np.all(np.isfinite(residual)))
    if audit["non_positive_detJ"] != 0: failures.append("non_positive_detJ")
    if not finite: failures.append("nonfinite_phase_history_or_residual")
    metrics = {
        "classification": "stage_d3d_a1h0_actual_history_kkt_complete" if not failures else "stage_d3d_a1h0_actual_history_kkt_incomplete",
        "analysis_complete": not failures,
        "failures": failures,
        "mesh_nodes": len(nodes),
        "active_node_count": active_count,
        "free_node_count": free_count,
        "duplicate_node_records": len(phase_keys)-len(set(phase_keys)),
        "duplicate_ip_records": len(history_keys)-len(set(history_keys)),
        "missing_node_records": 6601-len(set(phase_keys)),
        "missing_ip_records": 25600-len(set(history_keys)),
        "all_values_finite": finite,
        "node_coverage": len(dmap), "ip_coverage": len(h),
        "non_positive_detJ": audit["non_positive_detJ"],
        "free_residual_infinity_norm": float(np.max(np.abs(residual[~mask]))),
        "minimum_active_multiplier": float(np.min(residual[mask])),
        "active_bound_error": float(np.max(np.abs(d[mask] - np.array([lb[n] for n in labels])[mask]))),
    }
    (args.target_dir / "D3D_A1H0_ACTUAL_HISTORY_KKT.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (args.target_dir / "D3D_A1H0_ACTUAL_HISTORY_KKT.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["node", "active", "residual"])
        writer.writeheader()
        writer.writerows({"node": n, "active": bool(mask[i]), "residual": residual[i]} for i, n in enumerate(labels))
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0 if metrics["analysis_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
