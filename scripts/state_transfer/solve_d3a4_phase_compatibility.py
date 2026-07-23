#!/usr/bin/env python3
"""Solve the offline D3A4 constrained phase-compatibility projection."""

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.linalg import spsolve


GC = 2.7e-3
LC = 0.015
THICKNESS = 1.0
GAUSS = [
    (-1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
    (1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
    (1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
    (-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def shape_and_grad(xi, eta):
    n = np.array([
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta),
    ])
    dndxi = np.array([
        [-0.25 * (1.0 - eta), -0.25 * (1.0 - xi)],
        [0.25 * (1.0 - eta), -0.25 * (1.0 + xi)],
        [0.25 * (1.0 + eta), 0.25 * (1.0 + xi)],
        [-0.25 * (1.0 + eta), 0.25 * (1.0 - xi)],
    ])
    return n, dndxi


def jacobian(coords, dndxi):
    j = coords.T.dot(dndxi)
    det = float(np.linalg.det(j))
    inv_j = np.linalg.inv(j)
    return det, inv_j


def load_mesh(model_dir):
    nodes = {}
    for row in read_csv(model_dir / "target" / "target_nodes.csv"):
        nodes[int(row["node"])] = (float(row["x"]), float(row["y"]))
    elements = {}
    for row in read_csv(model_dir / "target" / "target_elements.csv"):
        elements[int(row["element"])] = [int(row["n1"]), int(row["n2"]), int(row["n3"]), int(row["n4"])]
    return nodes, elements


def load_f1_lower_bound(forensic_dir):
    rows = [row for row in read_csv(forensic_dir / "D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv") if row["frame_tag"] == "F1_equilibrated"]
    return {int(row["node"]): float(row["recovered_d_mean"]) for row in rows}


def load_f1_h(forensic_dir):
    rows = [row for row in read_csv(forensic_dir / "D3A3_STATE_BY_FRAME.csv") if row["frame_tag"] == "F1_equilibrated"]
    h = {}
    sdv12 = {}
    sdv13 = {}
    for row in rows:
        key = (int(row["element"]), int(row["uel_integration_point"]))
        h[key] = float(row["odb_sdv16"])
        sdv12[key] = float(row["odb_sdv12"])
        sdv13[key] = float(row["odb_sdv13"])
    return h, sdv12, sdv13


def load_forensic_residual(forensic_dir):
    return {
        int(row["node"]): float(row["F1_phase_residual"])
        for row in read_csv(forensic_dir / "D3A3_F1_PHASE_RESIDUAL_BY_NODE.csv")
    }


def assemble(nodes, elements, h_by_ip):
    labels = sorted(nodes)
    index = {node: i for i, node in enumerate(labels)}
    row_idx = []
    col_idx = []
    data = []
    f = np.zeros(len(labels))
    non_positive_detj = 0
    ip_count = 0
    for element, conn in sorted(elements.items()):
        coords = np.array([nodes[node] for node in conn], dtype=float)
        elem_indices = [index[node] for node in conn]
        for ip, (xi, eta) in enumerate(GAUSS, start=1):
            h = h_by_ip[(element, ip)]
            n, dndxi = shape_and_grad(xi, eta)
            detj, inv_j = jacobian(coords, dndxi)
            if detj <= 0.0:
                non_positive_detj += 1
            dndx = dndxi.dot(inv_j)
            weight = detj * THICKNESS
            mass_coeff = (GC / LC) + 2.0 * h
            local_k = GC * LC * dndx.dot(dndx.T) + mass_coeff * np.outer(n, n)
            local_f = 2.0 * h * n
            local_k *= weight
            local_f *= weight
            for a, ia in enumerate(elem_indices):
                f[ia] += local_f[a]
                for b, ib in enumerate(elem_indices):
                    row_idx.append(ia)
                    col_idx.append(ib)
                    data.append(local_k[a, b])
            ip_count += 1
    k = coo_matrix((data, (row_idx, col_idx)), shape=(len(labels), len(labels))).tocsr()
    return labels, index, k, f, {"non_positive_detJ": non_positive_detj, "integration_points": ip_count}


def solve_unconstrained(k, f):
    return np.asarray(spsolve(k, f), dtype=float)


def solve_lower_bound_active_set(k, f, lb, tol=1.0e-12, max_iter=200):
    n = len(lb)
    d = lb.copy()
    active = np.ones(n, dtype=bool)
    history = []
    stable_count = 0
    previous_active = None
    for iteration in range(1, max_iter + 1):
        r = np.asarray(k.dot(d) - f, dtype=float)
        release = active & (r < -tol)
        if np.any(release):
            active[release] = False
        free = ~active
        if np.any(free):
            free_idx = np.flatnonzero(free)
            active_idx = np.flatnonzero(active)
            rhs = f[free_idx].copy()
            if len(active_idx):
                rhs -= k[free_idx, :][:, active_idx].dot(lb[active_idx])
            d_free = np.asarray(spsolve(k[free_idx, :][:, free_idx], rhs), dtype=float)
            d[active] = lb[active]
            d[free_idx] = d_free
            violate = free_idx[d_free < lb[free_idx] - tol]
            if len(violate):
                d[violate] = lb[violate]
                active[violate] = True
        else:
            d[:] = lb
        r = np.asarray(k.dot(d) - f, dtype=float)
        free = ~active
        active_violation = np.min(r[active]) if np.any(active) else 0.0
        free_res_inf = np.max(np.abs(r[free])) if np.any(free) else 0.0
        lb_violation = np.min(d - lb)
        unchanged = previous_active is not None and np.array_equal(active, previous_active)
        stable_count = stable_count + 1 if unchanged else 0
        history.append({
            "iteration": iteration,
            "active_nodes": int(np.count_nonzero(active)),
            "free_nodes": int(np.count_nonzero(free)),
            "released_this_iteration": int(np.count_nonzero(release)),
            "free_residual_inf": float(free_res_inf),
            "minimum_active_multiplier": float(active_violation),
            "minimum_bound_margin": float(lb_violation),
            "membership_unchanged": bool(unchanged),
        })
        if free_res_inf <= 1.0e-10 and active_violation >= -1.0e-10 and lb_violation >= -1.0e-12 and stable_count >= 1:
            return d, active, history, True
        previous_active = active.copy()
    return d, active, history, False


def functional(k, f, d):
    return 0.5 * float(d.dot(k.dot(d))) - float(f.dot(d))


def corr(a, b):
    if len(a) < 2:
        return None
    aa = np.asarray(a, dtype=float)
    bb = np.asarray(b, dtype=float)
    if float(np.std(aa)) == 0.0 or float(np.std(bb)) == 0.0:
        return None
    return float(np.corrcoef(aa, bb)[0, 1])


def solve(args):
    args.out_dir.mkdir(parents=True, exist_ok=True)
    nodes, elements = load_mesh(args.model_dir)
    lb_by_node = load_f1_lower_bound(args.forensic_dir)
    h_by_ip, sdv12_by_ip, sdv13_by_ip = load_f1_h(args.forensic_dir)
    forensic_residual = load_forensic_residual(args.forensic_dir)
    labels, index, k, f, assembly = assemble(nodes, elements, h_by_ip)
    lb = np.array([lb_by_node[node] for node in labels], dtype=float)
    r_f1 = np.asarray(k.dot(lb) - f, dtype=float)
    residual_rows = []
    residual_errors = []
    for node, value in zip(labels, r_f1):
        expected = forensic_residual[node]
        error = value - expected
        residual_errors.append(error)
        x, y = nodes[node]
        residual_rows.append({
            "node": node,
            "x": x,
            "y": y,
            "reconstructed_residual": value,
            "forensic_residual": expected,
            "residual_error": error,
        })
    write_csv(args.out_dir / "D3A4_F1_RESIDUAL_RECONSTRUCTED.csv", ["node", "x", "y", "reconstructed_residual", "forensic_residual", "residual_error"], residual_rows)

    max_node = labels[int(np.argmax(np.abs(r_f1)))]
    forensic_max_node = max(forensic_residual, key=lambda node: abs(forensic_residual[node]))
    forensic_l2 = math.sqrt(sum(v * v for v in forensic_residual.values()) / len(forensic_residual))
    reconstructed_l2 = math.sqrt(float(np.dot(r_f1, r_f1)) / len(r_f1))
    assembly_audit = {
        "classification": "stage_d3a4_assembly_audit",
        "nodes": len(labels),
        "elements": len(elements),
        "integration_points": assembly["integration_points"],
        "non_positive_detJ": assembly["non_positive_detJ"],
        "node_coverage": len(residual_rows),
        "missing_nodes": len(set(labels) - set(forensic_residual)),
        "maximum_residual_reconstruction_error": max(abs(v) for v in residual_errors),
        "maximum_residual_node": max_node,
        "forensic_maximum_residual_node": forensic_max_node,
        "residual_L2": reconstructed_l2,
        "forensic_residual_L2": forensic_l2,
        "residual_L2_relative_error": abs(reconstructed_l2 - forensic_l2) / max(abs(forensic_l2), 1.0e-30),
    }
    write_json(args.out_dir / "D3A4_ASSEMBLY_AUDIT.json", assembly_audit)

    d_free = solve_unconstrained(k, f)
    d_compat, active, history, converged = solve_lower_bound_active_set(k, f, lb, args.active_tol, args.max_iter)
    r = np.asarray(k.dot(d_compat) - f, dtype=float)
    free = ~active
    delta = d_compat - lb

    recovery_f3 = {
        int(row["node"]): float(row["recovered_d_mean"])
        for row in read_csv(args.forensic_dir / "D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv")
        if row["frame_tag"] == "F3_release_last"
    }
    actual_release_delta = np.array([recovery_f3[node] - lb_by_node[node] for node in labels], dtype=float)
    unconstrained_delta = d_free - lb

    write_csv(
        args.out_dir / "D3A4_UNCONSTRAINED_NODAL_D.csv",
        ["node", "x", "y", "d_F1", "d_unconstrained", "d_unconstrained_minus_F1", "d_F3_minus_F1"],
        [
            {
                "node": node,
                "x": nodes[node][0],
                "y": nodes[node][1],
                "d_F1": lb[i],
                "d_unconstrained": d_free[i],
                "d_unconstrained_minus_F1": unconstrained_delta[i],
                "d_F3_minus_F1": actual_release_delta[i],
            }
            for i, node in enumerate(labels)
        ],
    )
    write_csv(
        args.out_dir / "D3A4_CONSTRAINED_NODAL_D.csv",
        ["node", "x", "y", "d_F1", "d_compatible", "d_compatible_minus_F1"],
        [
            {
                "node": node,
                "x": nodes[node][0],
                "y": nodes[node][1],
                "d_F1": lb[i],
                "d_compatible": d_compat[i],
                "d_compatible_minus_F1": delta[i],
            }
            for i, node in enumerate(labels)
        ],
    )
    write_csv(
        args.out_dir / "D3A4_ACTIVE_SET_BY_NODE.csv",
        ["node", "x", "y", "active_lower_bound", "d_compatible", "d_lb", "bound_margin", "residual_Kd_minus_f"],
        [
            {
                "node": node,
                "x": nodes[node][0],
                "y": nodes[node][1],
                "active_lower_bound": bool(active[i]),
                "d_compatible": d_compat[i],
                "d_lb": lb[i],
                "bound_margin": d_compat[i] - lb[i],
                "residual_Kd_minus_f": r[i],
            }
            for i, node in enumerate(labels)
        ],
    )

    kkt = {
        "classification": "stage_d3a4_active_set_kkt_metrics",
        "converged": converged,
        "iterations": len(history),
        "active_set_membership_stable": len(history) >= 2 and history[-1]["membership_unchanged"],
        "active_node_count": int(np.count_nonzero(active)),
        "free_node_count": int(np.count_nonzero(free)),
        "free_set_residual_infinity_norm": float(np.max(np.abs(r[free])) if np.any(free) else 0.0),
        "minimum_active_set_multiplier": float(np.min(r[active]) if np.any(active) else 0.0),
        "complementarity_infinity_norm": float(np.max(np.abs(r * (d_compat - lb)))),
        "minimum_d_compatible_minus_d_F1": float(np.min(delta)),
        "minimum_d_compatible": float(np.min(d_compat)),
        "maximum_d_compatible": float(np.max(d_compat)),
        "maximum_d_increase": float(np.max(delta)),
        "normalized_L2_d_increase": float(np.linalg.norm(delta) / max(np.linalg.norm(lb), 1.0e-30)),
        "predicted_healing_violations": int(np.count_nonzero(delta < -1.0e-12)),
        "history": history,
    }
    write_json(args.out_dir / "D3A4_KKT_METRICS.json", kkt)

    f_f1 = functional(k, f, lb)
    f_free = functional(k, f, d_free)
    f_compat = functional(k, f, d_compat)
    write_json(args.out_dir / "D3A4_PHASE_FUNCTIONAL_COMPARISON.json", {
        "classification": "stage_d3a4_phase_functional_comparison",
        "functional_at_F1": f_f1,
        "functional_at_unconstrained": f_free,
        "functional_at_compatible": f_compat,
        "compatible_minus_F1": f_compat - f_f1,
        "unconstrained_minus_F1": f_free - f_f1,
        "compatible_reduction_from_F1": f_f1 - f_compat,
        "unconstrained_reduction_from_F1": f_f1 - f_free,
    })
    write_json(args.out_dir / "D3A4_UNCONSTRAINED_COMPARISON.json", {
        "classification": "stage_d3a4_unconstrained_diagnostic",
        "minimum_unconstrained_minus_F1": float(np.min(unconstrained_delta)),
        "maximum_unconstrained_minus_F1": float(np.max(unconstrained_delta)),
        "normalized_L2_unconstrained_change": float(np.linalg.norm(unconstrained_delta) / max(np.linalg.norm(lb), 1.0e-30)),
        "correlation_unconstrained_change_vs_actual_F3_change": corr(unconstrained_delta, actual_release_delta),
        "actual_F3_negative_change_count_lt_minus_1e_10": int(np.count_nonzero(actual_release_delta < -1.0e-10)),
        "unconstrained_negative_change_count_lt_minus_1e_10": int(np.count_nonzero(unconstrained_delta < -1.0e-10)),
    })
    write_json(args.out_dir / "D3A4_INPUT_PROVENANCE.json", {
        "classification": "stage_d3a4_input_provenance",
        "forensic_dir": str(args.forensic_dir),
        "model_dir": str(args.model_dir),
        "lower_bound": "F1_equilibrated recovered nodal d",
        "history": "F1_equilibrated corrected SDV16",
        "Gc": GC,
        "lc": LC,
        "thickness": THICKNESS,
        "solver": "sparse_active_set_lower_bound_qp",
        "standard_solve_submitted": False,
        "fortran_compilation": False,
        "new_mesh": False,
    })

    largest = sorted(
        (
            {
                "node": node,
                "x": nodes[node][0],
                "y": nodes[node][1],
                "d_increase": float(delta[i]),
                "d_F1": float(lb[i]),
                "d_compatible": float(d_compat[i]),
            }
            for i, node in enumerate(labels)
        ),
        key=lambda row: row["d_increase"],
        reverse=True,
    )[:10]
    write_json(args.out_dir / "D3A4_COMPATIBILITY_STATUS.json", {
        "classification": "stage_d3a4_projection_solved_unvalidated",
        "largest_d_increase_locations": largest,
        "assembly_audit": assembly_audit,
        "kkt_metrics": kkt,
    })
    print("d3a4_solve_complete out_dir=%s" % args.out_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forensic-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r2_forensic"))
    parser.add_argument("--model-dir", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer"))
    parser.add_argument("--out-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/compatibility_projection_d3a4"))
    parser.add_argument("--active-tol", type=float, default=1.0e-12)
    parser.add_argument("--max-iter", type=int, default=200)
    args = parser.parse_args()
    solve(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
