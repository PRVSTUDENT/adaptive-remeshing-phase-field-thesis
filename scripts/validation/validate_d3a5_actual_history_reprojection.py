#!/usr/bin/env python3
"""Validate D3A5 actual-history reprojection and prepare package_compatible_r2."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.solve_d3a4_phase_compatibility import load_mesh  # noqa: E402
from scripts.validation.validate_d3a4_phase_compatibility import (  # noqa: E402
    det_jacobian,
    ip_xy,
    THICKNESS,
)

EXPECTED_NODES = 6601
EXPECTED_ELEMENTS = 6400
EXPECTED_IPS = 25600
EXPECTED_ACTUAL_FREE_RESIDUAL = 1.2035463824381645e-08
EXPECTED_MAX_FREE_RESIDUAL_NODE = 3200
PASS_CLASSIFICATION = "stage_d3a5_actual_history_reprojection_pass"
PACKAGE_PASS = "stage_d3a5_compatible_package_r2_pass"

FREE_RES_TOL = 1.0e-10
ACTIVE_MULT_TOL = -1.0e-10
ACTIVE_BOUND_TOL = 1.0e-12
COMPLEMENTARITY_TOL = 1.0e-10
BOUND_TOL = 1.0e-12
FUNCTIONAL_TOL = 1.0e-12


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def finite_rows(rows, fields):
    for row in rows:
        for field in fields:
            try:
                if not math.isfinite(float(row[field])):
                    return False
            except Exception:
                return False
    return True


def validate(target_dir: Path):
    failures = []
    required = [
        "D3A5_INPUT_PROVENANCE.json",
        "D3A5_SOURCE_HASHES.json",
        "D3A5_HISTORY_CHANGE_BY_IP.csv",
        "D3A5_HISTORY_CHANGE_AUDIT.json",
        "D3A5_RESIDUAL_CAUSAL_AUDIT.json",
        "D3A5_REPROJECTED_NODAL_D.csv",
        "D3A5_ACTIVE_SET_BY_NODE.csv",
        "D3A5_KKT_METRICS.json",
        "D3A5_PHASE_FUNCTIONAL_COMPARISON.json",
        "D3A5_STATUS.json",
    ]
    for name in required:
        if not (target_dir / name).exists():
            failures.append(name + " missing")
    if failures:
        return {
            "classification": "stage_d3a5_actual_history_reprojection_fail",
            "D3A5_ok": False,
            "failures": failures,
        }

    history = read_json(target_dir / "D3A5_HISTORY_CHANGE_AUDIT.json")
    causal = read_json(target_dir / "D3A5_RESIDUAL_CAUSAL_AUDIT.json")
    kkt = read_json(target_dir / "D3A5_KKT_METRICS.json")
    functional = read_json(target_dir / "D3A5_PHASE_FUNCTIONAL_COMPARISON.json")
    reprojected = read_csv(target_dir / "D3A5_REPROJECTED_NODAL_D.csv")
    active = read_csv(target_dir / "D3A5_ACTIVE_SET_BY_NODE.csv")

    # Causal residual requirements.
    if int(causal.get("node_coverage", -1)) != EXPECTED_NODES:
        failures.append("actual-H node coverage = %s" % causal.get("node_coverage"))
    if int(causal.get("old_H_ip_coverage", -1)) != EXPECTED_IPS:
        failures.append("old-H IP coverage = %s" % causal.get("old_H_ip_coverage"))
    if int(causal.get("actual_H_ip_coverage", -1)) != EXPECTED_IPS:
        failures.append("actual-H IP coverage = %s" % causal.get("actual_H_ip_coverage"))
    if int(history.get("ip_coverage_old", -1)) != EXPECTED_IPS:
        failures.append("history old IP coverage = %s" % history.get("ip_coverage_old"))
    if int(history.get("ip_coverage_actual", -1)) != EXPECTED_IPS:
        failures.append("history actual IP coverage = %s" % history.get("ip_coverage_actual"))
    if int(causal.get("non_positive_detJ_old", -1)) != 0 or int(causal.get("non_positive_detJ_actual", -1)) != 0:
        failures.append("non-positive detJ in causal residual assemblies")
    act_metrics = causal.get("actual_H_metrics", {})
    free_res = float(act_metrics.get("free_set_residual_infinity_norm", float("inf")))
    if abs(free_res - EXPECTED_ACTUAL_FREE_RESIDUAL) > 1.0e-16:
        failures.append(
            "actual-H free residual does not reproduce replay value: %s vs %s"
            % (free_res, EXPECTED_ACTUAL_FREE_RESIDUAL)
        )
    if int(act_metrics.get("maximum_free_residual_node", -1)) != EXPECTED_MAX_FREE_RESIDUAL_NODE:
        failures.append(
            "maximum free residual node = %s expected %s"
            % (act_metrics.get("maximum_free_residual_node"), EXPECTED_MAX_FREE_RESIDUAL_NODE)
        )

    # Geometry / finiteness / KKT.
    if int(kkt.get("nodes", -1)) != EXPECTED_NODES:
        failures.append("nodes = %s" % kkt.get("nodes"))
    if int(kkt.get("elements", -1)) != EXPECTED_ELEMENTS:
        failures.append("elements = %s" % kkt.get("elements"))
    if int(kkt.get("integration_points", -1)) != EXPECTED_IPS:
        failures.append("integration points = %s" % kkt.get("integration_points"))
    if int(kkt.get("non_positive_detJ", -1)) != 0:
        failures.append("non-positive detJ = %s" % kkt.get("non_positive_detJ"))
    if not kkt.get("all_values_finite", False):
        failures.append("nonfinite values present")
    if len(reprojected) != EXPECTED_NODES or len(active) != EXPECTED_NODES:
        failures.append("node output row count mismatch")
    if not finite_rows(reprojected, ["d_F1", "d_D3A5", "d_D3A5_minus_d_F1", "residual_Kd_minus_f"]):
        failures.append("nonfinite reprojected nodal values")
    if not finite_rows(active, ["d_compatible", "d_lb", "bound_margin", "residual_Kd_minus_f"]):
        failures.append("nonfinite active-set values")

    if float(kkt.get("minimum_d_D3A5_minus_d_F1", -float("inf"))) < -BOUND_TOL:
        failures.append("min(dD3A5-dF1) = %s" % kkt.get("minimum_d_D3A5_minus_d_F1"))
    if float(kkt.get("minimum_d_D3A5", -float("inf"))) < -BOUND_TOL:
        failures.append("min(dD3A5) = %s" % kkt.get("minimum_d_D3A5"))
    if float(kkt.get("maximum_d_D3A5", float("inf"))) > 1.0 + BOUND_TOL:
        failures.append("max(dD3A5) = %s" % kkt.get("maximum_d_D3A5"))

    if not kkt.get("converged"):
        failures.append("active-set solver did not converge")
    if not kkt.get("active_set_membership_stable"):
        failures.append("active-set membership did not stabilize")
    if int(kkt.get("iterations", 0)) <= 0 or int(kkt.get("iterations", 9999)) > 200:
        failures.append("iterations out of bounds: %s" % kkt.get("iterations"))
    if float(kkt.get("free_set_residual_infinity_norm", float("inf"))) > FREE_RES_TOL:
        failures.append(
            "free residual infinity norm = %s > %s"
            % (kkt.get("free_set_residual_infinity_norm"), FREE_RES_TOL)
        )
    if float(kkt.get("minimum_active_set_multiplier", -float("inf"))) < ACTIVE_MULT_TOL:
        failures.append(
            "minimum active multiplier = %s < %s"
            % (kkt.get("minimum_active_set_multiplier"), ACTIVE_MULT_TOL)
        )
    if float(kkt.get("active_bound_error", float("inf"))) > ACTIVE_BOUND_TOL:
        failures.append(
            "active bound error = %s > %s" % (kkt.get("active_bound_error"), ACTIVE_BOUND_TOL)
        )
    if float(kkt.get("complementarity_infinity_norm", float("inf"))) > COMPLEMENTARITY_TOL:
        failures.append(
            "complementarity infinity norm = %s > %s"
            % (kkt.get("complementarity_infinity_norm"), COMPLEMENTARITY_TOL)
        )
    if int(kkt.get("predicted_phase_decrease_violations", -1)) != 0:
        failures.append(
            "predicted phase-decrease violations = %s"
            % kkt.get("predicted_phase_decrease_violations")
        )
    if float(functional.get("D3A5_minus_F1", float("inf"))) > FUNCTIONAL_TOL:
        failures.append(
            "phase functional at dD3A5 exceeds F1 by %s" % functional.get("D3A5_minus_F1")
        )

    passed = not failures
    return {
        "classification": PASS_CLASSIFICATION if passed else "stage_d3a5_actual_history_reprojection_fail",
        "D3A5_ok": passed,
        "failures": failures,
        "history_audit": history,
        "residual_causal_audit": causal,
        "kkt_metrics": kkt,
        "phase_functional_comparison": functional,
        "active_node_count": kkt.get("active_node_count"),
        "free_node_count": kkt.get("free_node_count"),
        "maximum_phase_increase": kkt.get("maximum_d_increase"),
        "normalized_L2_phase_increase": kkt.get("normalized_L2_d_increase"),
        "functional_reduction": functional.get("functional_reduction_from_F1"),
        "changed_active_set_count_vs_d3a4": kkt.get("changed_active_set_count_vs_d3a4"),
        "iterations": kkt.get("iterations"),
    }


def prepare_package_r2(target_dir: Path, source_dir: Path, model_dir: Path, package_dir: Path):
    package_dir.mkdir(parents=True, exist_ok=True)
    nodes, elements = load_mesh(model_dir)
    reprojected = {
        int(row["node"]): float(row["d_D3A5"])
        for row in read_csv(target_dir / "D3A5_REPROJECTED_NODAL_D.csv")
    }
    lower_bound = {
        int(row["node"]): float(row["d_F1"])
        for row in read_csv(target_dir / "D3A5_REPROJECTED_NODAL_D.csv")
    }
    active_rows = read_csv(target_dir / "D3A5_ACTIVE_SET_BY_NODE.csv")
    f1_state = [
        row for row in read_csv(source_dir / "D3A3_STATE_BY_FRAME.csv")
        if row["frame_tag"] == "F1_equilibrated"
    ]
    state_by_key = {
        (int(row["element"]), int(row["uel_integration_point"])): row
        for row in f1_state
    }

    nodal_rows = [
        {"node": node, "x": nodes[node][0], "y": nodes[node][1], "d": reprojected[node]}
        for node in sorted(reprojected)
    ]
    lower_rows = [
        {
            "node": node,
            "x": nodes[node][0],
            "y": nodes[node][1],
            "d_lower_bound": lower_bound[node],
        }
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
    write_csv(
        package_dir / "D3_LOWER_BOUND_NODAL_D.csv",
        ["node", "x", "y", "d_lower_bound"],
        lower_rows,
    )
    write_csv(
        package_dir / "D3_ACTIVE_SET_BY_NODE.csv",
        list(active_rows[0].keys()),
        active_rows,
    )
    manifest = {
        "classification": PACKAGE_PASS,
        "nodal_d": "D3A5 reprojected d against actual R3 F1 H",
        "ip_H": "actual R3 F1 odb_sdv16 from job 1377417",
        "lower_bound": "recovered R3 F1 nodal d",
        "active_set": "D3A5 active set",
        "source_d3a5_dir": str(target_dir.as_posix()),
        "source_r3_dir": str(source_dir.as_posix()),
        "original_package_r1_preserved": True,
        "package_r1_replaced": False,
        "solver_job_submitted": False,
        "nodes": len(nodal_rows),
        "integration_points": len(ip_rows),
        "active_nodes": sum(
            1 for row in active_rows if str(row["active_lower_bound"]).lower() in ("true", "1", "yes")
        ),
    }
    write_json(package_dir / "D3_PACKAGE_COMPATIBLE_R2_MANIFEST.json", manifest)
    (package_dir / "D3_PACKAGE_COMPATIBLE_R2.ok").write_text(PACKAGE_PASS + "\n", encoding="utf-8")
    return manifest


def write_report(target_dir: Path, status: dict, package_manifest=None):
    kkt = status.get("kkt_metrics", {})
    causal = status.get("residual_causal_audit", {})
    history = status.get("history_audit", {})
    functional = status.get("phase_functional_comparison", {})
    lines = [
        "# D3A5 Actual-History Compatibility Reprojection Report",
        "",
        "- Classification: `%s`" % status.get("classification"),
        "- D3A5.ok: `%s`" % status.get("D3A5_ok"),
        "",
        "Offline sparse active-set obstacle solve using recovered R3 F1 phase as lower bound",
        "and actual R3 F1 SDV16 history. No Abaqus job, ODB reread, Fortran, or new mesh.",
        "",
        "## History change",
        "",
        "- max |H_actual - H_old|: `%s`" % history.get("maximum_abs_H_actual_minus_H_old"),
        "- normalized L2 H difference: `%s`" % history.get("normalized_L2_H_difference"),
        "- H increase / decrease counts: `%s` / `%s`"
        % (history.get("H_increase_count"), history.get("H_decrease_count")),
        "- H_old sum / H_actual sum: `%s` / `%s`"
        % (history.get("H_old_sum"), history.get("H_actual_sum")),
        "",
        "## Causal residual at d_F1",
        "",
        "- actual free residual: `%s`"
        % causal.get("actual_H_metrics", {}).get("free_set_residual_infinity_norm"),
        "- old free residual: `%s`"
        % causal.get("old_H_metrics", {}).get("free_set_residual_infinity_norm"),
        "- max free residual node: `%s`"
        % causal.get("actual_H_metrics", {}).get("maximum_free_residual_node"),
        "",
        "## KKT",
        "",
        "- active / free nodes: `%s` / `%s`"
        % (kkt.get("active_node_count"), kkt.get("free_node_count")),
        "- free residual inf: `%s`" % kkt.get("free_set_residual_infinity_norm"),
        "- min active multiplier: `%s`" % kkt.get("minimum_active_set_multiplier"),
        "- active bound error: `%s`" % kkt.get("active_bound_error"),
        "- max phase increase: `%s`" % kkt.get("maximum_d_increase"),
        "- normalized L2 phase increase: `%s`" % kkt.get("normalized_L2_d_increase"),
        "- functional reduction: `%s`" % functional.get("functional_reduction_from_F1"),
        "- changed active-set count vs D3A4: `%s`" % kkt.get("changed_active_set_count_vs_d3a4"),
        "- iterations: `%s`" % kkt.get("iterations"),
        "",
        "## Failures",
        "",
    ]
    if status.get("failures"):
        for item in status["failures"]:
            lines.append("- %s" % item)
    else:
        lines.append("- none")
    if package_manifest:
        lines.extend([
            "",
            "## package_compatible_r2",
            "",
            "- classification: `%s`" % package_manifest.get("classification"),
            "- nodes / IPs: `%s` / `%s`"
            % (package_manifest.get("nodes"), package_manifest.get("integration_points")),
            "- active nodes: `%s`" % package_manifest.get("active_nodes"),
        ])
    lines.append("")
    (target_dir / "D3A5_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/compatibility_reprojection_d3a5"),
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r3_compatible"),
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("models/state_transfer/d3_interrupted_transfer"),
    )
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2"),
    )
    parser.add_argument(
        "--skip-package",
        action="store_true",
        help="Validate only; do not prepare package_compatible_r2.",
    )
    args = parser.parse_args()

    status = validate(args.target_dir)
    package_manifest = None
    if status["D3A5_ok"] and not args.skip_package:
        package_manifest = prepare_package_r2(
            args.target_dir, args.source_dir, args.model_dir, args.package_dir
        )
        status["package_compatible_r2"] = package_manifest
    write_report(args.target_dir, status, package_manifest)

    # Persist validated status and marker only on pass.
    final_status = dict(status)
    write_json(args.target_dir / "D3A5_STATUS.json", final_status)
    ok_path = args.target_dir / "D3A5.ok"
    if status["D3A5_ok"]:
        ok_path.write_text(PASS_CLASSIFICATION + "\n", encoding="utf-8")
    elif ok_path.exists():
        ok_path.unlink()

    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["D3A5_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
