#!/usr/bin/env python3
"""Consecutive-frame phase/history irreversibility audit for D3D Step 4."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


PHASE_DEC_TOL = -1.0e-10
H_DEC_TOL = -1.0e-10
LB_TOL = -1.0e-10


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


def phase_by_frame(phase_csv: Path):
    rows = read_csv(phase_csv)
    if not rows:
        return {}
    if "recovered_d_mean" in rows[0]:
        out = {}
        for row in rows:
            out.setdefault(row["frame_tag"], {})[int(row["node"])] = float(row["recovered_d_mean"])
        return out
    colmap = {
        "F0_ingested": "d_F0",
        "F1_equilibrated": "d_F1",
        "F2_release_first": "d_F2",
        "F3_release_last": "d_F3",
    }
    out = {t: {} for t in colmap}
    for row in rows:
        node = int(row["node"])
        for t, c in colmap.items():
            if c in row and row[c] not in ("", None):
                out[t][node] = float(row[c])
    return {t: m for t, m in out.items() if m}


def h_by_frame(state_csv: Path):
    rows = read_csv(state_csv)
    out = {}
    for row in rows:
        tag = row["frame_tag"]
        key = (int(row["element"]), int(row["uel_integration_point"]))
        out.setdefault(tag, {})[key] = float(row["odb_sdv16"])
    return out


def ordered_audit_tags(manifest_path: Path, phase, history):
    """Order F3_release_last then all F4 frames by step_name/frame_index/time."""
    tags = []
    if manifest_path.exists():
        rows = read_csv(manifest_path)
        ordered = sorted(
            rows,
            key=lambda r: (
                r.get("step_name", ""),
                int(float(r.get("frame_index", 0))),
                float(r.get("step_time", 0.0) or 0.0),
            ),
        )
        for row in ordered:
            tag = row["frame_tag"]
            if tag == "F3_release_last" or str(tag).startswith("F4_segment"):
                if tag in phase and tag in history:
                    tags.append(tag)
        # Deduplicate while preserving order.
        seen = set()
        uniq = []
        for t in tags:
            if t not in seen:
                seen.add(t)
                uniq.append(t)
        if uniq:
            return uniq
    # Fallback without manifest.
    tags = []
    if "F3_release_last" in phase and "F3_release_last" in history:
        tags.append("F3_release_last")
    tags.extend(sorted(t for t in phase if t in history and str(t).startswith("F4_segment")))
    return tags


def load_lower_bounds(lower_csv: Path | None, active_csv: Path | None):
    lb = {}
    if lower_csv and lower_csv.exists():
        for row in read_csv(lower_csv):
            lb[int(row["node"])] = float(row["d_lower_bound"])
    if active_csv and active_csv.exists():
        for row in read_csv(active_csv):
            node = int(row["node"])
            if row.get("d_lb") not in (None, ""):
                lb[node] = float(row["d_lb"])
    return lb


def pair_metrics(left_tag, right_tag, phase, history, lb):
    d0 = phase[left_tag]
    d1 = phase[right_tag]
    h0 = history[left_tag]
    h1 = history[right_tag]
    nodes = sorted(set(d0) & set(d1))
    ips = sorted(set(h0) & set(h1))
    phase_dec = 0
    h_dec = 0
    below_lb = 0
    max_phase_dec = 0.0
    max_h_dec = 0.0
    max_phase_inc = 0.0
    l2_num = 0.0
    for n in nodes:
        delta = d1[n] - d0[n]
        l2_num += delta * delta
        if delta < PHASE_DEC_TOL:
            phase_dec += 1
            max_phase_dec = min(max_phase_dec, delta)
        if delta > max_phase_inc:
            max_phase_inc = delta
        if lb and n in lb and (d1[n] - lb[n]) < LB_TOL:
            below_lb += 1
    for ip in ips:
        delta = h1[ip] - h0[ip]
        if delta < H_DEC_TOL:
            h_dec += 1
            max_h_dec = min(max_h_dec, delta)
    n_nodes = len(nodes)
    n_ips = len(ips)
    return {
        "left_frame": left_tag,
        "right_frame": right_tag,
        "phase_node_coverage": n_nodes,
        "ip_coverage": n_ips,
        "phase_decrease_count": phase_dec,
        "H_decrease_count": h_dec,
        "below_lower_bound_count": below_lb,
        "maximum_phase_decrease": max_phase_dec if phase_dec else 0.0,
        "maximum_H_decrease": max_h_dec if h_dec else 0.0,
        "maximum_phase_increase": max_phase_inc,
        "normalized_L2_phase_change": math.sqrt(l2_num / n_nodes) if n_nodes else None,
    }


def analyze(
    target_dir: Path,
    lower_csv: Path | None = None,
    active_csv: Path | None = None,
):
    phase_csv = target_dir / "D3D_PHASE_NODE_STATE_BY_FRAME.csv"
    if not phase_csv.exists():
        phase_csv = target_dir / "D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv"
    state_csv = target_dir / "D3D_STATE_BY_FRAME.csv"
    if not state_csv.exists():
        state_csv = target_dir / "D3A3_STATE_BY_FRAME.csv"
    manifest = target_dir / "D3D_FRAME_MANIFEST.csv"

    failures = []
    if not phase_csv.exists():
        failures.append("phase CSV missing")
    if not state_csv.exists():
        failures.append("state CSV missing")
    if failures:
        audit = {
            "classification": "stage_d3d_irreversibility_audit_incomplete",
            "audit_complete": False,
            "failures": failures,
            "phase_decrease_violations": None,
            "H_decrease_violations": None,
            "below_lower_bound_violations": None,
        }
        write_json(target_dir / "D3D_IRREVERSIBILITY_AUDIT.json", audit)
        write_csv(target_dir / "D3D_IRREVERSIBILITY_BY_FRAME_PAIR.csv", ["left_frame", "right_frame"], [])
        return audit

    phase = phase_by_frame(phase_csv)
    history = h_by_frame(state_csv)
    lb = load_lower_bounds(lower_csv, active_csv)
    tags = ordered_audit_tags(manifest, phase, history)
    if len(tags) < 2:
        failures.append("fewer than 2 ordered audit frames (need F3 then F4 sequence)")
        audit = {
            "classification": "stage_d3d_irreversibility_audit_incomplete",
            "audit_complete": False,
            "failures": failures,
            "phase_decrease_violations": None,
            "H_decrease_violations": None,
            "below_lower_bound_violations": None,
            "ordered_tags": tags,
        }
        write_json(target_dir / "D3D_IRREVERSIBILITY_AUDIT.json", audit)
        write_csv(target_dir / "D3D_IRREVERSIBILITY_BY_FRAME_PAIR.csv", ["left_frame", "right_frame"], [])
        return audit

    pairs = []
    phase_tot = 0
    h_tot = 0
    lb_tot = 0
    max_phase_inc = 0.0
    for i in range(len(tags) - 1):
        m = pair_metrics(tags[i], tags[i + 1], phase, history, lb)
        pairs.append(m)
        phase_tot += int(m["phase_decrease_count"])
        h_tot += int(m["H_decrease_count"])
        lb_tot += int(m["below_lower_bound_count"])
        max_phase_inc = max(max_phase_inc, float(m["maximum_phase_increase"] or 0.0))

    write_csv(
        target_dir / "D3D_IRREVERSIBILITY_BY_FRAME_PAIR.csv",
        list(pairs[0].keys()),
        pairs,
    )
    audit = {
        "classification": "stage_d3d_irreversibility_audit_complete",
        "audit_complete": True,
        "failures": [],
        "ordered_tags": tags,
        "pair_count": len(pairs),
        "phase_decrease_violations": phase_tot,
        "H_decrease_violations": h_tot,
        "below_lower_bound_violations": lb_tot,
        "maximum_phase_increase": max_phase_inc,
        "phase_decrease_tolerance": PHASE_DEC_TOL,
        "H_decrease_tolerance": H_DEC_TOL,
    }
    write_json(target_dir / "D3D_IRREVERSIBILITY_AUDIT.json", audit)
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment"),
    )
    parser.add_argument(
        "--lower-bound-csv",
        type=Path,
        default=Path(
            "runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2/D3_LOWER_BOUND_NODAL_D.csv"
        ),
    )
    parser.add_argument(
        "--active-set-csv",
        type=Path,
        default=Path(
            "runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2/D3_ACTIVE_SET_BY_NODE.csv"
        ),
    )
    args = parser.parse_args()
    audit = analyze(args.target_dir, args.lower_bound_csv, args.active_set_csv)
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit.get("audit_complete", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
