#!/usr/bin/env python3
"""Per-frame actual-history KKT assembly for the D3D active-set segment.

Scientific gates apply only to F4_segment_* frames. F3_release_last is reported
as a baseline only. F0/F1/F2 are never used to decide D3D pass/fail.

Exit code is nonzero only when the analysis cannot be completed (missing state,
coverage failure on a gated frame, assembly exception, non-positive detJ,
nonfinite values). Negative active multipliers are scientific results: the
analyzer still finishes and lets the final validator classify the outcome.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
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

PREFIX_ONLY = frozenset({"F0_ingested", "F1_equilibrated", "F2_release_first"})
BASELINE_TAG = "F3_release_last"


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


def is_continuation_frame(tag: str) -> bool:
    return str(tag).startswith("F4_segment")


def is_reported_frame(tag: str) -> bool:
    return is_continuation_frame(tag) or tag == BASELINE_TAG


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
    rows = read_csv(phase_csv)
    if not rows:
        return {}
    if "recovered_d_mean" in rows[0]:
        out = {}
        for row in rows:
            tag = row["frame_tag"]
            out.setdefault(tag, {})[int(row["node"])] = float(row["recovered_d_mean"])
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


def ordered_tags(history, phase, manifest_path: Path | None):
    """Order frames by manifest step/frame_index when available."""
    if manifest_path and manifest_path.exists():
        rows = read_csv(manifest_path)
        tags = []
        for row in sorted(
            rows,
            key=lambda r: (
                r.get("step_name", ""),
                int(float(r.get("frame_index", 0))),
                float(r.get("step_time", 0.0) or 0.0),
            ),
        ):
            tag = row["frame_tag"]
            if tag in history and tag in phase and is_reported_frame(tag):
                tags.append(tag)
        if tags:
            return tags
    # Fallback: baseline then F4 sorted by tag.
    tags = []
    if BASELINE_TAG in history and BASELINE_TAG in phase:
        tags.append(BASELINE_TAG)
    cont = sorted(t for t in history if t in phase and is_continuation_frame(t))
    tags.extend(cont)
    return tags


def analyze(target_dir: Path, active_csv: Path, lower_csv: Path, model_dir: Path):
    nodes, elements = load_mesh(model_dir)
    active_map, lb_map = load_active_lower(active_csv, lower_csv)

    recovery = target_dir / "D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv"
    phase_csv = recovery if recovery.exists() else target_dir / "D3D_PHASE_NODE_STATE_BY_FRAME.csv"
    state_csv = target_dir / "D3A3_STATE_BY_FRAME.csv"
    if not state_csv.exists():
        state_csv = target_dir / "D3D_STATE_BY_FRAME.csv"

    analysis_failures = []
    if not phase_csv.exists():
        analysis_failures.append("phase CSV missing")
    if not state_csv.exists():
        analysis_failures.append("state CSV missing")
    if analysis_failures:
        summary = {
            "classification": "stage_d3d_per_frame_kkt_analysis_incomplete",
            "analysis_complete": False,
            "failures": analysis_failures,
        }
        write_json(target_dir / "D3D_PER_FRAME_KKT_SUMMARY.json", summary)
        write_csv(target_dir / "D3D_PER_FRAME_KKT.csv", ["frame_tag"], [])
        write_csv(
            target_dir / "D3D_ACTIVE_MULTIPLIER_CANDIDATES.csv",
            ["frame_tag", "node", "x", "y", "multiplier", "d", "d_lb"],
            [],
        )
        return summary

    phase = phase_by_frame(phase_csv)
    history = h_by_frame(state_csv)
    labels = sorted(nodes)
    active_mask = np.array([active_map[n] for n in labels], dtype=bool)
    lb = np.array([lb_map[n] for n in labels], dtype=float)

    tags = ordered_tags(history, phase, target_dir / "D3D_FRAME_MANIFEST.csv")
    continuation_expected = [t for t in tags if is_continuation_frame(t)]
    if not continuation_expected:
        # Still attempt to find any F4 in history even if ordering empty.
        continuation_expected = sorted(t for t in history if is_continuation_frame(t) and t in phase)

    frame_rows = []
    candidates = []
    first_neg_cont = None
    most_neg_cont = None
    max_free_res = None
    max_bound = None
    total_below = 0
    analysis_complete = True

    for tag in tags:
        role = "continuation" if is_continuation_frame(tag) else "baseline"
        h_by_ip = history[tag]
        d_by_node = phase[tag]
        node_cov = len(d_by_node)
        ip_cov = len(h_by_ip)
        if node_cov != EXPECTED_NODES or ip_cov != EXPECTED_IPS:
            row = {
                "frame_tag": tag,
                "role": role,
                "node_coverage": node_cov,
                "ip_coverage": ip_cov,
                "non_positive_detJ": "",
                "free_residual_inf": "",
                "minimum_active_multiplier": "",
                "active_bound_error": "",
                "active_nodes_below_tol": "",
                "kkt_ok": False,
                "scientific_active_multiplier_violation": False,
                "analysis_ok": False,
                "failures": "coverage",
            }
            frame_rows.append(row)
            if is_continuation_frame(tag) or tag == BASELINE_TAG:
                analysis_complete = False
                analysis_failures.append("%s coverage node=%s ip=%s" % (tag, node_cov, ip_cov))
            continue

        try:
            _, _, k, f, assembly = assemble(nodes, elements, h_by_ip)
            d = np.array([d_by_node[n] for n in labels], dtype=float)
            residual = np.asarray(k.dot(d) - f, dtype=float)
        except Exception as exc:  # noqa: BLE001 - report and continue analysis_complete=false
            analysis_complete = False
            analysis_failures.append("%s assembly exception: %s" % (tag, exc))
            frame_rows.append(
                {
                    "frame_tag": tag,
                    "role": role,
                    "node_coverage": node_cov,
                    "ip_coverage": ip_cov,
                    "non_positive_detJ": "",
                    "free_residual_inf": "",
                    "minimum_active_multiplier": "",
                    "active_bound_error": "",
                    "active_nodes_below_tol": "",
                    "kkt_ok": False,
                    "scientific_active_multiplier_violation": False,
                    "analysis_ok": False,
                    "failures": "assembly_exception",
                }
            )
            continue

        if not np.all(np.isfinite(residual)) or not np.all(np.isfinite(d)):
            analysis_complete = False
            analysis_failures.append("%s nonfinite residual/state" % tag)
            frame_rows.append(
                {
                    "frame_tag": tag,
                    "role": role,
                    "node_coverage": node_cov,
                    "ip_coverage": ip_cov,
                    "non_positive_detJ": int(assembly["non_positive_detJ"]),
                    "free_residual_inf": "",
                    "minimum_active_multiplier": "",
                    "active_bound_error": "",
                    "active_nodes_below_tol": "",
                    "kkt_ok": False,
                    "scientific_active_multiplier_violation": False,
                    "analysis_ok": False,
                    "failures": "nonfinite",
                }
            )
            continue

        free = ~active_mask
        free_res = float(np.max(np.abs(residual[free]))) if np.any(free) else 0.0
        min_mult = float(np.min(residual[active_mask])) if np.any(active_mask) else 0.0
        bound_err = (
            float(np.max(np.abs(d[active_mask] - lb[active_mask]))) if np.any(active_mask) else 0.0
        )
        below = int(np.count_nonzero(residual[active_mask] < ACTIVE_MULT_TOL))
        detj = int(assembly["non_positive_detJ"])

        tech_fails = []
        sci_fails = []
        if detj != 0:
            tech_fails.append("detJ")
            if is_continuation_frame(tag):
                analysis_complete = False
                analysis_failures.append("%s non-positive detJ" % tag)
        if free_res > FREE_RES_TOL:
            tech_fails.append("free_residual")
        if bound_err > ACTIVE_BOUND_TOL:
            tech_fails.append("bound_error")
        if min_mult < ACTIVE_MULT_TOL:
            sci_fails.append("active_multiplier")

        # kkt_ok for reporting: free residual + bound + detJ for continuation scientific use;
        # multiplier violation is scientific and recorded separately.
        tech_ok = not tech_fails
        mult_ok = not sci_fails
        kkt_ok = tech_ok and mult_ok

        if is_continuation_frame(tag):
            max_free_res = free_res if max_free_res is None else max(max_free_res, free_res)
            max_bound = bound_err if max_bound is None else max(max_bound, bound_err)
            total_below += below
            if min_mult < ACTIVE_MULT_TOL and first_neg_cont is None:
                first_neg_cont = tag
            if most_neg_cont is None or min_mult < most_neg_cont[0]:
                most_neg_cont = (min_mult, tag)
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
                "role": role,
                "node_coverage": EXPECTED_NODES,
                "ip_coverage": EXPECTED_IPS,
                "non_positive_detJ": detj,
                "free_residual_inf": free_res,
                "minimum_active_multiplier": min_mult,
                "active_bound_error": bound_err,
                "active_nodes_below_tol": below,
                "kkt_ok": kkt_ok,
                "scientific_active_multiplier_violation": not mult_ok,
                "analysis_ok": detj == 0 and math.isfinite(free_res) and math.isfinite(min_mult),
                "failures": ";".join(tech_fails + sci_fails),
            }
        )

    # Never gate on F0/F1/F2 even if present in phase/history.
    ignored = [t for t in history if t in PREFIX_ONLY]
    cont_rows = [r for r in frame_rows if is_continuation_frame(r["frame_tag"])]
    cont_kkt_ok = sum(1 for r in cont_rows if r["kkt_ok"])

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

    summary = {
        "classification": (
            "stage_d3d_per_frame_kkt_analysis_complete"
            if analysis_complete
            else "stage_d3d_per_frame_kkt_analysis_incomplete"
        ),
        "analysis_complete": analysis_complete,
        "failures": analysis_failures,
        "frames_evaluated": len(frame_rows),
        "frames_kkt_ok": sum(1 for r in frame_rows if r["kkt_ok"]),
        "continuation_frames_expected": len(continuation_expected),
        "continuation_frames_evaluated": len(cont_rows),
        "continuation_frames_kkt_ok": cont_kkt_ok,
        "first_frame_with_negative_active_multiplier": first_neg_cont,
        "first_continuation_frame_with_negative_multiplier": first_neg_cont,
        "most_negative_active_multiplier": most_neg_cont[0] if most_neg_cont else None,
        "most_negative_continuation_multiplier": most_neg_cont[0] if most_neg_cont else None,
        "most_negative_active_multiplier_frame": most_neg_cont[1] if most_neg_cont else None,
        "active_nodes_below_tolerance": total_below,
        "candidate_rows": len(candidates),
        "maximum_free_residual": max_free_res,
        "maximum_active_bound_error": max_bound,
        "ignored_prefix_tags": ignored,
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
        default=Path(
            "runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2/D3_ACTIVE_SET_BY_NODE.csv"
        ),
    )
    parser.add_argument(
        "--lower-bound-csv",
        type=Path,
        default=Path(
            "runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2/D3_LOWER_BOUND_NODAL_D.csv"
        ),
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("models/state_transfer/d3_interrupted_transfer"),
    )
    args = parser.parse_args()
    summary = analyze(args.target_dir, args.active_set_csv, args.lower_bound_csv, args.model_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    # Nonzero only when analysis cannot be completed.
    return 0 if summary.get("analysis_complete", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
