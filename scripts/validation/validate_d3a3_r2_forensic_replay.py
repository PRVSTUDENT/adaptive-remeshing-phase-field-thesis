#!/usr/bin/env python3
"""Classify the D3A3-R2 ODB-only forensic replay."""

import argparse
import csv
import json
import math
from pathlib import Path


TOL = 1.0e-8
CHECKPOINT_U2 = 0.003000000026077032


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def floats(rows, column):
    out = []
    for row in rows:
        value = row.get(column, "")
        if value not in ("", None):
            out.append(float(value))
    return out


def metric(values):
    if not values:
        return {"count": 0, "l2": None, "max_abs": None}
    return {
        "count": len(values),
        "l2": math.sqrt(sum(v * v for v in values) / len(values)),
        "max_abs": max(abs(v) for v in values),
    }


def finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def validate(target_dir):
    failures = []
    required = [
        "D3A3_TRANSFER_VS_ODB.csv",
        "D3A3_RF_U_CORRECTED.csv",
        "D3A3_RELEASE_JUMP.json",
        "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json",
        "D3A3_IP_ORDER_AUDIT.json",
        "D3A3_TOP_SET_AUDIT.json",
        "D3A3_PHASE_NODE_RECOVERY_AUDIT.json",
        "D3A3_F1_PHASE_COMPATIBILITY.json",
    ]
    for name in required:
        if not (target_dir / name).exists():
            failures.append(f"{name} missing")
    if failures:
        return {"failures": failures}

    transfer = read_csv(target_dir / "D3A3_TRANSFER_VS_ODB.csv")
    rf_u = read_csv(target_dir / "D3A3_RF_U_CORRECTED.csv")
    release = read_json(target_dir / "D3A3_RELEASE_JUMP.json")
    energy = read_json(target_dir / "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json")
    ip_audit = read_json(target_dir / "D3A3_IP_ORDER_AUDIT.json")
    top_audit = read_json(target_dir / "D3A3_TOP_SET_AUDIT.json")
    recovery_audit = read_json(target_dir / "D3A3_PHASE_NODE_RECOVERY_AUDIT.json")
    compatibility = read_json(target_dir / "D3A3_F1_PHASE_COMPATIBILITY.json")

    expected_records = 6400 * 4
    sdv15_transfer = metric(floats(transfer, "sdv15_error"))
    sdv16_transfer = metric(floats(transfer, "sdv16_error"))
    if sdv15_transfer["count"] != expected_records or sdv15_transfer["max_abs"] is None or sdv15_transfer["max_abs"] > TOL:
        failures.append(f"corrected SDV15 transfer error fails: {sdv15_transfer}")
    if sdv16_transfer["count"] != expected_records or sdv16_transfer["max_abs"] is None or sdv16_transfer["max_abs"] > TOL:
        failures.append(f"corrected SDV16 transfer error fails: {sdv16_transfer}")

    if ip_audit.get("odb_to_uel_integration_point") != {"1": 1, "2": 2, "3": 4, "4": 3}:
        failures.append("IP order audit mapping mismatch")
    if not top_audit.get("top_set_pass"):
        failures.append(f"TOP-set audit failed: {top_audit.get('failures')}")

    rf_by_frame = {row["frame_tag"]: row for row in rf_u}
    for tag in ["F1_equilibrated", "F3_release_last"]:
        row = rf_by_frame.get(tag)
        if not row:
            failures.append(f"{tag} missing from corrected RF/U")
            continue
        u2_mean = float(row["top_u2_mean"])
        u2_min = float(row["top_u2_min"])
        u2_max = float(row["top_u2_max"])
        rf2 = float(row["top_rf2_sum"])
        if abs(u2_mean - CHECKPOINT_U2) > TOL or abs(u2_max - u2_min) > TOL:
            failures.append(f"{tag} corrected TOP U2 checkpoint failed")
        if not math.isfinite(rf2):
            failures.append(f"{tag} corrected TOP RF2 nonfinite")

    recovery_failures = []
    for frame in recovery_audit.get("frames", []):
        if int(frame.get("recovered_nodes", -1)) != 6601:
            recovery_failures.append(f"{frame.get('frame_tag')} recovered_nodes={frame.get('recovered_nodes')}")
        if int(frame.get("elements_with_complete_IP_state", -1)) != 6400:
            recovery_failures.append(f"{frame.get('frame_tag')} complete_elements={frame.get('elements_with_complete_IP_state')}")
        if int(frame.get("missing_nodes", -1)) != 0:
            recovery_failures.append(f"{frame.get('frame_tag')} missing_nodes={frame.get('missing_nodes')}")
        if not frame.get("all_recovered_values_finite"):
            recovery_failures.append(f"{frame.get('frame_tag')} nonfinite recovered d")
        if not frame.get("values_within_0_1_tolerance"):
            recovery_failures.append(f"{frame.get('frame_tag')} recovered d out of range")
        spread = frame.get("maximum_shared_node_reconstruction_spread")
        if spread is None or float(spread) > TOL:
            recovery_failures.append(f"{frame.get('frame_tag')} shared spread={spread}")
        if frame.get("frame_tag") in ["F0_ingested", "F1_equilibrated"]:
            delta = frame.get("maximum_recovered_minus_transferred_abs")
            if delta is None or float(delta) > TOL:
                recovery_failures.append(f"{frame.get('frame_tag')} transfer nodal d delta={delta}")
    failures.extend(recovery_failures)

    for frame in energy.get("frames", []):
        for key in ["missing_phase_node_values", "missing_sdv12_values", "missing_sdv13_values", "non_positive_detJ_count"]:
            if int(frame.get(key, -1)) != 0:
                failures.append(f"{key} nonzero for {frame.get('frame_tag')}: {frame.get(key)}")
        for key in [
            "bulk_energy_from_SDV12",
            "undamaged_bulk_energy_from_SDV13",
            "fracture_energy_local_term",
            "fracture_energy_gradient_term",
            "total_fracture_energy",
            "total_reconstructed_internal_energy",
        ]:
            if not finite(frame.get(key)):
                failures.append(f"{key} nonfinite for {frame.get('frame_tag')}")

    h_decrease = int(release.get("equilibrated_vs_released", {}).get("H_decrease_violations", -1))
    d_healing = int(release.get("equilibrated_vs_released", {}).get("d_healing_violations", -1))
    if h_decrease != 0:
        failures.append(f"H decrease violations = {h_decrease}")
    if d_healing <= 0:
        failures.append(f"d-healing violations not positive: {d_healing}")

    classification = (
        "stage_d3a3_r2_ingestion_pass_release_not_accepted"
        if not failures
        else "stage_d3a3_r2_forensic_replay_fail"
    )
    return {
        "classification": classification,
        "forensic_ok": not failures,
        "D3A3_ok": False,
        "D3A3_R2_INGESTION_ok": not failures,
        "corrected_transfer_sdv15_error": sdv15_transfer,
        "corrected_transfer_sdv16_error": sdv16_transfer,
        "H_decrease_violations": h_decrease,
        "d_healing_violations": d_healing,
        "compatibility": compatibility,
        "failures": failures,
    }


def write_report(target_dir, status):
    compatibility = status.get("compatibility", {})
    lines = [
        "# D3A3-R2 Forensic Replay Report",
        "",
        "Classification: `%s`" % status.get("classification"),
        "",
        "This replay used the preserved `1377396.mmaster02` ODB only. No Abaqus/Standard solve, Fortran compilation, transfer package generation, or mesh generation was performed.",
        "",
        "Corrected ingestion findings:",
        "",
        "- SDV15 transfer max error: `%s`" % status.get("corrected_transfer_sdv15_error", {}).get("max_abs"),
        "- SDV16 transfer max error: `%s`" % status.get("corrected_transfer_sdv16_error", {}).get("max_abs"),
        "- H decrease violations: `%s`" % status.get("H_decrease_violations"),
        "- d-healing violations after release: `%s`" % status.get("d_healing_violations"),
        "",
        "Compatibility findings:",
        "",
        "- F1 residual L2 norm: `%s`" % compatibility.get("residual_L2_norm"),
        "- Maximum residual: `%s` at node `%s`" % (compatibility.get("maximum_residual_abs"), compatibility.get("maximum_residual_node")),
        "- Correlation between F1 residual and released d change: `%s`" % compatibility.get("correlation_F1_residual_vs_released_d_change"),
        "",
        "No canonical `D3A3.ok` marker was created because released phase healing remains nonzero.",
    ]
    (target_dir / "D3A3_R2_FORENSIC_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r2_forensic"))
    args = parser.parse_args()
    status = validate(args.target_dir)
    args.target_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.target_dir / "D3A3_R2_FORENSIC_STATUS.json", status)
    write_report(args.target_dir, status)
    if status.get("D3A3_R2_INGESTION_ok"):
        (args.target_dir / "D3A3_R2_INGESTION.ok").write_text("stage_d3a3_r2_ingestion_pass_release_not_accepted\n", encoding="utf-8")
    marker = args.target_dir / "D3A3.ok"
    if marker.exists():
        marker.unlink()
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status.get("forensic_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
