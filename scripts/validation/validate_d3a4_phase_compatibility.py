#!/usr/bin/env python3
"""Validate D3A4 compatibility projection outputs and prepare package_compatible_r1."""

import argparse
import csv
import json
import math
from pathlib import Path


TOL = 1.0e-10
BOUND_TOL = 1.0e-12
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


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def shape_values(ip):
    xi, eta = GAUSS[ip - 1]
    return [
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta),
    ]


def shape_grad_parent(ip):
    xi, eta = GAUSS[ip - 1]
    return [
        (-0.25 * (1.0 - eta), -0.25 * (1.0 - xi)),
        (0.25 * (1.0 - eta), -0.25 * (1.0 + xi)),
        (0.25 * (1.0 + eta), 0.25 * (1.0 + xi)),
        (-0.25 * (1.0 + eta), 0.25 * (1.0 - xi)),
    ]


def det_jacobian(coords, ip):
    dndxi = shape_grad_parent(ip)
    j11 = sum(coords[i][0] * dndxi[i][0] for i in range(4))
    j12 = sum(coords[i][0] * dndxi[i][1] for i in range(4))
    j21 = sum(coords[i][1] * dndxi[i][0] for i in range(4))
    j22 = sum(coords[i][1] * dndxi[i][1] for i in range(4))
    return j11 * j22 - j12 * j21


def ip_xy(coords, ip):
    n = shape_values(ip)
    return (
        sum(n[i] * coords[i][0] for i in range(4)),
        sum(n[i] * coords[i][1] for i in range(4)),
    )


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


def finite_rows(rows, fields):
    for row in rows:
        for field in fields:
            try:
                if not math.isfinite(float(row[field])):
                    return False
            except Exception:
                return False
    return True


def validate(target_dir):
    failures = []
    required = [
        "D3A4_INPUT_PROVENANCE.json",
        "D3A4_ASSEMBLY_AUDIT.json",
        "D3A4_F1_RESIDUAL_RECONSTRUCTED.csv",
        "D3A4_UNCONSTRAINED_NODAL_D.csv",
        "D3A4_UNCONSTRAINED_COMPARISON.json",
        "D3A4_CONSTRAINED_NODAL_D.csv",
        "D3A4_ACTIVE_SET_BY_NODE.csv",
        "D3A4_KKT_METRICS.json",
        "D3A4_PHASE_FUNCTIONAL_COMPARISON.json",
    ]
    for name in required:
        if not (target_dir / name).exists():
            failures.append(f"{name} missing")
    if failures:
        return {"classification": "stage_d3a4_constrained_phase_compatibility_fail", "failures": failures}

    assembly = read_json(target_dir / "D3A4_ASSEMBLY_AUDIT.json")
    kkt = read_json(target_dir / "D3A4_KKT_METRICS.json")
    functional = read_json(target_dir / "D3A4_PHASE_FUNCTIONAL_COMPARISON.json")
    constrained = read_csv(target_dir / "D3A4_CONSTRAINED_NODAL_D.csv")
    active = read_csv(target_dir / "D3A4_ACTIVE_SET_BY_NODE.csv")
    residual = read_csv(target_dir / "D3A4_F1_RESIDUAL_RECONSTRUCTED.csv")

    if int(assembly.get("nodes", -1)) != 6601:
        failures.append(f"nodes={assembly.get('nodes')}, expected 6601")
    if int(assembly.get("elements", -1)) != 6400:
        failures.append(f"elements={assembly.get('elements')}, expected 6400")
    if int(assembly.get("integration_points", -1)) != 25600:
        failures.append(f"integration_points={assembly.get('integration_points')}, expected 25600")
    if int(assembly.get("non_positive_detJ", -1)) != 0:
        failures.append(f"non_positive_detJ={assembly.get('non_positive_detJ')}")
    if int(assembly.get("node_coverage", -1)) != 6601 or int(assembly.get("missing_nodes", -1)) != 0:
        failures.append("residual audit node coverage failed")
    if float(assembly.get("maximum_residual_reconstruction_error", float("inf"))) > 1.0e-12:
        failures.append(f"maximum residual reconstruction error exceeds 1e-12: {assembly.get('maximum_residual_reconstruction_error')}")
    if assembly.get("maximum_residual_node") != assembly.get("forensic_maximum_residual_node"):
        failures.append("maximum residual node mismatch")
    if float(assembly.get("residual_L2_relative_error", float("inf"))) > 1.0e-10:
        failures.append(f"residual L2 relative error exceeds 1e-10: {assembly.get('residual_L2_relative_error')}")

    if len(constrained) != 6601 or len(active) != 6601 or len(residual) != 6601:
        failures.append("node output row count mismatch")
    if not finite_rows(constrained, ["d_F1", "d_compatible", "d_compatible_minus_F1"]):
        failures.append("nonfinite constrained nodal values")
    if not finite_rows(active, ["d_compatible", "d_lb", "bound_margin", "residual_Kd_minus_f"]):
        failures.append("nonfinite active-set values")

    if not kkt.get("converged"):
        failures.append("active-set solver did not converge")
    if not kkt.get("active_set_membership_stable"):
        failures.append("active-set membership did not stabilize")
    if float(kkt.get("free_set_residual_infinity_norm", float("inf"))) > TOL:
        failures.append(f"free residual inf exceeds {TOL}: {kkt.get('free_set_residual_infinity_norm')}")
    if float(kkt.get("minimum_active_set_multiplier", -float("inf"))) < -TOL:
        failures.append(f"minimum active multiplier below -{TOL}: {kkt.get('minimum_active_set_multiplier')}")
    if float(kkt.get("complementarity_infinity_norm", float("inf"))) > TOL:
        failures.append(f"complementarity inf exceeds {TOL}: {kkt.get('complementarity_infinity_norm')}")
    if float(kkt.get("minimum_d_compatible_minus_d_F1", -float("inf"))) < -BOUND_TOL:
        failures.append(f"minimum compatible-F1 below -{BOUND_TOL}: {kkt.get('minimum_d_compatible_minus_d_F1')}")
    if float(kkt.get("minimum_d_compatible", -float("inf"))) < -BOUND_TOL:
        failures.append(f"minimum d below -{BOUND_TOL}: {kkt.get('minimum_d_compatible')}")
    if float(kkt.get("maximum_d_compatible", float("inf"))) > 1.0 + BOUND_TOL:
        failures.append(f"maximum d above 1+{BOUND_TOL}: {kkt.get('maximum_d_compatible')}")
    if int(kkt.get("predicted_healing_violations", -1)) != 0:
        failures.append(f"predicted healing violations={kkt.get('predicted_healing_violations')}")
    if float(functional.get("compatible_minus_F1", float("inf"))) > 1.0e-12:
        failures.append(f"compatible functional above F1 by {functional.get('compatible_minus_F1')}")

    classification = (
        "stage_d3a4_constrained_phase_compatibility_pass"
        if not failures
        else "stage_d3a4_constrained_phase_compatibility_fail"
    )
    return {
        "classification": classification,
        "D3A4_ok": not failures,
        "failures": failures,
        "assembly_audit": assembly,
        "kkt_metrics": kkt,
        "phase_functional_comparison": functional,
    }


def prepare_package(target_dir, forensic_dir, model_dir, package_dir):
    package_dir.mkdir(parents=True, exist_ok=True)
    nodes, elements = load_mesh(model_dir)
    constrained = {
        int(row["node"]): float(row["d_compatible"])
        for row in read_csv(target_dir / "D3A4_CONSTRAINED_NODAL_D.csv")
    }
    lower_bound = {
        int(row["node"]): float(row["d_F1"])
        for row in read_csv(target_dir / "D3A4_CONSTRAINED_NODAL_D.csv")
    }
    f1_state = [
        row for row in read_csv(forensic_dir / "D3A3_STATE_BY_FRAME.csv")
        if row["frame_tag"] == "F1_equilibrated"
    ]
    state_by_key = {
        (int(row["element"]), int(row["uel_integration_point"])): row
        for row in f1_state
    }
    nodal_rows = [
        {"node": node, "x": nodes[node][0], "y": nodes[node][1], "d": constrained[node]}
        for node in sorted(constrained)
    ]
    lower_rows = [
        {"node": node, "x": nodes[node][0], "y": nodes[node][1], "d_lower_bound": lower_bound[node]}
        for node in sorted(lower_bound)
    ]
    ip_rows = []
    for element, conn in sorted(elements.items()):
        coords = [nodes[node] for node in conn]
        for ip in range(1, 5):
            row = state_by_key[(element, ip)]
            x, y = ip_xy(coords, ip)
            detj = det_jacobian(coords, ip)
            ip_rows.append({
                "element": element,
                "integration_point": ip,
                "x": x,
                "y": y,
                "H": float(row["odb_sdv16"]),
                "SDV12_degraded_elastic_energy_density": float(row["odb_sdv12"]),
                "SDV13_undamaged_elastic_energy_density": float(row["odb_sdv13"]),
                "stress_strain_energy_density": float(row["odb_sdv16"]),
                "detJ": detj,
                "jacobian_weight": detj * THICKNESS,
            })
    write_csv(package_dir / "D3_TRANSFERRED_NODAL_D.csv", ["node", "x", "y", "d"], nodal_rows)
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
        ip_rows,
    )
    write_csv(package_dir / "D3_LOWER_BOUND_NODAL_D.csv", ["node", "x", "y", "d_lower_bound"], lower_rows)
    provenance = {
        "classification": "stage_d3a4_compatible_package_prepared",
        "nodal_d": "D3A4 constrained compatibility solution",
        "ip_H": "corrected F1 SDV16 from D3A3 forensic replay",
        "lower_bound_provenance": "original transferred checkpoint/F1 recovered nodal d",
        "source_odb": "job 1377396 forensic F1 state",
        "source_forensic_dir": str(forensic_dir),
        "source_projection_dir": str(target_dir),
        "original_package_replaced": False,
        "solver_job_submitted": False,
        "nodes": len(nodal_rows),
        "integration_points": len(ip_rows),
    }
    write_json(package_dir / "D3_COMPATIBLE_PACKAGE_PROVENANCE.json", provenance)
    (package_dir / "D3_PACKAGE_COMPATIBLE_R1.ok").write_text("stage_d3a4_compatible_package_prepared\n", encoding="utf-8")
    return provenance


def write_report(target_dir, status, package_provenance):
    kkt = status.get("kkt_metrics", {})
    assembly = status.get("assembly_audit", {})
    functional = status.get("phase_functional_comparison", {})
    lines = [
        "# D3A4 Constrained Phase Compatibility Report",
        "",
        "Classification: `%s`" % status.get("classification"),
        "",
        "This is an offline sparse active-set obstacle solve using committed D3A3-R2 forensic evidence only. No Abaqus job, Fortran compilation, new mesh, or replacement of the original D3A2 package was performed.",
        "",
        "Assembly audit:",
        "",
        "- Nodes: `%s`" % assembly.get("nodes"),
        "- Elements: `%s`" % assembly.get("elements"),
        "- Integration points: `%s`" % assembly.get("integration_points"),
        "- Maximum F1 residual reconstruction error: `%s`" % assembly.get("maximum_residual_reconstruction_error"),
        "",
        "KKT metrics:",
        "",
        "- Active nodes: `%s`" % kkt.get("active_node_count"),
        "- Free nodes: `%s`" % kkt.get("free_node_count"),
        "- Free residual infinity norm: `%s`" % kkt.get("free_set_residual_infinity_norm"),
        "- Minimum active multiplier: `%s`" % kkt.get("minimum_active_set_multiplier"),
        "- Complementarity infinity norm: `%s`" % kkt.get("complementarity_infinity_norm"),
        "- Maximum d increase: `%s`" % kkt.get("maximum_d_increase"),
        "- Normalized L2 d increase: `%s`" % kkt.get("normalized_L2_d_increase"),
        "",
        "Functional:",
        "",
        "- Compatible minus F1: `%s`" % functional.get("compatible_minus_F1"),
        "- Compatible reduction from F1: `%s`" % functional.get("compatible_reduction_from_F1"),
        "",
        "Compatible package:",
        "",
        "- Prepared: `%s`" % bool(package_provenance),
        "- Directory: `runs/hpc/stage_d3/interrupted_transfer/package_compatible_r1/`",
        "",
        "The canonical D3A3 gate remains closed until a separate bounded D3A3-R3 release test is authorized and passes.",
    ]
    (target_dir / "D3A4_COMPATIBILITY_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/compatibility_projection_d3a4"))
    parser.add_argument("--forensic-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r2_forensic"))
    parser.add_argument("--model-dir", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer"))
    parser.add_argument("--package-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r1"))
    args = parser.parse_args()
    status = validate(args.target_dir)
    package_provenance = None
    if status["D3A4_ok"]:
        (args.target_dir / "D3A4.ok").write_text("stage_d3a4_constrained_phase_compatibility_pass\n", encoding="utf-8")
        package_provenance = prepare_package(args.target_dir, args.forensic_dir, args.model_dir, args.package_dir)
        status["compatible_package"] = package_provenance
    else:
        marker = args.target_dir / "D3A4.ok"
        if marker.exists():
            marker.unlink()
    write_json(args.target_dir / "D3A4_COMPATIBILITY_STATUS.json", status)
    write_report(args.target_dir, status, package_provenance)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["D3A4_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
