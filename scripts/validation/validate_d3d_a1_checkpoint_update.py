#!/usr/bin/env python3
"""Validate D3D-A1 offline checkpoint update and prepare its candidate package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

PASS = "stage_d3d_a1_checkpoint_obstacle_update_pass"
FAIL = "stage_d3d_a1_checkpoint_obstacle_update_fail"
PACKAGE = "stage_d3d_a1_candidate_package_prepared"
FREE_TOL = 1.0e-8
MULT_TOL = -1.0e-8
ACTIVE_BOUND_TOL = 1.0e-10
LOWER_TOL = 1.0e-10


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def bool_value(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate(source, kkt, functional, updated_rows, source_h_rows):
    failures = []
    checks = {
        "source_phase_coverage": int(kkt.get("source_phase_coverage", 0)) == 6601,
        "source_H_coverage": int(kkt.get("source_H_coverage", 0)) == 25600,
        "final_H_coverage": int(kkt.get("final_H_coverage", 0)) == 25600,
        "H_unchanged": int(kkt.get("H_changes", -1)) == 0,
        "non_positive_detJ": int(kkt.get("non_positive_detJ", -1)) == 0,
        "source_initial_active": int(source.get("initial_active_nodes", 0)) == 6446,
        "source_initial_free": int(source.get("initial_free_nodes", 0)) == 155,
        "source_seed_count": int(source.get("negative_active_multipliers", 0)) == 30,
        "endpoint_union_not_used": not bool(source.get("endpoint_union_used_as_release_set", True)),
        "converged": bool(kkt.get("deterministic_convergence_status", False)),
        "free_residual": float(kkt.get("free_residual_infinity_norm", float("inf"))) <= FREE_TOL,
        "active_multiplier": float(kkt.get("minimum_active_multiplier", -float("inf"))) >= MULT_TOL,
        "active_bound_error": float(kkt.get("active_bound_error", float("inf"))) <= ACTIVE_BOUND_TOL,
        "lower_bound_margin": float(kkt.get("minimum_lower_bound_margin", -float("inf"))) >= -LOWER_TOL,
        "phase_decreases": int(kkt.get("phase_decrease_violations", -1)) == 0,
        "lower_bound_violations": int(kkt.get("lower_bound_violations", -1)) == 0,
        "functional_nonincrease": bool(functional.get("functional_nonincrease", False))
        and float(functional.get("functional_change", float("inf"))) <= 1.0e-15,
        "state_reset": not bool(kkt.get("state_reset", True)),
        "spatial_variation_retained": bool(kkt.get("spatial_variation_retained", False)),
        "updated_node_rows": len(updated_rows) == 6601,
        "source_H_rows": len(source_h_rows) == 25600,
    }
    if updated_rows:
        checks["all_final_d_above_F3"] = min(
            float(row["d_D3D_A1"]) - float(row["d_F3"]) for row in updated_rows
        ) >= -LOWER_TOL
    else:
        checks["all_final_d_above_F3"] = False
    for name, passed in checks.items():
        if not passed:
            failures.append(name)
    return checks, failures


def prepare_package(target_dir: Path, package_dir: Path):
    updated = read_csv(target_dir / "D3D_A1_UPDATED_NODAL_D.csv")
    lower = read_csv(target_dir / "D3D_A1_SOURCE_NODAL_LOWER_BOUND.csv")
    history = read_csv(target_dir / "D3D_A1_SOURCE_IP_H.csv")
    active = read_csv(target_dir / "D3D_A1_UPDATED_ACTIVE_SET_BY_NODE.csv")

    write_csv(
        package_dir / "D3_TRANSFERRED_NODAL_D.csv",
        ["node", "x", "y", "d"],
        (
            {"node": row["node"], "x": row["x"], "y": row["y"], "d": row["d_D3D_A1"]}
            for row in updated
        ),
    )
    write_csv(
        package_dir / "D3_TRANSFERRED_IP_H.csv",
        ["element", "integration_point", "H"],
        (
            {
                "element": row["element"],
                "integration_point": row["integration_point"],
                "H": row["H_F3"],
            }
            for row in history
        ),
    )
    write_csv(
        package_dir / "D3_LOWER_BOUND_NODAL_D.csv",
        ["node", "x", "y", "d_lower_bound"],
        (
            {
                "node": row["node"], "x": row["x"], "y": row["y"],
                "d_lower_bound": row["d_lower_bound_F3"],
            }
            for row in lower
        ),
    )
    write_csv(
        package_dir / "D3_ACTIVE_SET_BY_NODE.csv",
        ["node", "x", "y", "active_lower_bound", "d_compatible", "d_lb",
         "bound_margin", "residual_Kd_minus_f"],
        (
            {
                "node": row["node"], "x": row["x"], "y": row["y"],
                "active_lower_bound": row["active_lower_bound"],
                "d_compatible": row["d_D3D_A1"], "d_lb": row["d_lb_F3"],
                "bound_margin": row["bound_margin"],
                "residual_Kd_minus_f": row["residual_Kd_minus_f"],
            }
            for row in active
        ),
    )
    package_files = [
        package_dir / "D3_TRANSFERRED_NODAL_D.csv",
        package_dir / "D3_TRANSFERRED_IP_H.csv",
        package_dir / "D3_LOWER_BOUND_NODAL_D.csv",
        package_dir / "D3_ACTIVE_SET_BY_NODE.csv",
    ]
    hashes = {path.name: sha256_file(path) for path in package_files}
    manifest = {
        "classification": PACKAGE,
        "source_classification": PASS,
        "source_job": "1377558.mmaster02",
        "source_frame": "F3_release_last",
        "checkpoint_u2_mm": 0.003000000026077032,
        "transferred_nodal_d": "offline corrected D3D-A1 checkpoint phase",
        "transferred_ip_H": "unchanged actual F3 SDV16",
        "lower_bound_nodal_d": "original recovered F3 phase",
        "active_set": "converged D3D-A1 KKT set",
        "candidate_restart_state": True,
        "accepted_restart_state": False,
        "mechanical_reequilibration_required": True,
        "abaqus_hold_authorized": False,
        "file_sha256": hashes,
    }
    write_json(package_dir / "D3D_A1_PACKAGE_MANIFEST.json", manifest)
    validation = {
        "classification": PACKAGE,
        "valid": True,
        "nodes": len(updated),
        "integration_points": len(history),
        "active_nodes": sum(bool_value(row["active_lower_bound"]) for row in active),
        "free_nodes": sum(not bool_value(row["active_lower_bound"]) for row in active),
        "H_changes": 0,
        "lower_bound_source_is_F3": True,
        "endpoint_union_used": False,
        "file_sha256": hashes,
    }
    write_json(package_dir / "D3D_A1_PACKAGE_VALIDATION.json", validation)
    return manifest, validation


def validate(target_dir: Path, package_dir: Path, create_package: bool = True):
    required = [
        "D3D_A1_SOURCE_STATE_AUDIT.json",
        "D3D_A1_KKT_VALIDATION.json",
        "D3D_A1_PHASE_FUNCTIONAL_COMPARISON.json",
        "D3D_A1_UPDATED_NODAL_D.csv",
        "D3D_A1_SOURCE_IP_H.csv",
        "D3D_A1_UPDATE_SUMMARY.json",
    ]
    missing = [name for name in required if not (target_dir / name).exists()]
    if missing:
        result = {"classification": FAIL, "D3D_A1_ok": False, "failures": [f"missing:{x}" for x in missing]}
        write_json(target_dir / "D3D_A1_KKT_VALIDATION.json", result)
        return result

    source = read_json(target_dir / "D3D_A1_SOURCE_STATE_AUDIT.json")
    kkt = read_json(target_dir / "D3D_A1_KKT_VALIDATION.json")
    functional = read_json(target_dir / "D3D_A1_PHASE_FUNCTIONAL_COMPARISON.json")
    updated = read_csv(target_dir / "D3D_A1_UPDATED_NODAL_D.csv")
    source_h = read_csv(target_dir / "D3D_A1_SOURCE_IP_H.csv")
    checks, failures = evaluate(source, kkt, functional, updated, source_h)
    passed = not failures
    result = {
        **kkt,
        "classification": PASS if passed else FAIL,
        "D3D_A1_ok": passed,
        "checks": checks,
        "failures": failures,
        "candidate_package_prepared": False,
        "abaqus_hold_authorized": False,
        "solver_submission_authorized": False,
        "d3e_authorized": False,
    }
    write_json(target_dir / "D3D_A1_KKT_VALIDATION.json", result)
    summary = read_json(target_dir / "D3D_A1_UPDATE_SUMMARY.json")
    summary.update({
        "classification": result["classification"],
        "D3D_A1_ok": passed,
        "validation_failures": failures,
    })
    if passed and create_package:
        prepare_package(target_dir, package_dir)
        result["candidate_package_prepared"] = True
        summary["candidate_package_prepared"] = True
        write_json(target_dir / "D3D_A1_KKT_VALIDATION.json", result)
    write_json(target_dir / "D3D_A1_UPDATE_SUMMARY.json", summary)
    ok = target_dir / "D3D_A1.ok"
    if passed:
        ok.write_text(PASS + "\n", encoding="utf-8")
    elif ok.exists():
        ok.unlink()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-dir", type=Path,
        default=Path("runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_update"),
    )
    parser.add_argument(
        "--package-dir", type=Path,
        default=Path("runs/hpc/stage_d3/fracture_continuation/package_d3d_a1_checkpoint_r1"),
    )
    parser.add_argument("--skip-package", action="store_true")
    args = parser.parse_args()
    result = validate(args.target_dir, args.package_dir, not args.skip_package)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("D3D_A1_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
