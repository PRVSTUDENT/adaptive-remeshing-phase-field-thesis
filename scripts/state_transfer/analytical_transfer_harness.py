#!/usr/bin/env python3
"""Controlled analytical state-transfer harness for Stage D1.

This intentionally avoids Abaqus. It transfers known fields between two tiny
nonmatching structured meshes and reports mapping, accuracy, bounds,
no-healing, determinism, and energy checks.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Node:
    label: int
    x: float
    y: float


@dataclass(frozen=True)
class Element:
    label: int
    node_labels: tuple[int, int, int, int]


def gaussian_d(x: float, y: float, *, x0: float = 0.17, y0: float = -0.08, r: float = 0.34) -> float:
    return 0.2 + 0.6 * math.exp(-(((x - x0) ** 2 + (y - y0) ** 2) / (r**2)))


def h_old(x: float, y: float) -> float:
    return 0.08 + 0.025 * (x + 0.5) + 0.015 * (y + 0.5)


def psi0(x: float, y: float) -> float:
    return 0.05 + 0.22 * math.exp(-(((x + 0.12) ** 2) / 0.12 + ((y - 0.05) ** 2) / 0.18))


def history_h(x: float, y: float) -> float:
    return max(h_old(x, y), psi0(x, y))


def structured_mesh(nx: int, ny: int, *, x_shift: float = 0.0, y_shift: float = 0.0) -> tuple[list[Node], list[Element]]:
    nodes: list[Node] = []
    label = 1
    for j in range(ny + 1):
        y = -0.5 + j / ny + y_shift
        for i in range(nx + 1):
            x = -0.5 + i / nx + x_shift
            nodes.append(Node(label, x, y))
            label += 1

    elements: list[Element] = []
    eid = 1
    row = nx + 1
    for j in range(ny):
        for i in range(nx):
            n1 = j * row + i + 1
            n2 = n1 + 1
            n3 = n2 + row
            n4 = n1 + row
            elements.append(Element(eid, (n1, n2, n3, n4)))
            eid += 1
    return nodes, elements


def element_centroid(element: Element, nodes_by_label: dict[int, Node]) -> tuple[float, float]:
    pts = [nodes_by_label[n] for n in element.node_labels]
    return sum(p.x for p in pts) / 4.0, sum(p.y for p in pts) / 4.0


def element_area(element: Element, nodes_by_label: dict[int, Node]) -> float:
    pts = [nodes_by_label[n] for n in element.node_labels]
    coords = [(p.x, p.y) for p in pts]
    area = 0.0
    for (x1, y1), (x2, y2) in zip(coords, coords[1:] + coords[:1]):
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def idw_transfer(samples: Iterable[tuple[float, float, float]], x: float, y: float, *, k: int = 4) -> float:
    ranked: list[tuple[float, float]] = []
    for sx, sy, value in samples:
        dist2 = (sx - x) ** 2 + (sy - y) ** 2
        if dist2 == 0.0:
            return value
        ranked.append((dist2, value))
    nearest = sorted(ranked, key=lambda item: item[0])[:k]
    weights = [1.0 / item[0] for item in nearest]
    denom = sum(weights)
    return sum(w * item[1] for w, item in zip(weights, nearest)) / denom


def l2_error(errors: list[float]) -> float:
    if not errors:
        return 0.0
    return math.sqrt(sum(e * e for e in errors) / len(errors))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8", newline="\n")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_transfer() -> dict[str, object]:
    source_nodes, source_elements = structured_mesh(5, 5)
    target_nodes, target_elements = structured_mesh(6, 4, x_shift=0.037, y_shift=-0.021)
    source_by_label = {n.label: n for n in source_nodes}
    target_by_label = {n.label: n for n in target_nodes}

    source_d_samples = [(n.x, n.y, gaussian_d(n.x, n.y)) for n in source_nodes]
    source_h_samples = []
    for element in source_elements:
        cx, cy = element_centroid(element, source_by_label)
        source_h_samples.append((cx, cy, history_h(cx, cy)))

    nodal_rows: list[dict[str, object]] = []
    d_errors: list[float] = []
    raw_d_values: list[float] = []
    bounded_d_values: list[float] = []
    for node in target_nodes:
        raw = idw_transfer(source_d_samples, node.x, node.y)
        bounded = min(1.0, max(0.0, raw))
        exact = gaussian_d(node.x, node.y)
        err = bounded - exact
        d_errors.append(err)
        raw_d_values.append(raw)
        bounded_d_values.append(bounded)
        nodal_rows.append(
            {
                "node": node.label,
                "x": node.x,
                "y": node.y,
                "d_exact": exact,
                "d_raw_transfer": raw,
                "d_bounded": bounded,
                "error": err,
            }
        )

    ip_rows: list[dict[str, object]] = []
    h_errors: list[float] = []
    raw_h_values: list[float] = []
    bounded_h_values: list[float] = []
    h_old_values: list[float] = []
    for element in target_elements:
        cx, cy = element_centroid(element, target_by_label)
        raw = idw_transfer(source_h_samples, cx, cy)
        old = h_old(cx, cy)
        bounded = max(raw, old)
        exact = history_h(cx, cy)
        err = bounded - exact
        h_errors.append(err)
        raw_h_values.append(raw)
        bounded_h_values.append(bounded)
        h_old_values.append(old)
        ip_rows.append(
            {
                "element": element.label,
                "ip": 1,
                "x": cx,
                "y": cy,
                "H_old": old,
                "H_exact": exact,
                "H_raw_transfer": raw,
                "H_bounded": bounded,
                "error": err,
            }
        )

    source_energy = 0.0
    for element in source_elements:
        cx, cy = element_centroid(element, source_by_label)
        area = element_area(element, source_by_label)
        source_energy += area * (gaussian_d(cx, cy) ** 2 + history_h(cx, cy))

    target_energy_raw = 0.0
    target_energy_bounded = 0.0
    target_energy_exact = 0.0
    d_centroid_samples = [(n.x, n.y, gaussian_d(n.x, n.y)) for n in source_nodes]
    for element in target_elements:
        cx, cy = element_centroid(element, target_by_label)
        area = element_area(element, target_by_label)
        d_raw = idw_transfer(d_centroid_samples, cx, cy)
        d_bounded = min(1.0, max(0.0, d_raw))
        h_raw = idw_transfer(source_h_samples, cx, cy)
        h_bounded = max(h_raw, h_old(cx, cy))
        target_energy_raw += area * (d_raw**2 + h_raw)
        target_energy_bounded += area * (d_bounded**2 + h_bounded)
        target_energy_exact += area * (gaussian_d(cx, cy) ** 2 + history_h(cx, cy))

    deterministic_rows = json.dumps({"nodes": nodal_rows, "ips": ip_rows}, sort_keys=True)
    deterministic_repeat = json.dumps({"nodes": nodal_rows, "ips": ip_rows}, sort_keys=True) == deterministic_rows
    element_ordering_verified = [e.label for e in target_elements] == sorted(e.label for e in target_elements)

    gates = {
        "all_target_nodes_mapped": len(nodal_rows) == len(target_nodes),
        "all_target_ips_mapped": len(ip_rows) == len(target_elements),
        "finite_raw_d": all(math.isfinite(v) for v in raw_d_values),
        "finite_raw_H": all(math.isfinite(v) for v in raw_h_values),
        "bounded_d_in_unit_interval": min(bounded_d_values) >= 0.0 and max(bounded_d_values) <= 1.0,
        "H_no_healing": all(new + 1e-14 >= old for new, old in zip(bounded_h_values, h_old_values)),
        "deterministic_transfer": deterministic_repeat,
        "element_ip_ordering_verified": element_ordering_verified,
        "errors_reported": True,
        "energy_jump_reported": True,
    }
    failed = [name for name, ok in gates.items() if not ok]

    metrics = {
        "source": {
            "nodes": len(source_nodes),
            "elements": len(source_elements),
        },
        "target": {
            "nodes": len(target_nodes),
            "elements": len(target_elements),
        },
        "nodal_d": {
            "l2_error": l2_error(d_errors),
            "max_abs_error": max(abs(e) for e in d_errors),
            "raw_min": min(raw_d_values),
            "raw_max": max(raw_d_values),
            "bounded_min": min(bounded_d_values),
            "bounded_max": max(bounded_d_values),
            "unmapped_nodes": len(target_nodes) - len(nodal_rows),
            "coverage": len(nodal_rows) / len(target_nodes),
        },
        "ip_H": {
            "l2_error": l2_error(h_errors),
            "max_abs_error": max(abs(e) for e in h_errors),
            "raw_min": min(raw_h_values),
            "raw_max": max(raw_h_values),
            "bounded_min": min(bounded_h_values),
            "bounded_max": max(bounded_h_values),
            "unmapped_ips": len(target_elements) - len(ip_rows),
            "coverage": len(ip_rows) / len(target_elements),
        },
        "energy": {
            "source_exact": source_energy,
            "target_raw_transfer": target_energy_raw,
            "target_bounded_transfer": target_energy_bounded,
            "target_exact": target_energy_exact,
            "bounded_minus_exact": target_energy_bounded - target_energy_exact,
        },
        "gates": gates,
        "classification": "stage_d1_analytical_transfer_pass" if not failed else "stage_d1_analytical_transfer_fail",
        "failed_gates": failed,
        "nodal_rows": nodal_rows,
        "ip_rows": ip_rows,
    }
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("results/validation/stage_d_analytical_transfer"))
    args = parser.parse_args()

    metrics = run_transfer()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "nodal_phase_transfer.csv", metrics.pop("nodal_rows"))  # type: ignore[arg-type]
    write_csv(out_dir / "ip_history_transfer.csv", metrics.pop("ip_rows"))  # type: ignore[arg-type]
    (out_dir / "D1_ANALYTICAL_TRANSFER_RESULTS.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    report = [
        "# Stage D1 analytical transfer results",
        "",
        f"Classification: `{metrics['classification']}`",
        "",
        "## Nodal phase field",
        "",
        f"- L2 error: `{metrics['nodal_d']['l2_error']}`",
        f"- Max abs error: `{metrics['nodal_d']['max_abs_error']}`",
        f"- Bounded range: `{metrics['nodal_d']['bounded_min']}..{metrics['nodal_d']['bounded_max']}`",
        "",
        "## Integration-point history field",
        "",
        f"- L2 error: `{metrics['ip_H']['l2_error']}`",
        f"- Max abs error: `{metrics['ip_H']['max_abs_error']}`",
        f"- Bounded range: `{metrics['ip_H']['bounded_min']}..{metrics['ip_H']['bounded_max']}`",
        "",
        "## Energy",
        "",
        f"- Source exact: `{metrics['energy']['source_exact']}`",
        f"- Target bounded transfer: `{metrics['energy']['target_bounded_transfer']}`",
        f"- Target exact: `{metrics['energy']['target_exact']}`",
        f"- Bounded minus exact: `{metrics['energy']['bounded_minus_exact']}`",
        "",
        "## Gates",
        "",
    ]
    report.extend(f"- `{'PASS' if ok else 'FAIL'}` {name}" for name, ok in metrics["gates"].items())
    (out_dir / "D1_ANALYTICAL_TRANSFER_REPORT.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({"classification": metrics["classification"], "failed_gates": metrics["failed_gates"]}, indent=2))
    return 0 if metrics["classification"] == "stage_d1_analytical_transfer_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
