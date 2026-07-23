#!/usr/bin/env python3
"""Analyze D3A3-R2 fixed-phase compatibility and release healing from forensic replay."""

import argparse
import csv
import json
import math
from pathlib import Path


GC = 2.7e-3
LC = 0.015
THICKNESS = 1.0
GAUSS = [
    (-1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
    (1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
    (1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
    (-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
]
THRESHOLDS = [-1.0e-10, -1.0e-8, -1.0e-6, -1.0e-4, -1.0e-3]


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
    n = [
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta),
    ]
    dndxi = [
        (-0.25 * (1.0 - eta), -0.25 * (1.0 - xi)),
        (0.25 * (1.0 - eta), -0.25 * (1.0 + xi)),
        (0.25 * (1.0 + eta), 0.25 * (1.0 + xi)),
        (-0.25 * (1.0 + eta), 0.25 * (1.0 - xi)),
    ]
    return n, dndxi


def jacobian(coords, dndxi):
    j11 = sum(coords[i][0] * dndxi[i][0] for i in range(4))
    j12 = sum(coords[i][0] * dndxi[i][1] for i in range(4))
    j21 = sum(coords[i][1] * dndxi[i][0] for i in range(4))
    j22 = sum(coords[i][1] * dndxi[i][1] for i in range(4))
    det = j11 * j22 - j12 * j21
    inv = [[j22 / det, -j12 / det], [-j21 / det, j11 / det]]
    return det, inv


def grad_shape(dndxi, inv_j):
    out = []
    for dxi, deta in dndxi:
        dx = dxi * inv_j[0][0] + deta * inv_j[1][0]
        dy = dxi * inv_j[0][1] + deta * inv_j[1][1]
        out.append((dx, dy))
    return out


def load_mesh(model_dir):
    nodes = {
        int(row["node"]): (float(row["x"]), float(row["y"]))
        for row in read_csv(model_dir / "target" / "target_nodes.csv")
    }
    elements = {
        int(row["element"]): [int(row["n1"]), int(row["n2"]), int(row["n3"]), int(row["n4"])]
        for row in read_csv(model_dir / "target" / "target_elements.csv")
    }
    return nodes, elements


def load_recovered(target_dir, tag):
    rows = [row for row in read_csv(target_dir / "D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv") if row["frame_tag"] == tag]
    return {int(row["node"]): float(row["recovered_d_mean"]) for row in rows}


def load_state(target_dir, tag, field):
    out = {}
    rows = [row for row in read_csv(target_dir / "D3A3_STATE_BY_FRAME.csv") if row["frame_tag"] == tag]
    for row in rows:
        value = row.get(field, "")
        if value not in ("", None):
            out[(int(row["element"]), int(row["uel_integration_point"]))] = float(value)
    return out


def correlation(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if math.isfinite(x) and math.isfinite(y)]
    if len(pairs) < 2:
        return None
    mx = sum(x for x, _ in pairs) / len(pairs)
    my = sum(y for _, y in pairs) / len(pairs)
    vx = sum((x - mx) ** 2 for x, _ in pairs)
    vy = sum((y - my) ** 2 for _, y in pairs)
    if vx <= 0.0 or vy <= 0.0:
        return None
    cov = sum((x - mx) * (y - my) for x, y in pairs)
    return cov / math.sqrt(vx * vy)


def adjacent_h(node, elements, h_by_ip):
    values = []
    for element, conn in elements.items():
        if node not in conn:
            continue
        for ip in range(1, 5):
            value = h_by_ip.get((element, ip))
            if value is not None:
                values.append(value)
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None}
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def analyze(target_dir, model_dir):
    nodes, elements = load_mesh(model_dir)
    d_f1 = load_recovered(target_dir, "F1_equilibrated")
    d_f3 = load_recovered(target_dir, "F3_release_last")
    h_f1 = load_state(target_dir, "F1_equilibrated", "odb_sdv16")
    h_f3 = load_state(target_dir, "F3_release_last", "odb_sdv16")

    residual = {node: 0.0 for node in d_f1}
    for element, conn in elements.items():
        if any(node not in d_f1 for node in conn):
            continue
        coords = [nodes[node] for node in conn]
        dvals = [d_f1[node] for node in conn]
        for ip, (xi, eta) in enumerate(GAUSS, start=1):
            h = h_f1[(element, ip)]
            nvals, dndxi = shape_and_grad(xi, eta)
            detj, inv_j = jacobian(coords, dndxi)
            dndx = grad_shape(dndxi, inv_j)
            d_ip = sum(nvals[i] * dvals[i] for i in range(4))
            grad_d = (
                sum(dndx[i][0] * dvals[i] for i in range(4)),
                sum(dndx[i][1] * dvals[i] for i in range(4)),
            )
            weight = detj * THICKNESS
            for a, node in enumerate(conn):
                grad_term = GC * LC * (dndx[a][0] * grad_d[0] + dndx[a][1] * grad_d[1])
                local_term = nvals[a] * (((GC / LC) + 2.0 * h) * d_ip - 2.0 * h)
                residual[node] += (grad_term + local_term) * weight

    healing_rows = []
    deltas = []
    residual_values = []
    for node in sorted(d_f1):
        if node not in d_f3:
            continue
        delta = d_f3[node] - d_f1[node]
        deltas.append(delta)
        residual_values.append(residual[node])
        x, y = nodes[node]
        healing_rows.append({
            "node": node,
            "x": x,
            "y": y,
            "F1_d": d_f1[node],
            "F3_d": d_f3[node],
            "F3_minus_F1_d": delta,
            "F1_phase_residual": residual[node],
        })

    residual_rows = []
    for node in sorted(residual):
        x, y = nodes[node]
        residual_rows.append({
            "node": node,
            "x": x,
            "y": y,
            "F1_phase_residual": residual[node],
            "F1_phase_residual_abs": abs(residual[node]),
        })

    max_res_node = max(residual, key=lambda n: abs(residual[n]))
    max_heal_row = min(healing_rows, key=lambda row: float(row["F3_minus_F1_d"]))
    healing_negative = [row for row in healing_rows if float(row["F3_minus_F1_d"]) < -1.0e-10]
    if healing_negative:
        xs = [float(row["x"]) for row in healing_negative]
        ys = [float(row["y"]) for row in healing_negative]
        bbox = {"x_min": min(xs), "x_max": max(xs), "y_min": min(ys), "y_max": max(ys)}
    else:
        bbox = None

    max_heal_node = int(max_heal_row["node"])
    status = {
        "classification": "stage_d3a3_f1_phase_compatibility_analyzed",
        "residual_L2_norm": math.sqrt(sum(v * v for v in residual.values()) / len(residual)),
        "maximum_residual_abs": abs(residual[max_res_node]),
        "maximum_residual_node": max_res_node,
        "negative_d_change_counts": {str(t): sum(1 for d in deltas if d < t) for t in THRESHOLDS},
        "correlation_F1_residual_vs_released_d_change": correlation(residual_values, deltas),
        "healing_region_bounding_box": bbox,
        "maximum_healing_location": {
            "node": max_heal_node,
            "x": float(max_heal_row["x"]),
            "y": float(max_heal_row["y"]),
            "F1_d": float(max_heal_row["F1_d"]),
            "F3_d": float(max_heal_row["F3_d"]),
            "F3_minus_F1_d": float(max_heal_row["F3_minus_F1_d"]),
            "F1_phase_residual": float(max_heal_row["F1_phase_residual"]),
            "F1_H_adjacent_ip": adjacent_h(max_heal_node, elements, h_f1),
            "F3_H_adjacent_ip": adjacent_h(max_heal_node, elements, h_f3),
        },
    }
    write_csv(target_dir / "D3A3_F1_PHASE_RESIDUAL_BY_NODE.csv", ["node", "x", "y", "F1_phase_residual", "F1_phase_residual_abs"], residual_rows)
    write_csv(target_dir / "D3A3_RELEASE_HEALING_LOCATIONS.csv", ["node", "x", "y", "F1_d", "F3_d", "F3_minus_F1_d", "F1_phase_residual"], healing_rows)
    write_json(target_dir / "D3A3_F1_PHASE_COMPATIBILITY.json", status)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r2_forensic"))
    parser.add_argument("--model-dir", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer"))
    args = parser.parse_args()
    status = analyze(args.target_dir, args.model_dir)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
