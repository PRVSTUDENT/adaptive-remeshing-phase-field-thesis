#!/usr/bin/env python3
"""Validate independent D3A checkpoint energy reconstruction."""

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Dict, List


EXPECTED_ELEMENTS = 3930
EXPECTED_IP_ROWS = 15720
BULK_REL_TOL = 1.0e-6
BALANCE_REL_TOL = 0.05
EPS = 1.0e-30


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def validate(out_dir: Path, checkpoint_dir: Path, job_id: str) -> Dict[str, object]:
    failures: List[str] = []
    summary = json.loads((out_dir / "D3A_RECONSTRUCTED_ENERGY.json").read_text(encoding="utf-8"))
    state_rows = read_csv(out_dir / "D3A_CHECKPOINT_STATE_WITH_ENERGY.csv")
    external_rows = read_csv(out_dir / "D3A_EXTERNAL_WORK_PATH.csv")

    seen = set()
    d_values = []
    h_values = []
    detj_values = []
    for row in state_rows:
        try:
            key = (int(row["element"]), int(row["integration_point"]))
        except Exception as exc:
            failures.append(f"invalid element/IP key: {exc}")
            continue
        if key in seen:
            failures.append(f"duplicate element/IP key {key[0]}/{key[1]}")
        seen.add(key)
        for name in [
            "x",
            "y",
            "gauss_xi",
            "gauss_eta",
            "gauss_weight",
            "detJ",
            "SDV12_degraded_elastic_energy_density",
            "SDV13_undamaged_elastic_energy_density",
            "SDV15_d",
            "SDV16_H",
            "SDV3_E11",
            "SDV4_E22",
            "SDV5_E12",
            "SDV6_degraded_S11",
            "SDV7_degraded_S22",
            "SDV8_degraded_S12",
            "phase_d_from_nodes",
            "grad_d_x",
            "grad_d_y",
        ]:
            if not finite(row.get(name, "")):
                failures.append(f"{name} is not finite for {key[0]}/{key[1]}")
                break
        if not finite(row.get("detJ", "")):
            continue
        detj = float(row["detJ"])
        detj_values.append(detj)
        if detj <= 0.0:
            failures.append(f"non-positive Jacobian for {key[0]}/{key[1]}: {detj}")
        if finite(row.get("SDV15_d", "")):
            d = float(row["SDV15_d"])
            d_values.append(d)
            if d < -1.0e-12 or d > 1.0 + 1.0e-12:
                failures.append(f"d out of bounds for {key[0]}/{key[1]}: {d}")
        if finite(row.get("SDV16_H", "")):
            h = float(row["SDV16_H"])
            h_values.append(h)
            if h < -1.0e-12:
                failures.append(f"H is negative for {key[0]}/{key[1]}: {h}")

    element_count = len({k[0] for k in seen})
    if element_count != EXPECTED_ELEMENTS:
        failures.append(f"expected {EXPECTED_ELEMENTS} physical elements, found {element_count}")
    if len(state_rows) != EXPECTED_IP_ROWS:
        failures.append(f"expected {EXPECTED_IP_ROWS} integration-point rows, found {len(state_rows)}")
    if abs(float(summary.get("ip_coverage", 0.0)) - 1.0) > 1.0e-12:
        failures.append(f"IP coverage is not 1.0: {summary.get('ip_coverage')}")
    if int(summary.get("nodal_phase_rows", 0)) < 3999:
        failures.append(f"nodal phase coverage incomplete: {summary.get('nodal_phase_rows')}")
    if len(seen) != len(state_rows):
        failures.append("state rows contain duplicate element/IP keys")

    for name in [
        "external_work",
        "absolute_loading_work",
        "bulk_energy_from_SDV12",
        "bulk_energy_from_stress_strain",
        "undamaged_bulk_energy_from_SDV13",
        "fracture_energy_local_term",
        "fracture_energy_gradient_term",
        "total_fracture_energy",
        "total_reconstructed_internal_energy",
        "absolute_energy_residual",
        "relative_energy_residual",
    ]:
        if not finite(summary.get(name)):
            failures.append(f"{name} is not finite")

    bulk_rel = float(summary.get("bulk_sdv12_vs_stress_strain_relative_difference", float("inf")))
    if not math.isfinite(bulk_rel) or bulk_rel > BULK_REL_TOL:
        failures.append(
            "integrated SDV12 vs 0.5*S:E relative difference exceeds "
            f"{BULK_REL_TOL}: {bulk_rel}"
        )
    if float(summary.get("fracture_energy_local_term", -1.0)) < -1.0e-14:
        failures.append("local fracture energy is negative")
    if float(summary.get("fracture_energy_gradient_term", -1.0)) < -1.0e-14:
        failures.append("gradient fracture energy is negative")
    if float(summary.get("total_fracture_energy", -1.0)) < -1.0e-14:
        failures.append("total fracture energy is negative")
    if not summary.get("external_work_path_nondecreasing"):
        failures.append("external work path is not nondecreasing during monotonic loading")
    rel_residual = float(summary.get("relative_energy_residual", float("inf")))
    if not math.isfinite(rel_residual) or rel_residual > BALANCE_REL_TOL:
        failures.append(f"relative energy residual exceeds {BALANCE_REL_TOL}: {rel_residual}")

    previous_work = None
    for row in external_rows:
        for name in ["U2", "RF2", "cumulative_signed_work"]:
            if not finite(row.get(name, "")):
                failures.append(f"external work path {name} is not finite")
                break
        work = float(row["cumulative_signed_work"])
        if previous_work is not None and work < previous_work - 1.0e-14:
            failures.append("external work cumulative path decreases")
            break
        previous_work = work

    status = {
        "classification": (
            "stage_d3a_checkpoint_pass_independent_energy_reconstruction"
            if not failures
            else "stage_d3a_energy_reconstruction_fail"
        ),
        "D3A_ok": not failures,
        "job_id": job_id,
        "physical_elements": element_count,
        "integration_point_rows": len(state_rows),
        "ip_coverage": summary.get("ip_coverage"),
        "nodal_phase_rows": summary.get("nodal_phase_rows"),
        "max_d": max(d_values) if d_values else None,
        "max_H": max(h_values) if h_values else None,
        "ip_count_d_ge_0p1": summary.get("ip_count_d_ge_0p1"),
        "ip_count_d_ge_0p5": summary.get("ip_count_d_ge_0p5"),
        "bulk_sdv12_vs_stress_strain_relative_difference": bulk_rel,
        "relative_energy_residual": summary.get("relative_energy_residual"),
        "external_work": summary.get("external_work"),
        "total_reconstructed_internal_energy": summary.get("total_reconstructed_internal_energy"),
        "failures": failures,
    }
    (out_dir / "D3A_ENERGY_VALIDATION_STATUS.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not failures:
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        (checkpoint_dir / "D3A.ok").write_text(
            "\n".join([
                "classification=stage_d3a_checkpoint_pass_independent_energy_reconstruction",
                "source_job=1376154.mmaster02",
                "checkpoint_U2=0.003000000026077032",
                "energy_evidence=independent_quadrature_reconstruction",
                "",
            ]),
            encoding="utf-8",
        )
        blocked = checkpoint_dir / "D3A_BLOCKED_STATUS.json"
        if blocked.exists():
            data = json.loads(blocked.read_text(encoding="utf-8"))
            data["previous_classification"] = data.get("classification", "stage_d3a_checkpoint_blocked_missing_energy_history")
            data["classification"] = "stage_d3a_checkpoint_pass_independent_energy_reconstruction"
            data["resolved_classification"] = "stage_d3a_checkpoint_pass_independent_energy_reconstruction"
            data["D3A_ok"] = True
            data["accepted_checkpoint_marker"] = True
            data["energy_evidence"] = "independent_quadrature_reconstruction"
            blocked.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2, sort_keys=True))
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--checkpoint-dir", type=Path, required=True)
    parser.add_argument("--job-id", default="not_submitted")
    args = parser.parse_args()
    status = validate(args.out_dir, args.checkpoint_dir, args.job_id)
    return 0 if status["D3A_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
