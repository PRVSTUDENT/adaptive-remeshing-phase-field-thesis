#!/usr/bin/env python3
"""Offline D3A5 actual-history constrained phase-compatibility reprojection.

Reprojects the R3 F1 compatible phase against the actual R3 F1 SDV16 history
field using the exact D3A4 quadrature/assembly and sparse active-set solver.
No Abaqus solve, ODB read, Fortran, mesh generation, or PBS submission.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.solve_d3a4_phase_compatibility import (  # noqa: E402
    assemble,
    functional,
    load_mesh,
    solve_lower_bound_active_set,
    write_csv,
    write_json,
)

EXPECTED_NODES = 6601
EXPECTED_ELEMENTS = 6400
EXPECTED_IPS = 25600
EXPECTED_ACTUAL_FREE_RESIDUAL = 1.2035463824381645e-08
EXPECTED_MAX_FREE_RESIDUAL_NODE = 3200
PASS_CLASSIFICATION = "stage_d3a5_actual_history_reprojection_pass"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_r3_f1_phase(replay_dir: Path):
    rows = read_csv(replay_dir / "D3A3_R3_PHASE_NODE_STATE_BY_FRAME.csv")
    return {int(row["node"]): float(row["d_F1"]) for row in rows}


def load_r3_f1_h(source_dir: Path):
    rows = [
        row
        for row in read_csv(source_dir / "D3A3_STATE_BY_FRAME.csv")
        if row["frame_tag"] == "F1_equilibrated"
    ]
    h = {}
    sdv12 = {}
    sdv13 = {}
    for row in rows:
        key = (int(row["element"]), int(row["uel_integration_point"]))
        h[key] = float(row["odb_sdv16"])
        sdv12[key] = float(row["odb_sdv12"])
        sdv13[key] = float(row["odb_sdv13"])
    return h, sdv12, sdv13


def load_package_h(package_dir: Path):
    h = {}
    for row in read_csv(package_dir / "D3_TRANSFERRED_IP_H.csv"):
        key = (int(row["element"]), int(row["integration_point"]))
        h[key] = float(row["H"])
    return h


def load_d3a4_active(d3a4_dir: Path):
    rows = read_csv(d3a4_dir / "D3A4_ACTIVE_SET_BY_NODE.csv")
    active = {}
    for row in rows:
        text = str(row["active_lower_bound"]).strip().lower()
        active[int(row["node"])] = text in ("true", "1", "yes")
    return active


def residual_metrics(labels, residual, active_mask):
    free = ~active_mask
    free_res = residual[free]
    free_inf = float(np.max(np.abs(free_res))) if np.any(free) else 0.0
    free_max_i = int(np.flatnonzero(free)[int(np.argmax(np.abs(free_res)))]) if np.any(free) else None
    free_max_node = labels[free_max_i] if free_max_i is not None else None
    overall_i = int(np.argmax(np.abs(residual)))
    return {
        "free_set_residual_infinity_norm": free_inf,
        "maximum_free_residual_node": free_max_node,
        "maximum_residual_node": labels[overall_i],
        "maximum_residual_abs": float(np.max(np.abs(residual))),
        "residual_L2": float(math.sqrt(float(np.dot(residual, residual)) / len(residual))),
    }


def solve(args):
    args.out_dir.mkdir(parents=True, exist_ok=True)
    nodes, elements = load_mesh(args.model_dir)
    d_f1_by_node = load_r3_f1_phase(args.replay_dir)
    h_actual, sdv12, sdv13 = load_r3_f1_h(args.source_dir)
    h_old = load_package_h(args.package_dir)
    d3a4_active = load_d3a4_active(args.d3a4_dir)

    source_files = {
        "phase_state": args.replay_dir / "D3A3_R3_PHASE_NODE_STATE_BY_FRAME.csv",
        "f1_residual": args.replay_dir / "D3A3_R3_F1_RESIDUAL_BY_NODE.csv",
        "f1_kkt": args.replay_dir / "D3A3_R3_F1_KKT_METRICS.json",
        "state_by_frame": args.source_dir / "D3A3_STATE_BY_FRAME.csv",
        "package_h": args.package_dir / "D3_TRANSFERRED_IP_H.csv",
        "package_d": args.package_dir / "D3_TRANSFERRED_NODAL_D.csv",
        "d3a4_active": args.d3a4_dir / "D3A4_ACTIVE_SET_BY_NODE.csv",
        "d3a4_constrained": args.d3a4_dir / "D3A4_CONSTRAINED_NODAL_D.csv",
        "target_nodes": args.model_dir / "target" / "target_nodes.csv",
        "target_elements": args.model_dir / "target" / "target_elements.csv",
    }
    source_hashes = {
        name: {"path": str(path.as_posix()), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        for name, path in source_files.items()
    }
    write_json(args.out_dir / "D3A5_SOURCE_HASHES.json", {
        "classification": "stage_d3a5_source_hashes",
        "files": source_hashes,
    })
    write_json(args.out_dir / "D3A5_INPUT_PROVENANCE.json", {
        "classification": "stage_d3a5_input_provenance",
        "lower_bound": "recovered R3 F1 nodal d (post-D3A4 compatible state)",
        "history": "actual R3 F1 odb_sdv16 from job 1377417 base extraction",
        "old_history": "package_compatible_r1/D3_TRANSFERRED_IP_H.csv",
        "mesh": "models/state_transfer/d3_interrupted_transfer/target",
        "assembly": "scripts.state_transfer.solve_d3a4_phase_compatibility.assemble",
        "solver": "sparse_active_set_lower_bound_qp",
        "abaqus_analysis_reused": True,
        "odb_reread": False,
        "solver_executed": False,
        "fortran_compiled": False,
        "new_mesh": False,
        "source_job": "1377417.mmaster02",
        "source_replay_dir": str(args.replay_dir.as_posix()),
        "source_failure_dir": str(args.source_dir.as_posix()),
        "hypothesis": "D3A4 used earlier forensic/package H; R3 F1 actual H differs slightly and explains free residual exceedance",
    })

    # History change audit.
    common_keys = sorted(set(h_old) & set(h_actual))
    history_rows = []
    diffs = []
    h_inc = 0
    h_dec = 0
    for key in common_keys:
        hold = h_old[key]
        hact = h_actual[key]
        delta = hact - hold
        diffs.append(delta)
        if delta > 1.0e-30:
            h_inc += 1
        elif delta < -1.0e-30:
            h_dec += 1
        history_rows.append({
            "element": key[0],
            "integration_point": key[1],
            "H_old": hold,
            "H_actual": hact,
            "H_actual_minus_H_old": delta,
            "abs_H_actual_minus_H_old": abs(delta),
        })
    write_csv(
        args.out_dir / "D3A5_HISTORY_CHANGE_BY_IP.csv",
        [
            "element",
            "integration_point",
            "H_old",
            "H_actual",
            "H_actual_minus_H_old",
            "abs_H_actual_minus_H_old",
        ],
        history_rows,
    )
    diffs_arr = np.asarray(diffs, dtype=float)
    history_audit = {
        "classification": "stage_d3a5_history_change_audit",
        "ip_coverage_old": len(h_old),
        "ip_coverage_actual": len(h_actual),
        "ip_coverage_common": len(common_keys),
        "expected_ip_coverage": EXPECTED_IPS,
        "maximum_abs_H_actual_minus_H_old": float(np.max(np.abs(diffs_arr))) if len(diffs_arr) else None,
        "normalized_L2_H_difference": float(
            np.linalg.norm(diffs_arr) / max(np.linalg.norm([h_old[k] for k in common_keys]), 1.0e-30)
        ) if len(diffs_arr) else None,
        "H_increase_count": h_inc,
        "H_decrease_count": h_dec,
        "H_old_sum": float(sum(h_old.values())),
        "H_actual_sum": float(sum(h_actual.values())),
        "missing_old_only": len(set(h_old) - set(h_actual)),
        "missing_actual_only": len(set(h_actual) - set(h_old)),
    }
    write_json(args.out_dir / "D3A5_HISTORY_CHANGE_AUDIT.json", history_audit)

    # Residual causal audit at fixed d_F1 with old vs actual H.
    labels, index, k_old, f_old, assembly_old = assemble(nodes, elements, h_old)
    _labels2, _index2, k_act, f_act, assembly_act = assemble(nodes, elements, h_actual)
    d_f1 = np.array([d_f1_by_node[node] for node in labels], dtype=float)
    active_mask = np.array([d3a4_active[node] for node in labels], dtype=bool)

    r_old = np.asarray(k_old.dot(d_f1) - f_old, dtype=float)
    r_act = np.asarray(k_act.dot(d_f1) - f_act, dtype=float)
    metrics_old = residual_metrics(labels, r_old, active_mask)
    metrics_act = residual_metrics(labels, r_act, active_mask)

    residual_causal = {
        "classification": "stage_d3a5_residual_causal_audit",
        "node_coverage": len(labels),
        "expected_nodes": EXPECTED_NODES,
        "old_H_ip_coverage": assembly_old["integration_points"],
        "actual_H_ip_coverage": assembly_act["integration_points"],
        "non_positive_detJ_old": assembly_old["non_positive_detJ"],
        "non_positive_detJ_actual": assembly_act["non_positive_detJ"],
        "d3a4_active_nodes": int(np.count_nonzero(active_mask)),
        "d3a4_free_nodes": int(np.count_nonzero(~active_mask)),
        "old_H_metrics": metrics_old,
        "actual_H_metrics": metrics_act,
        "expected_actual_free_residual": EXPECTED_ACTUAL_FREE_RESIDUAL,
        "expected_maximum_free_residual_node": EXPECTED_MAX_FREE_RESIDUAL_NODE,
        "actual_free_residual_matches_replay": abs(
            metrics_act["free_set_residual_infinity_norm"] - EXPECTED_ACTUAL_FREE_RESIDUAL
        ) <= 1.0e-18 * max(1.0, abs(EXPECTED_ACTUAL_FREE_RESIDUAL))
        or abs(metrics_act["free_set_residual_infinity_norm"] - EXPECTED_ACTUAL_FREE_RESIDUAL)
        <= 1.0e-20,
        "actual_free_residual_relative_error": abs(
            metrics_act["free_set_residual_infinity_norm"] - EXPECTED_ACTUAL_FREE_RESIDUAL
        ) / max(abs(EXPECTED_ACTUAL_FREE_RESIDUAL), 1.0e-30),
        "maximum_free_residual_node_matches_replay": (
            metrics_act["maximum_free_residual_node"] == EXPECTED_MAX_FREE_RESIDUAL_NODE
        ),
        "old_vs_actual_free_residual_ratio": (
            metrics_act["free_set_residual_infinity_norm"]
            / max(metrics_old["free_set_residual_infinity_norm"], 1.0e-30)
        ),
    }
    # Looser but explicit floating equality for the published residual value.
    residual_causal["actual_free_residual_matches_replay"] = (
        abs(metrics_act["free_set_residual_infinity_norm"] - EXPECTED_ACTUAL_FREE_RESIDUAL)
        <= 1.0e-16
    )
    write_json(args.out_dir / "D3A5_RESIDUAL_CAUSAL_AUDIT.json", residual_causal)

    # Solve obstacle problem with actual H and lb = d_F1.
    d_sol, active, history, converged = solve_lower_bound_active_set(
        k_act, f_act, d_f1.copy(), tol=1.0e-12, max_iter=200
    )
    residual = np.asarray(k_act.dot(d_sol) - f_act, dtype=float)
    free = ~active
    delta = d_sol - d_f1

    reproject_rows = []
    active_rows = []
    for i, node in enumerate(labels):
        x, y = nodes[node]
        reproject_rows.append({
            "node": node,
            "x": x,
            "y": y,
            "d_F1": float(d_f1[i]),
            "d_D3A5": float(d_sol[i]),
            "d_D3A5_minus_d_F1": float(delta[i]),
            "active_lower_bound": bool(active[i]),
            "residual_Kd_minus_f": float(residual[i]),
        })
        active_rows.append({
            "node": node,
            "x": x,
            "y": y,
            "active_lower_bound": bool(active[i]),
            "d_compatible": float(d_sol[i]),
            "d_lb": float(d_f1[i]),
            "bound_margin": float(delta[i]),
            "residual_Kd_minus_f": float(residual[i]),
        })
    write_csv(
        args.out_dir / "D3A5_REPROJECTED_NODAL_D.csv",
        [
            "node",
            "x",
            "y",
            "d_F1",
            "d_D3A5",
            "d_D3A5_minus_d_F1",
            "active_lower_bound",
            "residual_Kd_minus_f",
        ],
        reproject_rows,
    )
    write_csv(
        args.out_dir / "D3A5_ACTIVE_SET_BY_NODE.csv",
        [
            "node",
            "x",
            "y",
            "active_lower_bound",
            "d_compatible",
            "d_lb",
            "bound_margin",
            "residual_Kd_minus_f",
        ],
        active_rows,
    )

    # Compare active-set membership to D3A4.
    d3a4_active_arr = active_mask
    changed_active = int(np.count_nonzero(active != d3a4_active_arr))

    kkt = {
        "classification": "stage_d3a5_active_set_kkt_metrics",
        "converged": bool(converged),
        "iterations": len(history),
        "active_set_membership_stable": len(history) >= 1 and bool(history[-1]["membership_unchanged"]),
        "active_node_count": int(np.count_nonzero(active)),
        "free_node_count": int(np.count_nonzero(free)),
        "free_set_residual_infinity_norm": float(np.max(np.abs(residual[free])) if np.any(free) else 0.0),
        "minimum_active_set_multiplier": float(np.min(residual[active]) if np.any(active) else 0.0),
        "complementarity_infinity_norm": float(np.max(np.abs(residual * delta))),
        "active_bound_error": float(np.max(np.abs(delta[active])) if np.any(active) else 0.0),
        "minimum_d_D3A5_minus_d_F1": float(np.min(delta)),
        "minimum_d_D3A5": float(np.min(d_sol)),
        "maximum_d_D3A5": float(np.max(d_sol)),
        "maximum_d_increase": float(np.max(delta)),
        "normalized_L2_d_increase": float(np.linalg.norm(delta) / max(np.linalg.norm(d_f1), 1.0e-30)),
        "predicted_phase_decrease_violations": int(np.count_nonzero(delta < -1.0e-12)),
        "changed_active_set_count_vs_d3a4": changed_active,
        "history": history,
        "all_values_finite": bool(
            np.all(np.isfinite(d_sol))
            and np.all(np.isfinite(residual))
            and np.all(np.isfinite(k_act.data))
            and np.all(np.isfinite(f_act))
        ),
        "nodes": len(labels),
        "elements": len(elements),
        "integration_points": int(assembly_act["integration_points"]),
        "non_positive_detJ": int(assembly_act["non_positive_detJ"]),
    }
    write_json(args.out_dir / "D3A5_KKT_METRICS.json", kkt)

    f_f1 = functional(k_act, f_act, d_f1)
    f_sol = functional(k_act, f_act, d_sol)
    functional_cmp = {
        "classification": "stage_d3a5_phase_functional_comparison",
        "functional_at_F1": f_f1,
        "functional_at_D3A5": f_sol,
        "D3A5_minus_F1": f_sol - f_f1,
        "functional_reduction_from_F1": f_f1 - f_sol,
    }
    write_json(args.out_dir / "D3A5_PHASE_FUNCTIONAL_COMPARISON.json", functional_cmp)

    largest = sorted(
        (
            {
                "node": node,
                "x": nodes[node][0],
                "y": nodes[node][1],
                "d_increase": float(delta[i]),
                "d_F1": float(d_f1[i]),
                "d_D3A5": float(d_sol[i]),
            }
            for i, node in enumerate(labels)
        ),
        key=lambda row: row["d_increase"],
        reverse=True,
    )[:10]

    status = {
        "classification": "stage_d3a5_projection_solved_unvalidated",
        "D3A5_ok": False,
        "converged": converged,
        "history_audit": history_audit,
        "residual_causal_audit": residual_causal,
        "kkt_metrics": kkt,
        "phase_functional_comparison": functional_cmp,
        "largest_d_increase_locations": largest,
        "solver_job_submitted": False,
        "fortran_compiled": False,
        "odb_reread": False,
    }
    write_json(args.out_dir / "D3A5_STATUS.json", status)
    print(json.dumps({
        "classification": status["classification"],
        "converged": converged,
        "active_nodes": kkt["active_node_count"],
        "free_nodes": kkt["free_node_count"],
        "free_residual_inf": kkt["free_set_residual_infinity_norm"],
        "max_d_increase": kkt["maximum_d_increase"],
        "functional_reduction": functional_cmp["functional_reduction_from_F1"],
        "actual_free_residual": metrics_act["free_set_residual_infinity_norm"],
        "history_max_abs_delta_H": history_audit["maximum_abs_H_actual_minus_H_old"],
    }, indent=2, sort_keys=True))
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replay-dir",
        type=Path,
        default=Path(
            "runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r3_compatible_postprocess_replay"
        ),
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r3_compatible"),
    )
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r1"),
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
        "--out-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/compatibility_reprojection_d3a5"),
    )
    args = parser.parse_args()
    solve(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
