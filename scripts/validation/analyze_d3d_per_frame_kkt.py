#!/usr/bin/env python3
"""Per-frame actual-history KKT assembly for the D3D active-set segment."""

from __future__ import annotations

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
FREE_RES_TOL = 1.0e-8
ACTIVE_MULT_TOL = -1.0e-8
ACTIVE_BOUND_TOL = 1.0e-10


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


def bool_value(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes")


def load_active_lower(active_csv: Path, lower_csv: Path):
    active_rows = read_csv(active_csv)
    lower = {int(r["node"]): float(r["d_lower_bound"]) for r in read_csv(lower_csv)}
    active = {}
    lb = {}
    for row in active_rows:
        node = int(row["node"])
        active[node] = bool_value(row["active_lower_bound"])
        lb[node] = float(row["d_lb"]) if row.get("d_lb") not in (None, "") else lower[node]
    return active, lb


def phase_by_frame(phase_csv: Path):
    """Return frame_tag -> {node: d} from recovery-style or wide CSV."""
    rows = read_csv(phase_csv)
    if not rows:
        return {}
    # Wide format with d_F0..d_F3 plus continuation columns, or recovered_d_mean.
    if "recovered_d_mean" in rows[0]:
        out = {}
        for row in rows:
            tag = row["frame_tag"]
            out.setdefault(tag, {})[int(row["node"])] = float(row["recovered_d_mean"])
        return out
    # Wide node state: only fixed tags.
    tags = ["F0_ingested", "F1_equilibrated", "F2_release_first", "F3_release_last"]
    colmap = {
        "F0_ingested": "d_F0",
        "F1_equilibrated": "d_F1",
        "F2_release_first": "d_F2",
        "F3_release_last": "d_F3",
    }
    out = {t: {} for t in tags}
    for row in rows:
        node = int(row["node"])
        for t, c in colmap.items():
            if c in row and row[c] not in ("", None):
                out[t][node] = float(row[c])
    # Drop empty tags.
    return {t: m for t, m in out.items() if m}


def h_by_frame(state_csv: Path):
    rows = read_csv(state_csv)
    out = {}
    for row in rows:
        tag = row["frame_tag"]
        key = (int(row["element"]), int(row["uel_integration_point"]))
        out.setdefault(tag, {})[key] = float(row["odb_sdv16"])
    return out


def analyze(target_dir: Path, active_csv: Path, lower_csv: Path, model_dir: Path):
    nodes, elements = load_mesh(model_dir)
    active_map, lb_map = load_active_lower(active_csv, lower_csv)

    # Prefer recovery CSV for all frames including continuation.
    recovery = target_dir / "D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv"
    phase_csv = recovery if recovery.exists() else target_dir / "D3D_PHASE_NODE_STATE_BY_FRAME.csv"
    state_csv = target_dir / "D3A3_STATE_BY_FRAME.csv"
    if not state_csv.exists():
        state_csv = target_dir / "D3D_STATE_BY_FRAME.csv"

    phase = phase_by_frame(phase_csv)
    history = h_by_frame(state_csv)

    labels = sorted(nodes)
    active_mask = np.array([active_map[n] for n in labels], dtype=bool)
    lb = np.array([lb_map[n] for n in labels], dtype=float)

    frame_rows = []
    candidates = []
    first_neg_frame = None
    most_neg = None
    continuation_tags = [
        t for t in sorted(history.keys()) if t not in (
            "F0_ingested",
            "F1_equilibrated",
            "F2_release_first",
            "F3_release_last",
        ) or t.startswith("F4") or "SEGMENT" in t.upper() or "continuation" in t.lower()
    ]
    # Evaluate all frames that have both phase and H.
    tags = [t for t in history.keys() if t in phase]

    for tag in tags:
        h_by_ip = history[tag]
        d_by_node = phase[tag]
        if len(h_by_ip) != EXPECTED_IPS or len(d_by_node) != EXPECTED_NODES:
            frame_rows.append(
                {
                    "frame_tag": tag,
                    "node_coverage": len(d_by_node),
                    "ip_coverage": len(h_by_ip),
                    "free_residual_inf": "",
                    "minimum_active_multiplier": "",
                    "active_bound_error": "",
                    "active_nodes_below_tol": "",
                    "kkt_ok": False,
                    "failures": "coverage",
                }
            )
            continue
        _, _, k, f, assembly = assemble(nodes, elements, h_by_ip)
        d = np.array([d_by_node[n] for n in labels], dtype=float)
        residual = np.asarray(k.dot(d) - f, dtype=float)
        free = ~active_mask
        free_res = float(np.max(np.abs(residual[free]))) if np.any(free) else 0.0
        min_mult = float(np.min(residual[active_mask])) if np.any(active_mask) else 0.0
        bound_err = float(np.max(np.abs(d[active_mask] - lb[active_mask]))) if np.any(active_mask) else 0.0
        below = int(np.count_nonzero(residual[active_mask] < ACTIVE_MULT_TOL))
        fails = []
        if assembly["non_positive_detJ"] != 0:
            fails.append("detJ")
        if free_res > FREE_RES_TOL:
            fails.append("free_residual")
        if min_mult < ACTIVE_MULT_TOL:
            fails.append("active_multiplier")
        if bound_err > ACTIVE_BOUND_TOL:
            fails.append("bound_error")
        kkt_ok = not fails
        if min_mult < ACTIVE_MULT_TOL and first_neg_frame is None:
            first_neg_frame = tag
        if most_neg is None or min_mult < most_neg[0]:
            most_neg = (min_mult, tag)
        if below > 0:
            for i, node in enumerate(labels):
                if active_mask[i] and residual[i] < ACTIVE_MULT_TOL:
                    x, y = nodes[node]
                    candidates.append(
                        {
                            "frame_tag": tag,
                            "node": node,
                            "x": x,
                            "y": y,
                            "multiplier": float(residual[i]),
                            "d": float(d[i]),
                            "d_lb": float(lb[i]),
                        }
                    )
        frame_rows.append(
            {
                "frame_tag": tag,
                "node_coverage": EXPECTED_NODES,
                "ip_coverage": EXPECTED_IPS,
                "non_positive_detJ": int(assembly["non_positive_detJ"]),
                "free_residual_inf": free_res,
                "minimum_active_multiplier": min_mult,
                "active_bound_error": bound_err,
                "active_nodes_below_tol": below,
                "kkt_ok": kkt_ok,
                "failures": ";".join(fails),
            }
        )

    write_csv(
        target_dir / "D3D_PER_FRAME_KKT.csv",
        list(frame_rows[0].keys()) if frame_rows else ["frame_tag"],
        frame_rows,
    )
    write_csv(
        target_dir / "D3D_ACTIVE_MULTIPLIER_CANDIDATES.csv",
        ["frame_tag", "node", "x", "y", "multiplier", "d", "d_lb"],
        candidates,
    )

    continuation_fail = any(
        (not r["kkt_ok"]) and (
            str(r["frame_tag"]).startswith("F4")
            or "SEGMENT" in str(r["frame_tag"]).upper()
            or "continuation" in str(r["frame_tag"]).lower()
            or str(r["frame_tag"]) not in (
                "F0_ingested",
                "F1_equilibrated",
                "F2_release_first",
                "F3_release_last",
            )
        )
        for r in frame_rows
    )
    # Also consider all post-F3 frames: any frame after release endpoint in listing order.
    any_fail = any(not r["kkt_ok"] for r in frame_rows)
    summary = {
        "classification": (
            "stage_d3d_per_frame_kkt_pass"
            if not any_fail
            else "stage_d3d_per_frame_kkt_fail"
        ),
        "frames_evaluated": len(frame_rows),
        "frames_kkt_ok": sum(1 for r in frame_rows if r["kkt_ok"]),
        "first_frame_with_negative_active_multiplier": first_neg_frame,
        "most_negative_active_multiplier": most_neg[0] if most_neg else None,
        "most_negative_active_multiplier_frame": most_neg[1] if most_neg else None,
        "candidate_rows": len(candidates),
        "free_residual_tol": FREE_RES_TOL,
        "active_multiplier_tol": ACTIVE_MULT_TOL,
        "active_bound_tol": ACTIVE_BOUND_TOL,
    }
    write_json(target_dir / "D3D_PER_FRAME_KKT_SUMMARY.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment"),
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
    summary = analyze(args.target_dir, args.active_set_csv, args.lower_bound_csv, args.model_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["classification"] == "stage_d3d_per_frame_kkt_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
