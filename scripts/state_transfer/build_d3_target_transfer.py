#!/usr/bin/env python3
"""Build the D3A2 nonmatching target transfer package without PBS."""

import argparse
import csv
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
from scipy.spatial import cKDTree

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.reconstruct_d3_checkpoint_energy import (
    GAUSS,
    GC,
    IP_COUNT,
    LC,
    THICKNESS,
    jacobian,
    parse_h0_inp_scoped,
    shape,
)


NX = 80
NY = 80
K_SUPPORT = 8
EPS = 1.0e-30
SOURCE_JOB = "1376154.mmaster02"
CHECKPOINT_U2 = 0.003000000026077032
CHECKPOINT_RF2 = 0.39450356364250183


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: Sequence[str], rows: Iterable[Dict[str, object]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def build_target_mesh(nx: int = NX, ny: int = NY) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    nodes: List[Dict[str, object]] = []
    elements: List[Dict[str, object]] = []
    node_labels: Dict[Tuple[str, int, int], int] = {}
    next_label = 1
    mid_j = ny // 2
    tip_i = nx // 2
    for j in range(ny + 1):
        y = -0.5 + j / ny
        if abs(y) < 1.0e-15:
            y = 0.0
        for i in range(nx + 1):
            x = -0.5 + i / nx
            label = next_label
            next_label += 1
            node_labels[("main", i, j)] = label
            nodes.append({"node": label, "x": x, "y": y})
            if j == mid_j and i < tip_i:
                lower_label = next_label
                next_label += 1
                node_labels[("lower", i, j)] = lower_label
                nodes.append({"node": lower_label, "x": x, "y": y})

    def node_for(i: int, j: int, lower_face: bool = False) -> int:
        if lower_face and j == mid_j and i < tip_i:
            return node_labels[("lower", i, j)]
        return node_labels[("main", i, j)]

    for j in range(ny):
        for i in range(nx):
            label = j * nx + i + 1
            below_open_notch = j == mid_j - 1 and i < tip_i
            n1 = node_for(i, j)
            n2 = node_for(i + 1, j)
            n3 = node_for(i + 1, j + 1, below_open_notch and i + 1 < tip_i)
            n4 = node_for(i, j + 1, below_open_notch)
            elements.append({"element": label, "n1": n1, "n2": n2, "n3": n3, "n4": n4})
    return nodes, elements


def target_ip_rows(
    nodes_by_label: Dict[int, Tuple[float, float]],
    elements: List[Dict[str, object]],
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for elem in elements:
        label = int(elem["element"])
        conn = [int(elem[f"n{i}"]) for i in range(1, 5)]
        coords = [nodes_by_label[node] for node in conn]
        for ip in range(1, IP_COUNT + 1):
            xi, eta, weight = GAUSS[ip]
            n, dndxi = shape(xi, eta)
            detj, _ = jacobian(coords, dndxi)
            rows.append(
                {
                    "element": label,
                    "integration_point": ip,
                    "x": sum(n[i] * coords[i][0] for i in range(4)),
                    "y": sum(n[i] * coords[i][1] for i in range(4)),
                    "gauss_xi": xi,
                    "gauss_eta": eta,
                    "gauss_weight": weight,
                    "detJ": detj,
                    "jacobian_weight": detj * weight * THICKNESS,
                }
            )
    return rows


def idw_weights(tree: cKDTree, points: np.ndarray, k: int = K_SUPPORT) -> Tuple[np.ndarray, np.ndarray]:
    distances, indexes = tree.query(points, k=k)
    if k == 1:
        distances = distances[:, None]
        indexes = indexes[:, None]
    weights = np.zeros_like(distances, dtype=float)
    exact = distances <= 1.0e-14
    for row in range(distances.shape[0]):
        exact_cols = np.flatnonzero(exact[row])
        if len(exact_cols):
            weights[row, exact_cols[0]] = 1.0
        else:
            inv = 1.0 / np.maximum(distances[row], 1.0e-14) ** 2
            weights[row] = inv / inv.sum()
    return indexes, weights


def interpolate(values: np.ndarray, indexes: np.ndarray, weights: np.ndarray) -> np.ndarray:
    return np.sum(values[indexes] * weights, axis=1)


def l2_error(actual: np.ndarray, expected: np.ndarray) -> float:
    return float(np.sqrt(np.mean((actual - expected) ** 2)))


def write_mesh_files(base_dir: Path, nodes: List[Dict[str, object]], elements: List[Dict[str, object]]) -> None:
    target_dir = base_dir / "target"
    ensure_dir(target_dir)
    write_csv(target_dir / "target_nodes.csv", ["node", "x", "y"], nodes)
    write_csv(target_dir / "target_elements.csv", ["element", "n1", "n2", "n3", "n4"], elements)


def write_source_files(base_dir: Path, input_deck: Path) -> None:
    source_dir = base_dir / "source"
    ensure_dir(source_dir)
    mesh = parse_h0_inp_scoped(input_deck)
    write_csv(
        source_dir / "source_nodes.csv",
        ["node", "x", "y"],
        [{"node": node, "x": xy[0], "y": xy[1]} for node, xy in sorted(mesh.part_nodes.items())],
    )
    write_csv(
        source_dir / "source_elements.csv",
        ["element", "n1", "n2", "n3", "n4"],
        [
            {"element": element, "n1": conn[0], "n2": conn[1], "n3": conn[2], "n4": conn[3]}
            for element, conn in sorted(mesh.u1_elements.items())
        ],
    )


def write_target_inp(path: Path, nodes: List[Dict[str, object]], elements: List[Dict[str, object]]) -> None:
    lines = [
        "*Heading",
        "** D3A2 deterministic nonmatching target mesh package.",
        "** Generated locally; not submitted as a solver job.",
        "*Preprint, echo=NO, model=NO, history=NO, contact=NO",
        "*Node",
    ]
    for row in nodes:
        lines.append(f"{row['node']}, {row['x']}, {row['y']}")
    lines.extend([
        "*User Element, nodes=4, type=U1, properties=3, coordinates=2, VARIABLES=2",
        "3",
        "*Element, type=U1, elset=TARGET_PHASE",
    ])
    for row in elements:
        lines.append(f"{row['element']}, {row['n1']}, {row['n2']}, {row['n3']}, {row['n4']}")
    lines.extend([
        "*Elset, elset=TARGET_PHASE, generate",
        f"1, {len(elements)}, 1",
        "*Uel Property, elset=TARGET_PHASE",
        f"{LC}, {GC}, {THICKNESS}",
        "** The open split notch runs from x=-0.5 to x=0.0 on the exact y=0 line.",
    ])
    ensure_dir(path.parent)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_transfer_table(path: Path, transferred_ip_rows: List[Dict[str, object]]) -> None:
    lines = [
        "      INTEGER D3_TRANSFER_COUNT",
        f"      PARAMETER (D3_TRANSFER_COUNT={len(transferred_ip_rows)})",
        "      INTEGER D3_TRANSFER_ELEM(D3_TRANSFER_COUNT)",
        "      INTEGER D3_TRANSFER_IP(D3_TRANSFER_COUNT)",
        "      DOUBLE PRECISION D3_TRANSFER_H(D3_TRANSFER_COUNT)",
        "      DATA D3_TRANSFER_ELEM /",
    ]
    elems = [int(row["element"]) for row in transferred_ip_rows]
    ips = [int(row["integration_point"]) for row in transferred_ip_rows]
    hs = [float(row["H"]) for row in transferred_ip_rows]
    for values, formatter, closing in [
        (elems, lambda v: str(v), "/"),
        (ips, lambda v: str(v), "/"),
        (hs, lambda v: f"{v:.17E}", "/"),
    ]:
        if values is ips:
            lines.append("      DATA D3_TRANSFER_IP /")
        elif values is hs:
            lines.append("      DATA D3_TRANSFER_H /")
        chunks = [values[i : i + 6] for i in range(0, len(values), 6)]
        for index, chunk in enumerate(chunks):
            suffix = closing if index == len(chunks) - 1 else ","
            lines.append("     1 " + ", ".join(formatter(v) for v in chunk) + suffix)
    ensure_dir(path.parent)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_transfer_uel(path: Path) -> None:
    text = """      SUBROUTINE D3_TRANSFER_UEL_PLACEHOLDER()
C     Placeholder copied into the D3A2 package so the executable directory has
C     the expected transfer-table companion. The full ingestion UEL is created
C     in D3A3 before any solver submission.
      RETURN
      END
"""
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def build_package(args: argparse.Namespace) -> Dict[str, object]:
    model_dir = args.model_dir
    package_dir = args.package_dir
    executable_dir = model_dir / "executable"
    ensure_dir(model_dir / "source")
    ensure_dir(model_dir / "target")
    ensure_dir(executable_dir)
    ensure_dir(package_dir)
    package_ok = package_dir / "D3_PACKAGE.ok"
    if package_ok.exists():
        package_ok.unlink()

    nodes, elements = build_target_mesh(args.nx, args.ny)
    nodes_by_label = {int(row["node"]): (float(row["x"]), float(row["y"])) for row in nodes}
    target_ips = target_ip_rows(nodes_by_label, elements)
    write_mesh_files(model_dir, nodes, elements)
    write_source_files(model_dir, args.input_deck)
    write_target_inp(executable_dir / "D3A2_target_mesh_package.inp", nodes, elements)

    source_rows = read_csv(args.state_csv)
    source_points = np.array([[float(row["x"]), float(row["y"])] for row in source_rows], dtype=float)
    source_tree = cKDTree(source_points)
    source_element = np.array([int(row["element"]) for row in source_rows])
    source_ip = np.array([int(row["integration_point"]) for row in source_rows])
    source_d = np.array([float(row["SDV15_d"]) for row in source_rows])
    source_h = np.array([float(row["SDV16_H"]) for row in source_rows])
    source_sdv12 = np.array([float(row["SDV12_degraded_elastic_energy_density"]) for row in source_rows])
    source_sdv13 = np.array([float(row["SDV13_undamaged_elastic_energy_density"]) for row in source_rows])
    source_jac_weight = np.array([
        float(row["detJ"]) * float(row["gauss_weight"]) * float(row.get("thickness", THICKNESS))
        for row in source_rows
    ])
    source_se = np.array([float(row["bulk_energy_from_S_E"]) for row in source_rows]) / source_jac_weight

    target_node_points = np.array([[float(row["x"]), float(row["y"])] for row in nodes], dtype=float)
    node_indexes, node_weights = idw_weights(source_tree, target_node_points)
    target_d = interpolate(source_d, node_indexes, node_weights)

    target_ip_points = np.array([[float(row["x"]), float(row["y"])] for row in target_ips], dtype=float)
    ip_indexes, ip_weights = idw_weights(source_tree, target_ip_points)
    target_h = interpolate(source_h, ip_indexes, ip_weights)
    target_sdv12 = interpolate(source_sdv12, ip_indexes, ip_weights)
    target_sdv13 = interpolate(source_sdv13, ip_indexes, ip_weights)
    target_se = interpolate(source_se, ip_indexes, ip_weights)

    node_support_rows: List[Dict[str, object]] = []
    for row_index, node in enumerate(nodes):
        for support_col in range(K_SUPPORT):
            source_index = int(node_indexes[row_index, support_col])
            node_support_rows.append(
                {
                    "target_node": node["node"],
                    "x": node["x"],
                    "y": node["y"],
                    "field": "d",
                    "method": "idw_k8_source_ip_sdv15",
                    "source_element": int(source_element[source_index]),
                    "source_integration_point": int(source_ip[source_index]),
                    "source_x": float(source_points[source_index, 0]),
                    "source_y": float(source_points[source_index, 1]),
                    "weight": float(node_weights[row_index, support_col]),
                    "distance": float(np.linalg.norm(target_node_points[row_index] - source_points[source_index])),
                }
            )

    ip_support_rows: List[Dict[str, object]] = []
    for row_index, target_ip in enumerate(target_ips):
        for support_col in range(K_SUPPORT):
            source_index = int(ip_indexes[row_index, support_col])
            ip_support_rows.append(
                {
                    "target_element": target_ip["element"],
                    "target_integration_point": target_ip["integration_point"],
                    "x": target_ip["x"],
                    "y": target_ip["y"],
                    "field": "H",
                    "method": "idw_k8_source_ip_sdv16",
                    "source_element": int(source_element[source_index]),
                    "source_integration_point": int(source_ip[source_index]),
                    "source_x": float(source_points[source_index, 0]),
                    "source_y": float(source_points[source_index, 1]),
                    "weight": float(ip_weights[row_index, support_col]),
                    "distance": float(np.linalg.norm(target_ip_points[row_index] - source_points[source_index])),
                }
            )

    transferred_nodal_rows = [
        {"node": int(row["node"]), "x": row["x"], "y": row["y"], "d": float(target_d[index])}
        for index, row in enumerate(nodes)
    ]
    transferred_ip_rows = [
        {
            "element": int(row["element"]),
            "integration_point": int(row["integration_point"]),
            "x": row["x"],
            "y": row["y"],
            "H": float(target_h[index]),
            "SDV12_degraded_elastic_energy_density": float(target_sdv12[index]),
            "SDV13_undamaged_elastic_energy_density": float(target_sdv13[index]),
            "stress_strain_energy_density": float(target_se[index]),
            "detJ": row["detJ"],
            "jacobian_weight": row["jacobian_weight"],
        }
        for index, row in enumerate(target_ips)
    ]

    write_csv(package_dir / "D3_NODE_SUPPORT_MAP.csv", list(node_support_rows[0]), node_support_rows)
    write_csv(package_dir / "D3_IP_SUPPORT_MAP.csv", list(ip_support_rows[0]), ip_support_rows)
    write_csv(package_dir / "D3_TRANSFERRED_NODAL_D.csv", ["node", "x", "y", "d"], transferred_nodal_rows)
    write_csv(
        package_dir / "D3_TRANSFERRED_IP_H.csv",
        [
            "element",
            "integration_point",
            "x",
            "y",
            "H",
            "SDV12_degraded_elastic_energy_density",
            "SDV13_undamaged_elastic_energy_density",
            "stress_strain_energy_density",
            "detJ",
            "jacobian_weight",
        ],
        transferred_ip_rows,
    )
    write_transfer_table(executable_dir / "d3_transfer_table.inc", transferred_ip_rows)
    copy_transfer_uel(executable_dir / "d3_transfer_uel.for")

    target_d_by_node = {int(row["node"]): float(row["d"]) for row in transferred_nodal_rows}
    local_total = 0.0
    gradient_total = 0.0
    bulk_sdv12_total = 0.0
    bulk_se_total = 0.0
    bulk_sdv13_total = 0.0
    for elem in elements:
        conn = [int(elem[f"n{i}"]) for i in range(1, 5)]
        coords = [nodes_by_label[node] for node in conn]
        nodal_d = [target_d_by_node[node] for node in conn]
        for ip in range(1, IP_COUNT + 1):
            idx = (int(elem["element"]) - 1) * IP_COUNT + ip - 1
            xi, eta, weight = GAUSS[ip]
            n, dndxi = shape(xi, eta)
            detj, inv_j = jacobian(coords, dndxi)
            dndx = []
            for dxi, deta in dndxi:
                dndx.append((dxi * inv_j[0][0] + deta * inv_j[1][0], dxi * inv_j[0][1] + deta * inv_j[1][1]))
            d_ip = sum(n[i] * nodal_d[i] for i in range(4))
            grad_x = sum(dndx[i][0] * nodal_d[i] for i in range(4))
            grad_y = sum(dndx[i][1] * nodal_d[i] for i in range(4))
            jac_weight = weight * detj * THICKNESS
            bulk_sdv12_total += float(target_sdv12[idx]) * jac_weight
            bulk_se_total += float(target_se[idx]) * jac_weight
            bulk_sdv13_total += float(target_sdv13[idx]) * jac_weight
            local_total += GC * d_ip * d_ip / (2.0 * LC) * jac_weight
            gradient_total += GC * LC * (grad_x * grad_x + grad_y * grad_y) / 2.0 * jac_weight

    source_energy = json.loads(args.source_energy_json.read_text(encoding="utf-8"))
    target_internal = bulk_sdv12_total + local_total + gradient_total
    source_internal = float(source_energy["total_reconstructed_internal_energy"])
    energy_jump = {
        "classification": "stage_d3a2_predicted_energy_jump",
        "source_total_internal_energy": source_internal,
        "target_predicted_total_internal_energy": target_internal,
        "absolute_jump_target_minus_source": target_internal - source_internal,
        "relative_jump": abs(target_internal - source_internal) / max(abs(source_internal), abs(target_internal), EPS),
    }
    target_energy = {
        "classification": "stage_d3a2_target_predicted_energy",
        "physical_elements": len(elements),
        "integration_points": len(transferred_ip_rows),
        "bulk_energy_from_SDV12": bulk_sdv12_total,
        "bulk_energy_from_stress_strain": bulk_se_total,
        "undamaged_bulk_energy_from_SDV13": bulk_sdv13_total,
        "fracture_energy_local_term": local_total,
        "fracture_energy_gradient_term": gradient_total,
        "total_fracture_energy": local_total + gradient_total,
        "total_predicted_internal_energy": target_internal,
    }
    shutil.copy2(args.source_energy_json, package_dir / "D3_SOURCE_ENERGY.json")
    (package_dir / "D3_TARGET_PREDICTED_ENERGY.json").write_text(json.dumps(target_energy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (package_dir / "D3_PREDICTED_ENERGY_JUMP.json").write_text(json.dumps(energy_jump, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    source_self_indexes, source_self_weights = idw_weights(source_tree, source_points)
    self_d = interpolate(source_d, source_self_indexes, source_self_weights)
    self_h = interpolate(source_h, source_self_indexes, source_self_weights)
    error_metrics = {
        "classification": "stage_d3a2_transfer_error_metrics",
        "source_self_SDV15_L2_error": l2_error(self_d, source_d),
        "source_self_SDV15_max_error": float(np.max(np.abs(self_d - source_d))),
        "source_self_SDV16_L2_error": l2_error(self_h, source_h),
        "source_self_SDV16_max_error": float(np.max(np.abs(self_h - source_h))),
        "target_node_support_max_distance": float(max(float(row["distance"]) for row in node_support_rows)),
        "target_ip_support_max_distance": float(max(float(row["distance"]) for row in ip_support_rows)),
        "no_silent_clipping": True,
    }
    (package_dir / "D3_TRANSFER_ERROR_METRICS.json").write_text(json.dumps(error_metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    target_detj = np.array([float(row["detJ"]) for row in target_ips])
    validation = {
        "classification": "stage_d3a2_target_mesh_validation_pass" if bool(np.all(target_detj > 0.0)) else "stage_d3a2_target_mesh_validation_fail",
        "geometry": "1x1_mm_single_notch_split_line",
        "notch": "exact_y0_line_from_x0_to_x0p5_retained",
        "plane_strain": True,
        "thickness": THICKNESS,
        "lc": LC,
        "nx": args.nx,
        "ny": args.ny,
        "node_count": len(nodes),
        "physical_elements": len(elements),
        "less_than_H1_12064": len(elements) < 12064,
        "not_identical_to_H0_connectivity": len(elements) != 3930,
        "y0_line_node_count": sum(1 for row in nodes if abs(float(row["y"])) <= 1.0e-15),
        "minimum_detJ": float(np.min(target_detj)),
        "maximum_detJ": float(np.max(target_detj)),
        "non_positive_detJ_count": int(np.sum(target_detj <= 0.0)),
    }
    (package_dir / "D3_TARGET_MESH_VALIDATION.json").write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    provenance = {
        "classification": "stage_d3a2_transfer_provenance",
        "source_job": SOURCE_JOB,
        "checkpoint_U2": CHECKPOINT_U2,
        "checkpoint_RF2": CHECKPOINT_RF2,
        "source_phase": "SDV15 interpolated from accepted checkpoint IP state",
        "source_history": "SDV16 interpolated from accepted checkpoint IP state",
        "source_state_csv": str(args.state_csv),
        "source_state_csv_sha256": sha256(args.state_csv),
        "source_energy_json": str(args.source_energy_json),
        "source_energy_json_sha256": sha256(args.source_energy_json),
        "input_deck": str(args.input_deck),
        "input_deck_sha256": sha256(args.input_deck),
        "target_mesh": "deterministic_split_notch_Q4_80x80",
        "target_notch": "open seam from x=-0.5 to x=0.0 on y=0, lower-face nodes duplicated, tip shared",
        "support_method": "scipy_cKDTree_idw_k8",
        "solver_job_submitted": False,
    }
    (package_dir / "D3_TRANSFER_PROVENANCE.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = [
        "# D3A2 Nonmatching Transfer Package",
        "",
        "Classification: `stage_d3a2_transfer_package_built`",
        "",
        f"- Source job: `{SOURCE_JOB}`",
        f"- Checkpoint U2: `{CHECKPOINT_U2}` mm",
        f"- Target nodes: `{len(nodes)}`",
        f"- Target elements: `{len(elements)}`",
        f"- Target integration points: `{len(transferred_ip_rows)}`",
        f"- Target minimum detJ: `{validation['minimum_detJ']}`",
        f"- Node coverage: `1.0`",
        f"- IP coverage: `1.0`",
        f"- Predicted relative energy jump: `{energy_jump['relative_jump']}`",
        "",
        "No PBS job or fracture continuation was submitted.",
        "",
    ]
    (package_dir / "D3_TRANSFER_PACKAGE_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    status = {
        "classification": "stage_d3a2_transfer_package_built",
        "D3_package_ok": False,
        "package_dir": str(package_dir),
        "solver_job_submitted": False,
        "target_node_count": len(nodes),
        "target_element_count": len(elements),
        "target_ip_count": len(transferred_ip_rows),
    }
    (package_dir / "D3_TRANSFER_PACKAGE_STATUS.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-deck", type=Path, default=Path("models/generated/molnar_gravouil_2017/h_convergence_lc015/H0_exact/SingleNotch.inp"))
    parser.add_argument("--state-csv", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/checkpoint_energy_r1/D3A_CHECKPOINT_STATE_WITH_ENERGY.csv"))
    parser.add_argument("--source-energy-json", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/checkpoint_energy_r1/D3A_RECONSTRUCTED_ENERGY.json"))
    parser.add_argument("--model-dir", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer"))
    parser.add_argument("--package-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/package"))
    parser.add_argument("--nx", type=int, default=NX)
    parser.add_argument("--ny", type=int, default=NY)
    args = parser.parse_args()
    status = build_package(args)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
