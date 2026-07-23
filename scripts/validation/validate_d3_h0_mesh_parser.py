#!/usr/bin/env python3
"""Validate scope-aware H0 mesh parsing for D3A energy reconstruction."""

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.reconstruct_d3_checkpoint_energy import (  # noqa: E402
    GAUSS,
    IP_COUNT,
    PHYSICAL_ELEMENTS,
    THICKNESS,
    jacobian,
    parse_h0_inp_scoped,
    shape,
)


EXPECTED_IP_COUNT = PHYSICAL_ELEMENTS * IP_COUNT


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, fields: List[str], rows: Iterable[Dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def close_pair(actual: object, expected: object, tol: float = 1.0e-14) -> bool:
    if actual is None:
        return False
    ax, ay = actual  # type: ignore[misc]
    ex, ey = expected  # type: ignore[misc]
    return abs(ax - ex) <= tol and abs(ay - ey) <= tol


def validate(input_deck: Path, out_dir: Path) -> Dict[str, object]:
    ensure_dir(out_dir)
    mesh = parse_h0_inp_scoped(input_deck)
    failures: List[str] = []

    if not close_pair(mesh.part_nodes.get(1), (0.5, 0.0)):
        failures.append(f"Part-1 node 1 is {mesh.part_nodes.get(1)}, expected (0.5, 0.0)")
    if not close_pair(mesh.assembly_nodes.get(1), (0.5, 0.5)):
        failures.append(f"Assembly node 1 is {mesh.assembly_nodes.get(1)}, expected (0.5, 0.5)")
    if 1 not in mesh.part_nodes or 1 not in mesh.assembly_nodes:
        failures.append("node label 1 is not present in both part and assembly namespaces")
    if mesh.u1_elements.get(345) != (171, 1, 9, 450):
        failures.append(f"element 345 connectivity is {mesh.u1_elements.get(345)}")
    if mesh.u1_elements.get(2240) != (172, 2225, 9, 1):
        failures.append(f"element 2240 connectivity is {mesh.u1_elements.get(2240)}")
    if len(mesh.u1_elements) != PHYSICAL_ELEMENTS:
        failures.append(f"physical element count is {len(mesh.u1_elements)}, expected {PHYSICAL_ELEMENTS}")
    if mesh.duplicate_part_node_labels:
        failures.append(f"duplicate Part-1 node labels: {mesh.duplicate_part_node_labels[:10]}")
    if mesh.missing_connectivity_nodes:
        failures.append(f"missing connectivity nodes: {mesh.missing_connectivity_nodes[:10]}")

    jacobian_rows: List[Dict[str, object]] = []
    detj_values: List[tuple[float, int, int]] = []
    for element, conn in sorted(mesh.u1_elements.items()):
        coords = [mesh.part_nodes[node] for node in conn]
        for ip in range(1, IP_COUNT + 1):
            xi, eta, weight = GAUSS[ip]
            _, dndxi = shape(xi, eta)
            detj, _ = jacobian(coords, dndxi)
            detj_values.append((detj, element, ip))
            jacobian_rows.append(
                {
                    "element": element,
                    "integration_point": ip,
                    "node1": conn[0],
                    "node2": conn[1],
                    "node3": conn[2],
                    "node4": conn[3],
                    "gauss_xi": xi,
                    "gauss_eta": eta,
                    "gauss_weight": weight,
                    "detJ": detj,
                    "jacobian_weight": detj * weight * THICKNESS,
                    "positive": detj > 0.0,
                }
            )

    non_positive = [(detj, element, ip) for detj, element, ip in detj_values if detj <= 0.0]
    min_detj, min_element, min_ip = min(detj_values)
    max_detj, max_element, max_ip = max(detj_values)

    if len(jacobian_rows) != EXPECTED_IP_COUNT:
        failures.append(f"quadrature-point count is {len(jacobian_rows)}, expected {EXPECTED_IP_COUNT}")
    if non_positive:
        failures.append(f"non-positive determinant count is {len(non_positive)}, expected 0")
    if not math.isfinite(min_detj) or not math.isfinite(max_detj):
        failures.append("detJ extrema are not finite")

    audit = {
        "classification": (
            "stage_d3a_h0_mesh_parser_scope_pass"
            if not failures
            else "stage_d3a_h0_mesh_parser_scope_fail"
        ),
        "input_deck": str(input_deck),
        "part_name": "Part-1",
        "part_node_count": len(mesh.part_nodes),
        "assembly_node_count": len(mesh.assembly_nodes),
        "part_node_1": mesh.part_nodes.get(1),
        "assembly_node_1": mesh.assembly_nodes.get(1),
        "node_1_namespaces_separate": 1 in mesh.part_nodes and 1 in mesh.assembly_nodes,
        "element_345_connectivity": mesh.u1_elements.get(345),
        "element_2240_connectivity": mesh.u1_elements.get(2240),
        "physical_element_count": len(mesh.u1_elements),
        "quadrature_point_count": len(jacobian_rows),
        "non_positive_determinant_count": len(non_positive),
        "minimum_detJ": min_detj,
        "minimum_detJ_element": min_element,
        "minimum_detJ_integration_point": min_ip,
        "maximum_detJ": max_detj,
        "maximum_detJ_element": max_element,
        "maximum_detJ_integration_point": max_ip,
        "duplicate_labels_across_scopes": mesh.duplicate_labels_across_scopes,
        "duplicate_part_node_labels": mesh.duplicate_part_node_labels,
        "duplicate_assembly_node_labels": mesh.duplicate_assembly_node_labels,
        "missing_connectivity_nodes": mesh.missing_connectivity_nodes,
        "failures": failures,
    }
    (out_dir / "D3A_MESH_NAMESPACE_AUDIT.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(
        out_dir / "D3A_JACOBIAN_AUDIT.csv",
        [
            "element",
            "integration_point",
            "node1",
            "node2",
            "node3",
            "node4",
            "gauss_xi",
            "gauss_eta",
            "gauss_weight",
            "detJ",
            "jacobian_weight",
            "positive",
        ],
        jacobian_rows,
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-deck", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    audit = validate(args.input_deck, args.out_dir)
    return 0 if not audit["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
