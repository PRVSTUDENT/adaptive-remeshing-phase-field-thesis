#!/usr/bin/env python3
"""Assemble D3D-A1H0 endpoint KKT metrics using actual equilibrated SDV16."""

import argparse
import csv
import json
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
    _, _, k, f, audit = assemble(nodes, elements, h)
    d = np.array([dmap[n] for n in labels])
    mask = np.array([active_map[n] for n in labels], dtype=bool)
    residual = np.asarray(k.dot(d) - f)
    metrics = {
        "classification": "stage_d3d_a1h0_actual_history_kkt_complete",
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
