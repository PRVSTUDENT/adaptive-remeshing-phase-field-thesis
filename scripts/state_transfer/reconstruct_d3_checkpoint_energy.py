#!/usr/bin/env python3
"""Reconstruct D3A checkpoint energy from exported ODB state and H0 mesh."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


PHYSICAL_ELEMENTS = 3930
IP_COUNT = 4
GC = 2.7e-3
LC = 0.015
THICKNESS = 1.0
EPS = 1.0e-30
GAUSS = {
    1: (-1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0), 1.0),
    2: (1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0), 1.0),
    3: (1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0), 1.0),
    4: (-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0), 1.0),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: List[str], rows: Iterable[Dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def f(row: Dict[str, str], name: str) -> float:
    return float(row[name])


def parse_h0_inp(path: Path) -> Tuple[Dict[int, Tuple[float, float]], Dict[int, Tuple[int, int, int, int]]]:
    nodes: Dict[int, Tuple[float, float]] = {}
    elems: Dict[int, Tuple[int, int, int, int]] = {}
    mode = None
    element_block = None
    with path.open(encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("**"):
                continue
            lower = line.lower()
            if lower.startswith("*node"):
                mode = "node"
                continue
            if lower.startswith("*element"):
                mode = "element"
                element_block = lower
                continue
            if line.startswith("*"):
                mode = None
                element_block = None
                continue
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if mode == "node" and len(parts) >= 3:
                label = int(parts[0])
                nodes[label] = (float(parts[1]), float(parts[2]))
            elif mode == "element" and element_block and "type=u1" in element_block and len(parts) >= 5:
                label = int(parts[0])
                if 1 <= label <= PHYSICAL_ELEMENTS:
                    elems[label] = tuple(int(p) for p in parts[1:5])  # type: ignore[assignment]
    return nodes, elems


def shape(xi: float, eta: float) -> Tuple[List[float], List[Tuple[float, float]]]:
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


def jacobian(coords: List[Tuple[float, float]], dndxi: List[Tuple[float, float]]) -> Tuple[float, List[List[float]]]:
    j11 = sum(coords[i][0] * dndxi[i][0] for i in range(4))
    j12 = sum(coords[i][0] * dndxi[i][1] for i in range(4))
    j21 = sum(coords[i][1] * dndxi[i][0] for i in range(4))
    j22 = sum(coords[i][1] * dndxi[i][1] for i in range(4))
    det = j11 * j22 - j12 * j21
    inv = [[j22 / det, -j12 / det], [-j21 / det, j11 / det]]
    return det, inv


def grad_shape(dndxi: List[Tuple[float, float]], inv_j: List[List[float]]) -> List[Tuple[float, float]]:
    out = []
    for dxi, deta in dndxi:
        dx = dxi * inv_j[0][0] + deta * inv_j[1][0]
        dy = dxi * inv_j[0][1] + deta * inv_j[1][1]
        out.append((dx, dy))
    return out


def integrate_external_work(rows: List[Dict[str, str]], checkpoint_total_time: float, checkpoint_u2: float) -> Tuple[List[Dict[str, object]], float, float, bool]:
    path_rows = []
    cumulative = 0.0
    previous = None
    monotonic = True
    selected = [
        r for r in rows
        if float(r["total_time"]) <= checkpoint_total_time + 1.0e-12
        and float(r["U2"]) <= checkpoint_u2 + 1.0e-10
    ]
    selected.sort(key=lambda r: (float(r["total_time"]), int(r["frame_index"])))
    for row in selected:
        u2 = float(row["U2"])
        rf2 = float(row["RF2"])
        increment = 0.0
        if previous is not None:
            du = u2 - previous[0]
            if du < -1.0e-12:
                monotonic = False
            increment = 0.5 * (rf2 + previous[1]) * du
            cumulative += increment
        path_rows.append({
            "step": row["step"],
            "frame_index": row["frame_index"],
            "frame_id": row["frame_id"],
            "total_time": row["total_time"],
            "U2": u2,
            "RF2": rf2,
            "incremental_signed_work": increment,
            "cumulative_signed_work": cumulative,
            "cumulative_absolute_loading_work": abs(cumulative),
        })
        previous = (u2, rf2)
    return path_rows, cumulative, abs(cumulative), monotonic


def reconstruct(args: argparse.Namespace) -> Dict[str, object]:
    ensure_dir(args.out_dir)
    nodes, elements = parse_h0_inp(args.input_deck)
    state_rows = read_csv(args.state_csv)
    nodal_rows = read_csv(args.nodal_d_csv)
    rf_u_rows = read_csv(args.rf_u_csv)
    selection = json.loads(args.selection_json.read_text(encoding="utf-8"))

    phase_by_node = {int(r["node"]): float(r["phase_d"]) for r in nodal_rows if r.get("phase_d", "") != ""}
    state_by_key = {(int(r["element"]), int(r["integration_point"])): r for r in state_rows}

    external_path, signed_work, abs_work, work_monotonic = integrate_external_work(
        rf_u_rows,
        float(selection["total_time"]),
        float(selection["actual_U2"]),
    )
    write_csv(
        args.out_dir / "D3A_EXTERNAL_WORK_PATH.csv",
        [
            "step",
            "frame_index",
            "frame_id",
            "total_time",
            "U2",
            "RF2",
            "incremental_signed_work",
            "cumulative_signed_work",
            "cumulative_absolute_loading_work",
        ],
        external_path,
    )

    element_bulk: Dict[int, Dict[str, float]] = {}
    element_frac: Dict[int, Dict[str, float]] = {}
    enriched_rows = []
    positive_jacobians = True

    for element, conn in sorted(elements.items()):
        coords = [nodes[n] for n in conn]
        nodal_d = [phase_by_node[n] for n in conn]
        bulk_sdv12 = 0.0
        bulk_sdv13 = 0.0
        bulk_se = 0.0
        frac_local = 0.0
        frac_gradient = 0.0
        for ip in range(1, IP_COUNT + 1):
            xi, eta, weight = GAUSS[ip]
            n, dndxi = shape(xi, eta)
            detj, inv_j = jacobian(coords, dndxi)
            if detj <= 0.0:
                positive_jacobians = False
            dndx = grad_shape(dndxi, inv_j)
            d_ip = sum(n[i] * nodal_d[i] for i in range(4))
            grad_x = sum(dndx[i][0] * nodal_d[i] for i in range(4))
            grad_y = sum(dndx[i][1] * nodal_d[i] for i in range(4))
            row = state_by_key[(element, ip)]
            sdv12 = f(row, "SDV12_degraded_elastic_energy_density")
            sdv13 = f(row, "SDV13_undamaged_elastic_energy_density")
            s11 = f(row, "SDV6_degraded_S11")
            s22 = f(row, "SDV7_degraded_S22")
            s12 = f(row, "SDV8_degraded_S12")
            e11 = f(row, "SDV3_E11")
            e22 = f(row, "SDV4_E22")
            e12 = f(row, "SDV5_E12")
            se_density = 0.5 * (s11 * e11 + s22 * e22 + s12 * e12)
            jac_weight = weight * detj * THICKNESS
            local_density = GC * d_ip * d_ip / (2.0 * LC)
            gradient_density = GC * LC * (grad_x * grad_x + grad_y * grad_y) / 2.0
            bulk_sdv12 += sdv12 * jac_weight
            bulk_sdv13 += sdv13 * jac_weight
            bulk_se += se_density * jac_weight
            frac_local += local_density * jac_weight
            frac_gradient += gradient_density * jac_weight
            enriched = dict(row)
            enriched.update({
                "gauss_xi": xi,
                "gauss_eta": eta,
                "gauss_weight": weight,
                "detJ": detj,
                "thickness": THICKNESS,
                "phase_d_from_nodes": d_ip,
                "grad_d_x": grad_x,
                "grad_d_y": grad_y,
                "bulk_energy_from_SDV12": sdv12 * jac_weight,
                "bulk_energy_from_S_E": se_density * jac_weight,
                "undamaged_bulk_energy_from_SDV13": sdv13 * jac_weight,
                "fracture_energy_local": local_density * jac_weight,
                "fracture_energy_gradient": gradient_density * jac_weight,
            })
            enriched_rows.append(enriched)
        element_bulk[element] = {
            "element": element,
            "bulk_energy_from_SDV12": bulk_sdv12,
            "bulk_energy_from_stress_strain": bulk_se,
            "undamaged_bulk_energy_from_SDV13": bulk_sdv13,
            "relative_sdv12_vs_stress_strain": abs(bulk_sdv12 - bulk_se) / max(abs(bulk_sdv12), abs(bulk_se), EPS),
        }
        element_frac[element] = {
            "element": element,
            "fracture_energy_local_term": frac_local,
            "fracture_energy_gradient_term": frac_gradient,
            "total_fracture_energy": frac_local + frac_gradient,
        }

    enriched_fields = list(state_rows[0].keys()) + [
        "phase_d_from_nodes",
        "grad_d_x",
        "grad_d_y",
        "bulk_energy_from_SDV12",
        "bulk_energy_from_S_E",
        "undamaged_bulk_energy_from_SDV13",
        "fracture_energy_local",
        "fracture_energy_gradient",
    ]
    write_csv(args.out_dir / "D3A_CHECKPOINT_STATE_WITH_ENERGY.csv", enriched_fields, enriched_rows)
    write_csv(
        args.out_dir / "D3A_ELEMENT_BULK_ENERGY.csv",
        ["element", "bulk_energy_from_SDV12", "bulk_energy_from_stress_strain", "undamaged_bulk_energy_from_SDV13", "relative_sdv12_vs_stress_strain"],
        element_bulk.values(),
    )
    write_csv(
        args.out_dir / "D3A_ELEMENT_FRACTURE_ENERGY.csv",
        ["element", "fracture_energy_local_term", "fracture_energy_gradient_term", "total_fracture_energy"],
        element_frac.values(),
    )

    bulk_sdv12_total = sum(v["bulk_energy_from_SDV12"] for v in element_bulk.values())
    bulk_se_total = sum(v["bulk_energy_from_stress_strain"] for v in element_bulk.values())
    bulk_sdv13_total = sum(v["undamaged_bulk_energy_from_SDV13"] for v in element_bulk.values())
    frac_local_total = sum(v["fracture_energy_local_term"] for v in element_frac.values())
    frac_gradient_total = sum(v["fracture_energy_gradient_term"] for v in element_frac.values())
    total_fracture = frac_local_total + frac_gradient_total
    total_internal = bulk_sdv12_total + total_fracture
    residual = signed_work - total_internal
    summary = {
        "classification": "stage_d3a_energy_reconstructed",
        "source_job": args.source_job_id,
        "checkpoint_U2": selection["actual_U2"],
        "checkpoint_RF2": selection["checkpoint_RF2"],
        "checkpoint_RF2_over_H0_peak_RF2": selection["checkpoint_RF2_over_H0_peak_RF2"],
        "max_d": selection.get("max_d"),
        "max_H": selection.get("max_H"),
        "ip_count_d_ge_0p1": selection.get("ip_count_d_ge_0p1"),
        "ip_count_d_ge_0p5": selection.get("ip_count_d_ge_0p5"),
        "physical_elements": len(elements),
        "integration_point_rows": len(state_rows),
        "nodal_phase_rows": len(nodal_rows),
        "ip_coverage": len(state_by_key) / float(PHYSICAL_ELEMENTS * IP_COUNT),
        "external_work": signed_work,
        "absolute_loading_work": abs_work,
        "external_work_path_nondecreasing": work_monotonic,
        "bulk_energy_from_SDV12": bulk_sdv12_total,
        "bulk_energy_from_stress_strain": bulk_se_total,
        "undamaged_bulk_energy_from_SDV13": bulk_sdv13_total,
        "bulk_sdv12_vs_stress_strain_relative_difference": abs(bulk_sdv12_total - bulk_se_total) / max(abs(bulk_sdv12_total), abs(bulk_se_total), EPS),
        "fracture_energy_local_term": frac_local_total,
        "fracture_energy_gradient_term": frac_gradient_total,
        "total_fracture_energy": total_fracture,
        "total_reconstructed_internal_energy": total_internal,
        "absolute_energy_residual": residual,
        "relative_energy_residual": abs(residual) / max(abs(signed_work), abs(total_internal), EPS),
        "jacobian_determinants_positive": positive_jacobians,
        "thickness": THICKNESS,
        "Gc": GC,
        "lc": LC,
    }
    provenance = {
        "classification": "stage_d3a_energy_reconstruction_input_provenance",
        "source_job": args.source_job_id,
        "checkpoint_U2": selection["actual_U2"],
        "input_deck": str(args.input_deck),
        "input_deck_sha256": sha256(args.input_deck),
        "state_csv": str(args.state_csv),
        "nodal_d_csv": str(args.nodal_d_csv),
        "rf_u_csv": str(args.rf_u_csv),
        "selection_json": str(args.selection_json),
        "method": "independent_Q4_2x2_quadrature_from_existing_H0_ODB_exports",
        "new_fracture_solve": False,
        "uel_compilation": False,
    }
    args.out_dir.joinpath("D3A_RECONSTRUCTED_ENERGY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_dir.joinpath("D3A_ENERGY_INPUT_PROVENANCE.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = [
        "# D3A Independent Energy Reconstruction",
        "",
        "Classification: `stage_d3a_energy_reconstructed`",
        "",
        "- Source job: `{}`".format(args.source_job_id),
        "- Checkpoint U2: `{}` mm".format(selection["actual_U2"]),
        "- External work: `{}`".format(signed_work),
        "- Bulk energy from SDV12: `{}`".format(bulk_sdv12_total),
        "- Bulk energy from 0.5*S:E: `{}`".format(bulk_se_total),
        "- Undamaged bulk energy from SDV13: `{}`".format(bulk_sdv13_total),
        "- Fracture energy local term: `{}`".format(frac_local_total),
        "- Fracture energy gradient term: `{}`".format(frac_gradient_total),
        "- Total reconstructed internal energy: `{}`".format(total_internal),
        "- Relative energy residual: `{}`".format(summary["relative_energy_residual"]),
        "",
        "The reconstruction uses the accepted H0 input deck connectivity, the",
        "checkpoint nodal phase field, and exported integration-point state.",
        "No Abaqus/Standard solve and no UEL compilation are performed.",
        "",
    ]
    args.out_dir.joinpath("D3A_ENERGY_BALANCE_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-csv", type=Path, required=True)
    parser.add_argument("--nodal-d-csv", type=Path, required=True)
    parser.add_argument("--rf-u-csv", type=Path, required=True)
    parser.add_argument("--selection-json", type=Path, required=True)
    parser.add_argument("--input-deck", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--source-job-id", default="1376154.mmaster02")
    args = parser.parse_args()
    reconstruct(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
