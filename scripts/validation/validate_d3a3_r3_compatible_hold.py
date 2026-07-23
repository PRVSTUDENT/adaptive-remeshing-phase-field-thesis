#!/usr/bin/env python3
"""Validate D3A3-R3 compatible active-set release-hold outputs."""

import argparse
import csv
import json
import math
from pathlib import Path


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
    return {"count": len(values), "l2": math.sqrt(sum(v * v for v in values) / len(values)), "max_abs": max(abs(v) for v in values)}


def rel_change(a, b):
    return abs(b - a) / max(abs(a), abs(b), 1.0e-30)


def validate(target_dir, d3a4_dir):
    failures = []
    required = [
        "D3A3_TRANSFER_VS_ODB.csv",
        "D3A3_STATE_BY_FRAME.csv",
        "D3A3_RF_U_CORRECTED.csv",
        "D3A3_RELEASE_JUMP.json",
        "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json",
    ]
    for name in required:
        if not (target_dir / name).exists():
            failures.append(name + " missing")
    if failures:
        return {"classification": "stage_d3a3_r3_ingestion_fail", "failures": failures, "D3A3_ok": False}

    transfer = read_csv(target_dir / "D3A3_TRANSFER_VS_ODB.csv")
    state = read_csv(target_dir / "D3A3_STATE_BY_FRAME.csv")
    rf = read_csv(target_dir / "D3A3_RF_U_CORRECTED.csv")
    release = read_json(target_dir / "D3A3_RELEASE_JUMP.json")
    energy = read_json(target_dir / "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json")
    active = read_csv(d3a4_dir / "D3A4_ACTIVE_SET_BY_NODE.csv")

    expected_ip = 6400 * 4
    sdv15 = metric(floats(transfer, "sdv15_error"))
    sdv16 = metric(floats(transfer, "sdv16_error"))
    if sdv15["count"] != expected_ip or sdv15["max_abs"] is None or sdv15["max_abs"] > 1.0e-8:
        failures.append("SDV15 compatible-transfer error fails: %s" % sdv15)
    if sdv16["count"] != expected_ip or sdv16["max_abs"] is None or sdv16["max_abs"] > 1.0e-8:
        failures.append("SDV16 compatible-transfer error fails: %s" % sdv16)

    rf_by = {row["frame_tag"]: row for row in rf}
    for tag in ["F1_equilibrated", "F3_release_last"]:
        row = rf_by.get(tag)
        if not row:
            failures.append(tag + " missing in TOP RF/U")
            continue
        if int(float(row.get("top_node_count", 0))) != 81:
            failures.append(tag + " TOP node count != 81")
        vals = [float(row["top_u2_mean"]), float(row["top_u2_min"]), float(row["top_u2_max"])]
        if any(abs(v - CHECKPOINT_U2) > 1.0e-8 for v in vals):
            failures.append(tag + " TOP U2 checkpoint mismatch")
        if not math.isfinite(float(row["top_rf2_sum"])):
            failures.append(tag + " TOP RF2 nonfinite")
    if "F1_equilibrated" in rf_by and "F3_release_last" in rf_by:
        rf_jump = rel_change(float(rf_by["F1_equilibrated"]["top_rf2_sum"]), float(rf_by["F3_release_last"]["top_rf2_sum"]))
        if rf_jump > 0.05:
            failures.append("RF release jump exceeds 5%: %s" % rf_jump)
    else:
        rf_jump = None

    jump = release.get("equilibrated_vs_released", {})
    if int(jump.get("H_decrease_violations", -1)) != 0:
        failures.append("H decrease violations = %s" % jump.get("H_decrease_violations"))
    if int(jump.get("d_healing_violations", -1)) != 0:
        failures.append("d decrease violations from Step 2 to Step 3 = %s" % jump.get("d_healing_violations"))

    rec = {row["frame_tag"]: row for row in energy.get("frames", [])}
    energy_jump = None
    if "F1_equilibrated" in rec and "F3_release_last" in rec:
        e1 = float(rec["F1_equilibrated"]["total_reconstructed_internal_energy"])
        e3 = float(rec["F3_release_last"]["total_reconstructed_internal_energy"])
        energy_jump = rel_change(e1, e3)
        if energy_jump > 0.05:
            failures.append("reconstructed energy release jump exceeds 5%: %s" % energy_jump)
    for tag in ["F1_equilibrated", "F3_release_last"]:
        frame = rec.get(tag, {})
        for key in ["missing_phase_node_values", "missing_sdv12_values", "missing_sdv13_values", "non_positive_detJ_count"]:
            if int(frame.get(key, -1)) != 0:
                failures.append("%s nonzero for %s: %s" % (key, tag, frame.get(key)))

    state_f1 = {(int(r["element"]), int(r["uel_integration_point"])): float(r["odb_sdv15"]) for r in state if r["frame_tag"] == "F1_equilibrated"}
    state_f3 = {(int(r["element"]), int(r["uel_integration_point"])): float(r["odb_sdv15"]) for r in state if r["frame_tag"] == "F3_release_last"}
    phase_diffs = [state_f3[k] - state_f1[k] for k in state_f1 if k in state_f3]
    phase_adjust = metric(phase_diffs)
    if phase_adjust["max_abs"] is None or phase_adjust["max_abs"] > 0.01:
        failures.append("maximum phase adjustment exceeds 0.01: %s" % phase_adjust["max_abs"])

    status = {
        "classification": "stage_d3a3_r3_compatible_release_pass" if not failures else "stage_d3a3_r3_active_set_release_fail",
        "D3A3_R3_ok": not failures,
        "D3A3_ok": not failures,
        "failures": failures,
        "transfer_sdv15_error": sdv15,
        "transfer_sdv16_error": sdv16,
        "RF_release_jump": rf_jump,
        "reconstructed_energy_release_jump": energy_jump,
        "phase_adjustment": phase_adjust,
        "active_nodes_expected": sum(1 for row in active if row["active_lower_bound"].lower() == "true"),
    }
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r3_compatible"))
    parser.add_argument("--d3a4-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/compatibility_projection_d3a4"))
    args = parser.parse_args()
    status = validate(args.target_dir, args.d3a4_dir)
    write_json(args.target_dir / "D3A3_R3_STATUS.json", status)
    if status["D3A3_ok"]:
        (args.target_dir / "D3A3_R3.ok").write_text("stage_d3a3_r3_compatible_release_pass\n", encoding="utf-8")
        (args.target_dir / "D3A3.ok").write_text("stage_d3a3_r3_compatible_release_pass\n", encoding="utf-8")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["D3A3_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
