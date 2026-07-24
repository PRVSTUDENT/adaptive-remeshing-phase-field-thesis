#!/usr/bin/env python3
"""Deterministic offline D3D-A1 checkpoint obstacle update.

No Abaqus deck, ODB access, PBS artifact, or solver submission is performed.
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
from scipy.sparse.linalg import spsolve

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.solve_d3a4_phase_compatibility import (  # noqa: E402
    assemble,
    functional,
    load_mesh,
)

SOURCE_TAG = "F3_release_last"
COMPARISON_TAG = "F4_segment_initial"
EXPECTED_NODES = 6601
EXPECTED_ELEMENTS = 6400
EXPECTED_IPS = 25600
EXPECTED_ACTIVE = 6446
EXPECTED_FREE = 155
EXPECTED_SEEDS = 30
FREE_RESIDUAL_TOL = 1.0e-8
ACTIVE_MULTIPLIER_TOL = -1.0e-8
ACTIVE_BOUND_TOL = 1.0e-10
LOWER_BOUND_TOL = 1.0e-10
MAX_ITERATIONS = 200


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bool_value(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def solve_primal_dual(
    k,
    f: np.ndarray,
    lower: np.ndarray,
    initial_active: np.ndarray,
    *,
    max_iterations: int = MAX_ITERATIONS,
    free_residual_tol: float = FREE_RESIDUAL_TOL,
    active_multiplier_tol: float = ACTIVE_MULTIPLIER_TOL,
    active_bound_tol: float = ACTIVE_BOUND_TOL,
    lower_bound_tol: float = LOWER_BOUND_TOL,
):
    """Solve with deterministic simultaneous membership updates.

    Bound nodes satisfying the multiplier gate remain active, which provides
    the required minimum-release tie break.
    """
    active = np.asarray(initial_active, dtype=bool).copy()
    d = np.asarray(lower, dtype=float).copy()
    history = []
    all_reactivated: set[int] = set()
    previous_active = None

    for iteration in range(1, max_iterations + 1):
        active_before = active.copy()
        free = ~active
        d[active] = lower[active]
        if np.any(free):
            free_idx = np.flatnonzero(free)
            active_idx = np.flatnonzero(active)
            rhs = np.asarray(f[free_idx], dtype=float).copy()
            if active_idx.size:
                rhs -= k[free_idx, :][:, active_idx].dot(lower[active_idx])
            d[free_idx] = np.asarray(
                spsolve(k[free_idx, :][:, free_idx], rhs), dtype=float
            )

        reactivated = (~active) & (d < lower - lower_bound_tol)
        if np.any(reactivated):
            active[reactivated] = True
            d[reactivated] = lower[reactivated]
            all_reactivated.update(int(i) for i in np.flatnonzero(reactivated))

        d[active] = lower[active]
        residual = np.asarray(k.dot(d) - f, dtype=float)
        released = active & (residual < active_multiplier_tol)
        if np.any(released):
            active[released] = False

        # Metrics describe the membership selected for the next reduced solve.
        free = ~active
        d[active] = lower[active]
        if np.any(released) or np.any(reactivated):
            # Do not claim convergence until the selected membership is solved.
            free_residual = float("inf")
        else:
            residual = np.asarray(k.dot(d) - f, dtype=float)
            free_residual = (
                float(np.max(np.abs(residual[free]))) if np.any(free) else 0.0
            )
        residual = np.asarray(k.dot(d) - f, dtype=float)
        minimum_multiplier = (
            float(np.min(residual[active])) if np.any(active) else 0.0
        )
        active_bound_error = (
            float(np.max(np.abs(d[active] - lower[active])))
            if np.any(active)
            else 0.0
        )
        maximum_phase_increase = float(np.max(d - lower))
        unchanged = previous_active is not None and np.array_equal(active, previous_active)
        phase_functional = functional(k, f, d)
        history.append(
            {
                "iteration": iteration,
                "active_count": int(np.count_nonzero(active)),
                "free_count": int(np.count_nonzero(free)),
                "newly_released_count": int(np.count_nonzero(released)),
                "newly_reactivated_count": int(np.count_nonzero(reactivated)),
                "free_residual_infinity_norm": free_residual,
                "minimum_active_multiplier": minimum_multiplier,
                "active_bound_error": active_bound_error,
                "phase_functional": phase_functional,
                "maximum_phase_increase_from_F3": maximum_phase_increase,
                "membership_unchanged": unchanged,
            }
        )
        converged = (
            not np.any(released)
            and not np.any(reactivated)
            and free_residual <= free_residual_tol
            and minimum_multiplier >= active_multiplier_tol
            and active_bound_error <= active_bound_tol
            and float(np.min(d - lower)) >= -lower_bound_tol
        )
        if converged:
            return d, active, history, True, all_reactivated
        previous_active = active.copy()
        if np.array_equal(active, active_before) and not np.all(np.isfinite(d)):
            break
    return d, active, history, False, all_reactivated


def connected_groups(released_nodes: set[int], elements: dict[int, list[int]]):
    adjacency = {node: set() for node in released_nodes}
    for conn in elements.values():
        edges = zip(conn, conn[1:] + conn[:1])
        for a, b in edges:
            if a in adjacency and b in adjacency:
                adjacency[a].add(b)
                adjacency[b].add(a)
    groups = []
    unseen = set(released_nodes)
    while unseen:
        root = min(unseen)
        stack = [root]
        unseen.remove(root)
        group = []
        while stack:
            node = stack.pop()
            group.append(node)
            for other in sorted(adjacency[node]):
                if other in unseen:
                    unseen.remove(other)
                    stack.append(other)
        groups.append(sorted(group))
    return sorted(groups, key=lambda values: (-len(values), values[0]))


def frame_rows(path: Path, tag: str) -> list[dict[str, str]]:
    return [row for row in read_csv(path) if row["frame_tag"] == tag]


def max_abs_mapping_difference(rows_a, rows_b, key_columns, value_columns):
    def mapping(rows):
        return {
            tuple(row[column] for column in key_columns): tuple(
                float(row[column]) for column in value_columns
            )
            for row in rows
        }
    a, b = mapping(rows_a), mapping(rows_b)
    if set(a) != set(b):
        return None
    return max(
        (abs(x - y) for key in a for x, y in zip(a[key], b[key])),
        default=0.0,
    )


def solve(args):
    args.out_dir.mkdir(parents=True, exist_ok=True)
    nodes, elements = load_mesh(args.model_dir)
    labels = sorted(nodes)
    label_index = {node: i for i, node in enumerate(labels)}

    phase_path = args.source_dir / "D3D_PHASE_NODE_STATE_BY_FRAME.csv"
    state_path = args.source_dir / "D3D_STATE_BY_FRAME.csv"
    phase_f3 = frame_rows(phase_path, SOURCE_TAG)
    phase_f4 = frame_rows(phase_path, COMPARISON_TAG)
    state_f3 = frame_rows(state_path, SOURCE_TAG)
    state_f4 = frame_rows(state_path, COMPARISON_TAG)
    phase_by_node = {
        int(row["node"]): float(row["recovered_d_mean"]) for row in phase_f3
    }
    h_by_ip = {
        (int(row["element"]), int(row["uel_integration_point"])): float(
            row["odb_sdv16"]
        )
        for row in state_f3
    }

    prior_rows = read_csv(args.prior_active_set)
    prior_active = {
        int(row["node"]): bool_value(row["active_lower_bound"]) for row in prior_rows
    }
    candidate_rows = [
        row
        for row in read_csv(args.source_dir / "D3D_ACTIVE_MULTIPLIER_CANDIDATES.csv")
        if row["frame_tag"] == COMPARISON_TAG
    ]
    seed_nodes = {int(row["node"]) for row in candidate_rows}
    endpoint_nodes = {
        int(row["node"])
        for row in read_csv(args.source_dir / "D3D_ACTIVE_MULTIPLIER_CANDIDATES.csv")
        if row["frame_tag"] == "F4_segment_end"
    }
    if len(seed_nodes) != EXPECTED_SEEDS:
        raise ValueError(f"expected 30 seed nodes, found {len(seed_nodes)}")
    if seed_nodes == endpoint_nodes or len(endpoint_nodes) != 3157:
        raise ValueError("endpoint union guard failed")

    lower = np.array([phase_by_node[node] for node in labels], dtype=float)
    initial_active = np.array([prior_active[node] for node in labels], dtype=bool)
    for node in seed_nodes:
        initial_active[label_index[node]] = False

    labels2, _, k, f, assembly = assemble(nodes, elements, h_by_ip)
    if labels2 != labels:
        raise ValueError("mesh label order changed")
    residual_f3 = np.asarray(k.dot(lower) - f, dtype=float)
    prior_active_mask = np.array([prior_active[node] for node in labels], dtype=bool)
    prior_free = ~prior_active_mask

    write_csv(
        args.out_dir / "D3D_A1_SOURCE_NODAL_LOWER_BOUND.csv",
        ["node", "x", "y", "d_lower_bound_F3"],
        (
            {
                "node": node,
                "x": nodes[node][0],
                "y": nodes[node][1],
                "d_lower_bound_F3": phase_by_node[node],
            }
            for node in labels
        ),
    )
    write_csv(
        args.out_dir / "D3D_A1_SOURCE_IP_H.csv",
        ["element", "integration_point", "H_F3"],
        (
            {"element": element, "integration_point": ip, "H_F3": value}
            for (element, ip), value in sorted(h_by_ip.items())
        ),
    )
    write_csv(
        args.out_dir / "D3D_A1_SOURCE_ACTIVE_SET.csv",
        ["node", "x", "y", "active_F3", "initial_active_A1", "initial_release_seed"],
        (
            {
                "node": node,
                "x": nodes[node][0],
                "y": nodes[node][1],
                "active_F3": prior_active[node],
                "initial_active_A1": bool(initial_active[i]),
                "initial_release_seed": node in seed_nodes,
            }
            for i, node in enumerate(labels)
        ),
    )
    seed_by_node = {int(row["node"]): row for row in candidate_rows}
    write_csv(
        args.out_dir / "D3D_A1_INITIAL_RELEASE_SEED.csv",
        ["node", "x", "y", "multiplier_F3", "d_F3"],
        (
            {
                "node": node,
                "x": nodes[node][0],
                "y": nodes[node][1],
                "multiplier_F3": seed_by_node[node]["multiplier"],
                "d_F3": phase_by_node[node],
            }
            for node in sorted(seed_nodes)
        ),
    )

    manifest = {row["frame_tag"]: row for row in read_csv(args.source_dir / "D3D_FRAME_MANIFEST.csv")}
    energy = {
        row["frame_tag"]: row
        for row in json.loads(
            (args.source_dir / "D3D_RECONSTRUCTED_ENERGY_BY_FRAME.json").read_text(
                encoding="utf-8"
            )
        )["frames"]
    }
    phase_difference = max_abs_mapping_difference(
        phase_f3, phase_f4, ["node"], ["recovered_d_mean"]
    )
    state_difference = max_abs_mapping_difference(
        state_f3,
        state_f4,
        ["element", "uel_integration_point"],
        ["odb_sdv12", "odb_sdv13", "odb_sdv15", "odb_sdv16"],
    )
    audit = {
        "classification": "stage_d3d_a1_source_state_audit",
        "source_job": "1377558.mmaster02",
        "source_frame": SOURCE_TAG,
        "checkpoint_u2_mm": float(manifest[SOURCE_TAG]["actual_top_u2_mean"]),
        "nodes": len(phase_by_node),
        "elements": len(elements),
        "integration_points": len(h_by_ip),
        "initial_active_nodes": int(np.count_nonzero(prior_active_mask)),
        "initial_free_nodes": int(np.count_nonzero(prior_free)),
        "negative_active_multipliers": len(seed_nodes),
        "minimum_active_multiplier": float(np.min(residual_f3[prior_active_mask])),
        "free_residual_infinity_norm": float(
            np.max(np.abs(residual_f3[prior_free]))
        ),
        "non_positive_detJ": int(assembly["non_positive_detJ"]),
        "F3_F4_initial_phase_max_abs_difference": phase_difference,
        "F3_F4_initial_state_max_abs_difference": state_difference,
        "F3_F4_initial_displacement_abs_difference": abs(
            float(manifest[SOURCE_TAG]["actual_top_u2_mean"])
            - float(manifest[COMPARISON_TAG]["actual_top_u2_mean"])
        ),
        "F3_F4_initial_reaction_abs_difference": abs(
            float(manifest[SOURCE_TAG]["top_rf2_sum"])
            - float(manifest[COMPARISON_TAG]["top_rf2_sum"])
        ),
        "F3_F4_initial_energy_abs_difference": abs(
            float(energy[SOURCE_TAG]["total_reconstructed_internal_energy"])
            - float(energy[COMPARISON_TAG]["total_reconstructed_internal_energy"])
        ),
        "initial_release_seed_nodes": len(seed_nodes),
        "endpoint_nodes": len(endpoint_nodes),
        "endpoint_union_used_as_release_set": False,
        "state_reset": False,
    }
    write_json(args.out_dir / "D3D_A1_SOURCE_STATE_AUDIT.json", audit)

    d_final, active_final, history, converged, reactivated_indices = solve_primal_dual(
        k, f, lower, initial_active, max_iterations=args.max_iterations
    )
    residual = np.asarray(k.dot(d_final) - f, dtype=float)
    free_final = ~active_final
    delta = d_final - lower
    released_nodes = {
        node
        for i, node in enumerate(labels)
        if prior_active_mask[i] and not active_final[i]
    }
    reactivated_nodes = {
        labels[i] for i in reactivated_indices if not initial_active[i]
    }
    groups = connected_groups(released_nodes, elements)

    write_csv(
        args.out_dir / "D3D_A1_ACTIVE_SET_ITERATIONS.csv",
        [
            "iteration", "active_count", "free_count", "newly_released_count",
            "newly_reactivated_count", "free_residual_infinity_norm",
            "minimum_active_multiplier", "active_bound_error",
            "phase_functional", "maximum_phase_increase_from_F3",
            "membership_unchanged",
        ],
        history,
    )
    write_csv(
        args.out_dir / "D3D_A1_UPDATED_NODAL_D.csv",
        ["node", "x", "y", "d_F3", "d_D3D_A1", "d_update"],
        (
            {
                "node": node, "x": nodes[node][0], "y": nodes[node][1],
                "d_F3": lower[i], "d_D3D_A1": d_final[i], "d_update": delta[i],
            }
            for i, node in enumerate(labels)
        ),
    )
    write_csv(
        args.out_dir / "D3D_A1_UPDATED_ACTIVE_SET_BY_NODE.csv",
        ["node", "x", "y", "active_lower_bound", "d_D3D_A1", "d_lb_F3",
         "bound_margin", "residual_Kd_minus_f", "initial_release_seed"],
        (
            {
                "node": node, "x": nodes[node][0], "y": nodes[node][1],
                "active_lower_bound": bool(active_final[i]),
                "d_D3D_A1": d_final[i], "d_lb_F3": lower[i],
                "bound_margin": delta[i], "residual_Kd_minus_f": residual[i],
                "initial_release_seed": node in seed_nodes,
            }
            for i, node in enumerate(labels)
        ),
    )
    release_rows = [
        {
            "node": node, "x": nodes[node][0], "y": nodes[node][1],
            "initial_release_seed": node in seed_nodes,
            "d_update": delta[label_index[node]],
            "residual_Kd_minus_f": residual[label_index[node]],
        }
        for node in sorted(released_nodes)
    ]
    write_csv(
        args.out_dir / "D3D_A1_RELEASED_NODES.csv",
        ["node", "x", "y", "initial_release_seed", "d_update", "residual_Kd_minus_f"],
        release_rows,
    )
    write_csv(
        args.out_dir / "D3D_A1_REACTIVATED_NODES.csv",
        ["node", "x", "y", "was_initial_seed"],
        (
            {
                "node": node, "x": nodes[node][0], "y": nodes[node][1],
                "was_initial_seed": node in seed_nodes,
            }
            for node in sorted(reactivated_nodes)
        ),
    )

    functional_before = functional(k, f, lower)
    functional_after = functional(k, f, d_final)
    functional_record = {
        "classification": "stage_d3d_a1_phase_functional_comparison",
        "functional_before_update": functional_before,
        "functional_after_update": functional_after,
        "functional_change": functional_after - functional_before,
        "functional_nonincrease": functional_after <= functional_before + 1.0e-15,
    }
    write_json(
        args.out_dir / "D3D_A1_PHASE_FUNCTIONAL_COMPARISON.json",
        functional_record,
    )
    kkt = {
        "classification": "stage_d3d_a1_kkt_computed_unvalidated",
        "deterministic_convergence_status": bool(converged),
        "iteration_count": len(history),
        "final_active_nodes": int(np.count_nonzero(active_final)),
        "final_free_nodes": int(np.count_nonzero(free_final)),
        "free_residual_infinity_norm": float(
            np.max(np.abs(residual[free_final])) if np.any(free_final) else 0.0
        ),
        "minimum_active_multiplier": float(
            np.min(residual[active_final]) if np.any(active_final) else 0.0
        ),
        "active_bound_error": float(
            np.max(np.abs(delta[active_final])) if np.any(active_final) else 0.0
        ),
        "minimum_lower_bound_margin": float(np.min(delta)),
        "phase_decrease_violations": int(np.count_nonzero(delta < -LOWER_BOUND_TOL)),
        "lower_bound_violations": int(np.count_nonzero(delta < -LOWER_BOUND_TOL)),
        "maximum_phase_update": float(np.max(delta)),
        "normalized_L2_phase_update": float(
            np.linalg.norm(delta) / max(np.linalg.norm(lower), 1.0e-30)
        ),
        "H_changes": 0,
        "source_phase_coverage": len(phase_by_node),
        "source_H_coverage": len(h_by_ip),
        "final_H_coverage": len(h_by_ip),
        "non_positive_detJ": int(assembly["non_positive_detJ"]),
        "state_reset": False,
        "spatial_variation_retained": bool(np.ptp(d_final) > 0.0),
        "tolerances": {
            "free_residual_infinity_norm": FREE_RESIDUAL_TOL,
            "minimum_active_multiplier": ACTIVE_MULTIPLIER_TOL,
            "active_bound_error": ACTIVE_BOUND_TOL,
            "phase_lower_bound": LOWER_BOUND_TOL,
        },
    }
    write_json(args.out_dir / "D3D_A1_KKT_VALIDATION.json", kkt)
    summary = {
        **kkt,
        "classification": "stage_d3d_a1_checkpoint_obstacle_update_unvalidated",
        "initial_active_nodes": EXPECTED_ACTIVE,
        "initial_free_nodes": EXPECTED_FREE,
        "initial_release_seed_nodes": len(seed_nodes),
        "total_nodes_released_relative_to_F3": len(released_nodes),
        "original_30_remaining_free": len(seed_nodes & released_nodes),
        "additional_nodes_released": len(released_nodes - seed_nodes),
        "nodes_reactivated": len(reactivated_nodes),
        "spatial_group_count": len(groups),
        "spatial_groups": [
            {"group_id": i + 1, "node_count": len(group), "node_labels": group}
            for i, group in enumerate(groups)
        ],
        "endpoint_union_release_prohibited": True,
        "endpoint_union_used_as_release_set": False,
        "abaqus_job_submitted": False,
        "pbs_artifact_created": False,
    }
    write_json(args.out_dir / "D3D_A1_UPDATE_SUMMARY.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir", type=Path,
        default=Path("runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment"),
    )
    parser.add_argument(
        "--prior-active-set", type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2/D3_ACTIVE_SET_BY_NODE.csv"),
    )
    parser.add_argument(
        "--model-dir", type=Path,
        default=Path("models/state_transfer/d3_interrupted_transfer"),
    )
    parser.add_argument(
        "--out-dir", type=Path,
        default=Path("runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_update"),
    )
    parser.add_argument("--max-iterations", type=int, default=MAX_ITERATIONS)
    args = parser.parse_args()
    solve(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
