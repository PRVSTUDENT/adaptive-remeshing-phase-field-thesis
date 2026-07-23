#!/usr/bin/env python3
"""Validate D3A3 static preflight or completed ingestion/hold outputs."""

import argparse
import csv
import json
import math
from pathlib import Path


DEFAULT_TOL = 1.0e-8
CHECKPOINT_U2 = 0.003000000026077032
PHASE_ADJUSTMENT_NORM_TOL = 0.05
PHASE_ADJUSTMENT_MAX_TOL = 0.01
RF_RELEASE_JUMP_TOL = 0.05
ENERGY_JUMP_TOL = 0.05


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def floats(rows, column):
    out = []
    for row in rows:
        value = row.get(column, "")
        if value not in ("", None):
            out.append(float(value))
    return out


def finite_or_none(value):
    if value in ("", None):
        return None
    out = float(value)
    return out if math.isfinite(out) else None


def by_frame(rows):
    return {row["frame_tag"]: row for row in rows}


def rel_change(a, b):
    return abs(b - a) / max(abs(a), abs(b), 1.0e-30)


def metric(values):
    if not values:
        return {"count": 0, "l2": None, "max_abs": None}
    return {
        "count": len(values),
        "l2": math.sqrt(sum(v * v for v in values) / len(values)),
        "max_abs": max(abs(v) for v in values),
    }


def require_file(target_dir, name, failures):
    path = target_dir / name
    if not path.exists():
        failures.append(f"{name} missing")
    return path


def validate_completed(target_dir, failures, tol):
    required = [
        "D3A3_STATE_BY_FRAME.csv",
        "D3A3_TRANSFER_VS_ODB.csv",
        "D3A3_INITIAL_VS_EQUILIBRATED.csv",
        "D3A3_EQUILIBRATED_VS_RELEASED.csv",
        "D3A3_RF_U.csv",
        "D3A3_ENERGY_BY_FRAME.json",
        "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME.json",
        "D3A3_RELEASE_JUMP.json",
    ]
    paths = {name: require_file(target_dir, name, failures) for name in required}
    if failures:
        return {}

    transfer = read_csv(paths["D3A3_TRANSFER_VS_ODB.csv"])
    initial_eq = read_csv(paths["D3A3_INITIAL_VS_EQUILIBRATED.csv"])
    eq_release = read_csv(paths["D3A3_EQUILIBRATED_VS_RELEASED.csv"])
    rf_u = read_csv(paths["D3A3_RF_U.csv"])
    energy = read_json(paths["D3A3_ENERGY_BY_FRAME.json"])
    reconstructed_energy = read_json(paths["D3A3_RECONSTRUCTED_ENERGY_BY_FRAME.json"])
    release = read_json(paths["D3A3_RELEASE_JUMP.json"])

    sdv15_transfer = metric(floats(transfer, "sdv15_error"))
    sdv16_transfer = metric(floats(transfer, "sdv16_error"))
    sdv15_eq = metric(floats(initial_eq, "sdv15_delta"))
    sdv16_eq = metric(floats(initial_eq, "sdv16_delta"))
    sdv15_release = metric(floats(eq_release, "sdv15_delta"))
    sdv16_release = metric(floats(eq_release, "sdv16_delta"))

    expected_records = 6400 * 4
    if len(transfer) != expected_records:
        failures.append(f"D3A3_TRANSFER_VS_ODB.csv rows={len(transfer)}, expected {expected_records}")
    for name, data in [
        ("sdv15_transfer", sdv15_transfer),
        ("sdv16_transfer", sdv16_transfer),
    ]:
        if data["count"] != expected_records:
            failures.append(f"{name} has {data['count']} numeric rows, expected {expected_records}")
        if data["max_abs"] is None or data["max_abs"] > tol:
            failures.append(f"{name} max_abs {data['max_abs']} exceeds {tol}")
    if len(rf_u) < 3:
        failures.append("RF-U extraction has fewer than three frame rows")
    rf_by_frame = by_frame(rf_u)
    for tag in ["F1_equilibrated", "F3_release_last"]:
        if tag not in rf_by_frame:
            failures.append(f"{tag} missing from RF-U extraction")
    checkpoint_row = rf_by_frame.get("F1_equilibrated") or rf_by_frame.get("F3_release_last")
    if checkpoint_row:
        u2 = finite_or_none(checkpoint_row.get("top_u2_mean"))
        if u2 is None or abs(u2 - CHECKPOINT_U2) > 1.0e-8:
            failures.append(f"checkpoint U2 not reached: {u2}")
    for row in rf_u:
        rf2 = finite_or_none(row.get("top_rf2_sum"))
        if rf2 is None:
            failures.append(f"RF2 is not finite for {row.get('frame_tag')}")
    if "F1_equilibrated" in rf_by_frame and "F3_release_last" in rf_by_frame:
        rf1 = finite_or_none(rf_by_frame["F1_equilibrated"].get("top_rf2_sum"))
        rf3 = finite_or_none(rf_by_frame["F3_release_last"].get("top_rf2_sum"))
        if rf1 is not None and rf3 is not None and rel_change(rf1, rf3) > RF_RELEASE_JUMP_TOL:
            failures.append(f"RF release jump exceeds {RF_RELEASE_JUMP_TOL}: {rel_change(rf1, rf3)}")

    release_h_decrease = int(release.get("equilibrated_vs_released", {}).get("H_decrease_violations", -1))
    release_d_healing = int(release.get("equilibrated_vs_released", {}).get("d_healing_violations", -1))
    if release_h_decrease != 0:
        failures.append(f"H decrease violations = {release_h_decrease}")
    if release_d_healing != 0:
        failures.append(f"d-healing violations = {release_d_healing}")

    frame_rows = read_csv(paths["D3A3_STATE_BY_FRAME.csv"])
    final_rows = [r for r in frame_rows if r.get("frame_tag") == "F3_release_last"]
    final_d = floats(final_rows, "odb_sdv15")
    final_h = floats(final_rows, "odb_sdv16")
    state_reset = (
        not final_d
        or not final_h
        or max(abs(v) for v in final_d) < 1.0e-14
        or max(abs(v) for v in final_h) < 1.0e-14
    )
    if state_reset:
        failures.append("state reset = true")
    spatial_variation_retained = bool(final_d) and (max(final_d) - min(final_d)) > 1.0e-6
    if not spatial_variation_retained:
        failures.append("spatial variation retained = false")

    baseline_phase_l2 = math.sqrt(sum(v * v for v in floats([r for r in frame_rows if r.get("frame_tag") == "F1_equilibrated"], "odb_sdv15")) / expected_records)
    release_phase_l2 = sdv15_release["l2"]
    normalized_phase_adjustment = (
        release_phase_l2 / max(baseline_phase_l2, 1.0e-30)
        if release_phase_l2 is not None
        else float("inf")
    )
    if normalized_phase_adjustment > PHASE_ADJUSTMENT_NORM_TOL:
        failures.append(f"normalized L2 phase adjustment exceeds {PHASE_ADJUSTMENT_NORM_TOL}: {normalized_phase_adjustment}")
    if sdv15_release["max_abs"] is None or sdv15_release["max_abs"] > PHASE_ADJUSTMENT_MAX_TOL:
        failures.append(f"maximum phase adjustment exceeds {PHASE_ADJUSTMENT_MAX_TOL}: {sdv15_release['max_abs']}")

    rec_frames = {row["frame_tag"]: row for row in reconstructed_energy.get("frames", [])}
    for tag in ["F1_equilibrated", "F3_release_last"]:
        frame = rec_frames.get(tag)
        if not frame:
            failures.append(f"reconstructed energy missing for {tag}")
            continue
        if int(frame.get("non_positive_detJ_count", -1)) != 0:
            failures.append(f"non-positive detJ in reconstructed energy for {tag}")
        for key in ["missing_phase_node_values", "missing_sdv12_values", "missing_sdv13_values"]:
            if int(frame.get(key, -1)) != 0:
                failures.append(f"{key} nonzero for {tag}: {frame.get(key)}")
    energy_jump = None
    if "F1_equilibrated" in rec_frames and "F3_release_last" in rec_frames:
        e1 = float(rec_frames["F1_equilibrated"].get("total_reconstructed_internal_energy", float("nan")))
        e3 = float(rec_frames["F3_release_last"].get("total_reconstructed_internal_energy", float("nan")))
        energy_jump = rel_change(e1, e3)
        if not math.isfinite(energy_jump) or energy_jump > ENERGY_JUMP_TOL:
            failures.append(f"reconstructed energy jump exceeds {ENERGY_JUMP_TOL}: {energy_jump}")

    return {
        "transfer_sdv15_error": sdv15_transfer,
        "transfer_sdv16_error": sdv16_transfer,
        "initial_vs_equilibrated_sdv15_delta": sdv15_eq,
        "initial_vs_equilibrated_sdv16_delta": sdv16_eq,
        "equilibrated_vs_released_sdv15_delta": sdv15_release,
        "equilibrated_vs_released_sdv16_delta": sdv16_release,
        "rf_u_rows": len(rf_u),
        "energy": energy,
        "reconstructed_energy": reconstructed_energy,
        "release_jump": release,
        "checkpoint_U2_target": CHECKPOINT_U2,
        "normalized_L2_phase_adjustment": normalized_phase_adjustment,
        "maximum_phase_adjustment": sdv15_release["max_abs"],
        "RF_release_jump": (
            rel_change(finite_or_none(rf_by_frame["F1_equilibrated"].get("top_rf2_sum")), finite_or_none(rf_by_frame["F3_release_last"].get("top_rf2_sum")))
            if "F1_equilibrated" in rf_by_frame and "F3_release_last" in rf_by_frame
            and finite_or_none(rf_by_frame["F1_equilibrated"].get("top_rf2_sum")) is not None
            and finite_or_none(rf_by_frame["F3_release_last"].get("top_rf2_sum")) is not None
            else None
        ),
        "reconstructed_energy_jump": energy_jump,
        "H_decrease_violations": release_h_decrease,
        "d_healing_violations": release_d_healing,
        "state_reset": state_reset,
        "spatial_variation_retained": spatial_variation_retained,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r2"))
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--tol", type=float, default=DEFAULT_TOL)
    args = parser.parse_args()

    failures = []
    static_path = args.target_dir / "D3A3_STATIC_VALIDATION.json"
    if not static_path.exists():
        failures.append("D3A3_STATIC_VALIDATION.json missing")
        static = {}
    else:
        static = read_json(static_path)
        if static.get("classification") != "stage_d3a3_static_validation_pass":
            failures.append("static validation did not pass")

    completed = {} if args.static_only else validate_completed(args.target_dir, failures, args.tol)
    classification = (
        "stage_d3a3_static_validation_pass"
        if not failures and args.static_only
        else ("stage_d3a3_full_target_ingestion_pass" if not failures else "stage_d3a3_state_ingestion_fail")
    )
    status = {
        "classification": classification,
        "D3A3_ok": not failures and not args.static_only,
        "static_only": args.static_only,
        "tolerance": args.tol,
        "static": static,
        "completed": completed,
        "failures": failures,
    }
    args.target_dir.mkdir(parents=True, exist_ok=True)
    (args.target_dir / "D3A3_STATUS.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if status["D3A3_ok"]:
        (args.target_dir / "D3A3.ok").write_text("stage_d3a3_full_target_ingestion_pass\n", encoding="utf-8")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
