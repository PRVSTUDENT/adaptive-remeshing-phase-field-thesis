#!/usr/bin/env python3
"""Validate the D3A2 nonmatching transfer package before any solver job."""

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


EXPECTED_ELEMENTS_MIN = 5000
EXPECTED_ELEMENTS_MAX = 8000
WEIGHT_TOL = 1.0e-10


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def weight_sum_failures(rows: Iterable[Dict[str, str]], key_fields: Tuple[str, ...]) -> List[str]:
    sums: dict[Tuple[str, ...], float] = defaultdict(float)
    for row in rows:
        key = tuple(row[field] for field in key_fields)
        sums[key] += float(row["weight"])
    return [
        f"{'/'.join(key)} weight sum {value}"
        for key, value in sums.items()
        if abs(value - 1.0) > WEIGHT_TOL
    ]


def duplicate_failures(rows: Iterable[Dict[str, str]], key_fields: Tuple[str, ...], label: str) -> List[str]:
    counts = Counter(tuple(row[field] for field in key_fields) for row in rows)
    return [f"duplicate {label} key {'/'.join(key)}" for key, count in counts.items() if count > 1]


def validate(package_dir: Path) -> Dict[str, object]:
    failures: List[str] = []
    required = [
        "D3_TARGET_MESH_VALIDATION.json",
        "D3_TRANSFER_PROVENANCE.json",
        "D3_NODE_SUPPORT_MAP.csv",
        "D3_IP_SUPPORT_MAP.csv",
        "D3_TRANSFERRED_NODAL_D.csv",
        "D3_TRANSFERRED_IP_H.csv",
        "D3_TRANSFER_ERROR_METRICS.json",
        "D3_TARGET_NOTCH_TOPOLOGY.json",
        "D3_TARGET_NOTCH_NODE_PAIRS.csv",
        "D3_TARGET_NOTCH_CROSSING_ELEMENTS.csv",
        "D3_SOURCE_ENERGY.json",
        "D3_TARGET_PREDICTED_ENERGY.json",
        "D3_PREDICTED_ENERGY_JUMP.json",
        "D3_TRANSFER_PACKAGE_REPORT.md",
    ]
    for name in required:
        if not (package_dir / name).exists():
            failures.append(f"missing required package file {name}")
    if failures:
        status = {"classification": "stage_d3a2_transfer_package_fail", "D3_package_ok": False, "failures": failures}
        (package_dir / "D3_TRANSFER_PACKAGE_STATUS.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(status, indent=2, sort_keys=True))
        return status

    mesh = json.loads((package_dir / "D3_TARGET_MESH_VALIDATION.json").read_text(encoding="utf-8"))
    topology = json.loads((package_dir / "D3_TARGET_NOTCH_TOPOLOGY.json").read_text(encoding="utf-8"))
    provenance = json.loads((package_dir / "D3_TRANSFER_PROVENANCE.json").read_text(encoding="utf-8"))
    errors = json.loads((package_dir / "D3_TRANSFER_ERROR_METRICS.json").read_text(encoding="utf-8"))
    source_energy = json.loads((package_dir / "D3_SOURCE_ENERGY.json").read_text(encoding="utf-8"))
    target_energy = json.loads((package_dir / "D3_TARGET_PREDICTED_ENERGY.json").read_text(encoding="utf-8"))
    jump = json.loads((package_dir / "D3_PREDICTED_ENERGY_JUMP.json").read_text(encoding="utf-8"))
    node_support = read_csv(package_dir / "D3_NODE_SUPPORT_MAP.csv")
    ip_support = read_csv(package_dir / "D3_IP_SUPPORT_MAP.csv")
    nodal_d = read_csv(package_dir / "D3_TRANSFERRED_NODAL_D.csv")
    ip_h = read_csv(package_dir / "D3_TRANSFERRED_IP_H.csv")

    if provenance.get("solver_job_submitted") is not False:
        failures.append("provenance does not explicitly prohibit solver submission")
    if mesh.get("classification") != "stage_d3a2_target_mesh_validation_pass":
        failures.append(f"target mesh validation did not pass: {mesh.get('classification')}")
    if topology.get("classification") != "stage_d3a2_target_notch_topology_pass":
        failures.append(f"target notch topology validation did not pass: {topology.get('classification')}")
    element_count = int(mesh.get("physical_elements", 0))
    ip_count = len(ip_h)
    node_count = len(nodal_d)
    if element_count < EXPECTED_ELEMENTS_MIN or element_count > EXPECTED_ELEMENTS_MAX:
        failures.append(f"target element count outside preferred range: {element_count}")
    if ip_count != element_count * 4:
        failures.append(f"target IP coverage incomplete: {ip_count} rows for {element_count} elements")
    if len({row["node"] for row in nodal_d}) != node_count:
        failures.append("duplicate target-node keys")
    failures.extend(duplicate_failures(ip_h, ("element", "integration_point"), "target element/IP"))

    if len({row["target_node"] for row in node_support}) != node_count:
        failures.append("target-node support coverage is not 100%")
    if len({(row["target_element"], row["target_integration_point"]) for row in ip_support}) != ip_count:
        failures.append("target element/IP support coverage is not 100%")
    for label, rows in [("node support", node_support), ("IP support", ip_support)]:
        for row in rows:
            if not finite(row.get("weight")) or not finite(row.get("distance")):
                failures.append(f"{label} contains non-finite weight/distance")
                break
            weight = float(row["weight"])
            if weight < -1.0e-14 or weight > 1.0 + 1.0e-14:
                failures.append(f"{label} weight out of bounds: {weight}")
                break
    failures.extend(weight_sum_failures(node_support, ("target_node",))[:10])
    failures.extend(weight_sum_failures(ip_support, ("target_element", "target_integration_point"))[:10])

    for row in nodal_d:
        if not finite(row.get("d")):
            failures.append("transferred nodal d contains a non-finite value")
            break
        d = float(row["d"])
        if d < -1.0e-12 or d > 1.0 + 1.0e-12:
            failures.append(f"transferred nodal d out of bounds: {d}")
            break
    for row in ip_h:
        for name in ["H", "detJ", "jacobian_weight"]:
            if not finite(row.get(name)):
                failures.append(f"transferred IP {name} contains a non-finite value")
                break
        h = float(row["H"])
        detj = float(row["detJ"])
        if h < -1.0e-12:
            failures.append(f"transferred H is negative: {h}")
            break
        if detj <= 0.0:
            failures.append(f"target detJ is non-positive: {detj}")
            break

    if errors.get("no_silent_clipping") is not True:
        failures.append("package does not declare no_silent_clipping")
    for obj_name, obj in [
        ("source energy", source_energy),
        ("target predicted energy", target_energy),
        ("predicted energy jump", jump),
    ]:
        for key, value in obj.items():
            if isinstance(value, (int, float)) and not math.isfinite(float(value)):
                failures.append(f"{obj_name} {key} is not finite")
    if float(target_energy.get("fracture_energy_local_term", -1.0)) < -1.0e-14:
        failures.append("target local fracture energy is negative")
    if float(target_energy.get("fracture_energy_gradient_term", -1.0)) < -1.0e-14:
        failures.append("target gradient fracture energy is negative")
    if float(target_energy.get("total_fracture_energy", -1.0)) < -1.0e-14:
        failures.append("target total fracture energy is negative")

    status = {
        "classification": "stage_d3a2_transfer_package_pass" if not failures else "stage_d3a2_transfer_package_fail",
        "D3_package_ok": not failures,
        "solver_job_submitted": False,
        "target_node_coverage": len({row["target_node"] for row in node_support}) / max(node_count, 1),
        "target_ip_coverage": len({(row["target_element"], row["target_integration_point"]) for row in ip_support}) / max(ip_count, 1),
        "target_nodes": node_count,
        "target_elements": element_count,
        "target_integration_points": ip_count,
        "minimum_detJ": mesh.get("minimum_detJ"),
        "maximum_detJ": mesh.get("maximum_detJ"),
        "non_positive_detJ_count": mesh.get("non_positive_detJ_count"),
        "notch_topology_classification": topology.get("classification"),
        "notch_length": topology.get("notch_length"),
        "duplicated_open_face_node_pairs": topology.get("duplicated_open_face_node_pairs"),
        "notch_crossing_element_count": topology.get("crossing_element_count"),
        "source_self_SDV15_L2_error": errors.get("source_self_SDV15_L2_error"),
        "source_self_SDV15_max_error": errors.get("source_self_SDV15_max_error"),
        "source_self_SDV16_L2_error": errors.get("source_self_SDV16_L2_error"),
        "source_self_SDV16_max_error": errors.get("source_self_SDV16_max_error"),
        "predicted_energy_relative_jump": jump.get("relative_jump"),
        "unmapped_state_count": 0 if not failures else None,
        "failures": failures,
    }
    (package_dir / "D3_TRANSFER_PACKAGE_STATUS.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not failures:
        (package_dir / "D3_PACKAGE.ok").write_text(
            "\n".join([
                "classification=stage_d3a2_transfer_package_pass",
                "source_job=1376154.mmaster02",
                "checkpoint_U2=0.003000000026077032",
                "solver_job_submitted=false",
                "",
            ]),
            encoding="utf-8",
        )
    print(json.dumps(status, indent=2, sort_keys=True))
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/package"))
    args = parser.parse_args()
    status = validate(args.package_dir)
    return 0 if status["D3_package_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
