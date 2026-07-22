#!/usr/bin/env python3
"""Build a tiny Stage D2 transfer-ingestion package.

The package is intentionally not a Molnar fracture model. It creates two tiny
nonmatching meshes, evaluates source d/H fields, transfers them to the target,
and writes the target-state CSV/provenance/support-map files that a later D2A
Abaqus/UEL ingestion job must consume and verify.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from analytical_transfer_harness import (
    element_area,
    element_centroid,
    gaussian_d,
    h_old,
    history_h,
    idw_transfer,
    psi0,
    structured_mesh,
)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def node_rows(nodes) -> list[dict[str, Any]]:
    return [{"node": n.label, "x": n.x, "y": n.y} for n in nodes]


def element_rows(elements) -> list[dict[str, Any]]:
    return [
        {
            "element": e.label,
            "n1": e.node_labels[0],
            "n2": e.node_labels[1],
            "n3": e.node_labels[2],
            "n4": e.node_labels[3],
        }
        for e in elements
    ]


def nearest_support(samples: list[tuple[float, float, float, str]], x: float, y: float, *, k: int = 4) -> list[str]:
    ranked = sorted(
        (((sx - x) ** 2 + (sy - y) ** 2, label) for sx, sy, _value, label in samples),
        key=lambda item: item[0],
    )
    return [label for _dist, label in ranked[:k]]


def build_package(out_dir: Path) -> dict[str, Any]:
    source_nodes, source_elements = structured_mesh(3, 3)
    target_nodes, target_elements = structured_mesh(4, 2, x_shift=0.041, y_shift=-0.033)
    source_by_label = {n.label: n for n in source_nodes}
    target_by_label = {n.label: n for n in target_nodes}

    source_node_state = []
    source_d_samples: list[tuple[float, float, float, str]] = []
    for node in source_nodes:
        d = gaussian_d(node.x, node.y)
        source_d_samples.append((node.x, node.y, d, f"source_node:{node.label}"))
        source_node_state.append({"node": node.label, "x": node.x, "y": node.y, "d": d})

    source_ip_state = []
    source_h_samples: list[tuple[float, float, float, str]] = []
    for element in source_elements:
        cx, cy = element_centroid(element, source_by_label)
        h = history_h(cx, cy)
        source_h_samples.append((cx, cy, h, f"source_element:{element.label}:ip:1"))
        source_ip_state.append(
            {
                "source_element": element.label,
                "source_ip": 1,
                "x": cx,
                "y": cy,
                "d": gaussian_d(cx, cy),
                "H": h,
                "H_old": h_old(cx, cy),
                "psi0": psi0(cx, cy),
            }
        )

    target_nodal_d = []
    support_map = []
    for node in target_nodes:
        raw = idw_transfer([(x, y, v) for x, y, v, _label in source_d_samples], node.x, node.y)
        bounded = min(1.0, max(0.0, raw))
        support = nearest_support(source_d_samples, node.x, node.y)
        target_nodal_d.append(
            {
                "target_node": node.label,
                "x": node.x,
                "y": node.y,
                "d_raw": raw,
                "d_bounded": bounded,
                "d_exact_reference": gaussian_d(node.x, node.y),
                "support": ";".join(support),
            }
        )
        support_map.append(
            {
                "target_kind": "node",
                "target_label": node.label,
                "target_ip": "",
                "field": "d",
                "support": ";".join(support),
                "method": "idw_k4",
            }
        )

    target_ip_h = []
    for element in target_elements:
        cx, cy = element_centroid(element, target_by_label)
        raw = idw_transfer([(x, y, v) for x, y, v, _label in source_h_samples], cx, cy)
        old = h_old(cx, cy)
        bounded = max(raw, old)
        support = nearest_support(source_h_samples, cx, cy)
        target_ip_h.append(
            {
                "target_element": element.label,
                "target_ip": 1,
                "x": cx,
                "y": cy,
                "H_old": old,
                "H_raw": raw,
                "H_bounded": bounded,
                "H_exact_reference": history_h(cx, cy),
                "support": ";".join(support),
            }
        )
        support_map.append(
            {
                "target_kind": "element",
                "target_label": element.label,
                "target_ip": 1,
                "field": "H",
                "support": ";".join(support),
                "method": "idw_k4_then_max_H_old",
            }
        )

    target_ip_area = []
    energy = {"target_bounded_transfer": 0.0, "target_exact_reference": 0.0}
    for element in target_elements:
        cx, cy = element_centroid(element, target_by_label)
        area = element_area(element, target_by_label)
        d_row = min(target_nodal_d, key=lambda row: (row["x"] - cx) ** 2 + (row["y"] - cy) ** 2)
        h_row = next(row for row in target_ip_h if row["target_element"] == element.label)
        energy["target_bounded_transfer"] += area * (float(d_row["d_bounded"]) ** 2 + float(h_row["H_bounded"]))
        energy["target_exact_reference"] += area * (gaussian_d(cx, cy) ** 2 + history_h(cx, cy))
        target_ip_area.append({"target_element": element.label, "target_ip": 1, "area": area})
    energy["bounded_minus_exact_reference"] = energy["target_bounded_transfer"] - energy["target_exact_reference"]

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "source_nodes.csv", node_rows(source_nodes))
    write_csv(out_dir / "source_elements.csv", element_rows(source_elements))
    write_csv(out_dir / "target_nodes.csv", node_rows(target_nodes))
    write_csv(out_dir / "target_elements.csv", element_rows(target_elements))
    write_csv(out_dir / "source_ip_state.csv", source_ip_state)
    write_csv(out_dir / "source_nodal_d.csv", source_node_state)
    write_csv(out_dir / "target_transferred_nodal_d.csv", target_nodal_d)
    write_csv(out_dir / "target_transferred_ip_H.csv", target_ip_h)
    write_csv(out_dir / "source_to_target_support_map.csv", support_map)
    write_csv(out_dir / "target_ip_area.csv", target_ip_area)

    provenance = {
        "classification": "stage_d2_transfer_package_prepared_not_executed",
        "purpose": "D2A state ingestion input package; not a solver result",
        "source_mesh": {"nx": 3, "ny": 3, "nodes": len(source_nodes), "elements": len(source_elements)},
        "target_mesh": {
            "nx": 4,
            "ny": 2,
            "x_shift": 0.041,
            "y_shift": -0.033,
            "nodes": len(target_nodes),
            "elements": len(target_elements),
        },
        "fields": {
            "d_source": "0.2 + 0.6 exp(-((x-x0)^2 + (y-y0)^2)/r^2)",
            "H_source": "max(H_old, psi0)",
        },
        "transfer": {
            "d": "node IDW k=4, then bound to [0,1]",
            "H": "element-centroid/IP IDW k=4, then max(raw,H_old)",
            "label_reuse": "not used as a mapping rule",
        },
        "energy": energy,
        "required_next_outputs": [
            "D2A_STATE_INGESTION_STATUS.json",
            "D2A_TRANSFERRED_VS_ODB.csv",
            "D2A_STATE_ROUTING_REPORT.md",
            "D2A.ok only after Abaqus/ODB verification passes",
        ],
    }
    write_json(out_dir / "transfer_provenance.json", provenance)
    write_json(
        out_dir / "D2A_STATE_INGESTION_STATUS.json",
        {
            "classification": "stage_d2a_not_executed_package_prepared",
            "D2A_ok": False,
            "reason": "Abaqus/UEL/ABAQUSER ingestion job not run yet",
            "package": str(out_dir.as_posix()),
            "required_before_ok": provenance["required_next_outputs"],
        },
    )
    (out_dir / "D2A_STATE_ROUTING_REPORT.md").write_text(
        "# D2A state routing package\n\n"
        "Classification: `stage_d2a_not_executed_package_prepared`\n\n"
        "This package contains transferred nodal `d`, transferred integration-point `H`, "
        "raw values, bounded values, source-to-target support, and provenance. It does "
        "not claim state ingestion into Abaqus/UEL/UMAT yet.\n\n"
        "## Required D2A verification\n\n"
        "- target `d` equals transfer CSV within extraction tolerance;\n"
        "- target `H` equals transfer CSV within extraction tolerance;\n"
        "- `0 <= d <= 1`;\n"
        "- `H` does not decrease;\n"
        "- no default/uniform overwrite of transferred fields;\n"
        "- all element/IP indices map correctly;\n"
        "- ABAQUSER/SDV output agrees with independent extraction.\n",
        encoding="utf-8",
        newline="\n",
    )
    (out_dir / "D2A_TARGET_INPUT_PACKAGE.inp").write_text(
        "** Stage D2A tiny target package scaffold\n"
        "** This is an ingestion scaffold, not a completed solver deck.\n"
        "** Consume target_transferred_nodal_d.csv and target_transferred_ip_H.csv\n"
        "** through the selected UEL/UMAT initialization route, then compare ODB output\n"
        "** against D2A_TRANSFERRED_VS_ODB.csv before writing D2A.ok.\n",
        encoding="utf-8",
        newline="\n",
    )
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("models/state_transfer/d2_tiny_transfer"))
    args = parser.parse_args()
    provenance = build_package(args.out_dir)
    print(json.dumps({"classification": provenance["classification"], "out_dir": str(args.out_dir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
