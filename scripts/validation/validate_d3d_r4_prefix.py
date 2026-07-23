#!/usr/bin/env python3
"""Compare D3D prefix endpoint against accepted R4 F3 release state."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def floats_by_key(rows, key_fields, value_field, frame_tag):
    out = {}
    for row in rows:
        if row.get("frame_tag") != frame_tag:
            continue
        key = tuple(int(row[k]) if k != "node" else int(row[k]) for k in key_fields)
        out[key] = float(row[value_field])
    return out


def max_abs_diff(a: dict, b: dict):
    keys = set(a) & set(b)
    if not keys:
        return None, 0
    diffs = [abs(a[k] - b[k]) for k in keys]
    return max(diffs), len(keys)


def rel_diff(a, b):
    return abs(b - a) / max(abs(a), abs(b), 1.0e-30)


def validate(d3d_dir: Path, r4_dir: Path):
    failures = []
    d3d_state = read_csv(d3d_dir / "D3A3_STATE_BY_FRAME.csv") if (d3d_dir / "D3A3_STATE_BY_FRAME.csv").exists() else read_csv(d3d_dir / "D3D_STATE_BY_FRAME.csv")
    r4_state = read_csv(r4_dir / "D3A3_STATE_BY_FRAME.csv")

    # Prefer release endpoint frame tags.
    d3d_tag = "F3_release_last"
    r4_tag = "F3_release_last"

    d3d_s15 = floats_by_key(d3d_state, ["element", "uel_integration_point"], "odb_sdv15", d3d_tag)
    r4_s15 = floats_by_key(r4_state, ["element", "uel_integration_point"], "odb_sdv15", r4_tag)
    d3d_s16 = floats_by_key(d3d_state, ["element", "uel_integration_point"], "odb_sdv16", d3d_tag)
    r4_s16 = floats_by_key(r4_state, ["element", "uel_integration_point"], "odb_sdv16", r4_tag)
    s15_max, s15_n = max_abs_diff(d3d_s15, r4_s15)
    s16_max, s16_n = max_abs_diff(d3d_s16, r4_s16)
    if s15_max is None or s15_max > 1.0e-8:
        failures.append("SDV15 max difference from accepted R4 F3 = %s" % s15_max)
    if s16_max is None or s16_max > 1.0e-8:
        failures.append("SDV16 max difference from accepted R4 F3 = %s" % s16_max)

    # Phase recovery comparison if available.
    phase_max = None
    d3d_phase_path = d3d_dir / "D3D_PHASE_NODE_STATE_BY_FRAME.csv"
    r4_phase_path = r4_dir / "D3A3_R4_PHASE_NODE_STATE_BY_FRAME.csv"
    if d3d_phase_path.exists() and r4_phase_path.exists():
        d3d_ph = {
            int(r["node"]): float(r["d_F3"])
            for r in read_csv(d3d_phase_path)
        }
        r4_ph = {
            int(r["node"]): float(r["d_F3"])
            for r in read_csv(r4_phase_path)
        }
        phase_max, _ = max_abs_diff(d3d_ph, r4_ph)
        if phase_max is None or phase_max > 1.0e-8:
            failures.append("recovered nodal phase max difference = %s" % phase_max)

    d3d_rf_path = d3d_dir / "D3D_TOP_RF_U.csv"
    if not d3d_rf_path.exists():
        d3d_rf_path = d3d_dir / "D3A3_RF_U_CORRECTED.csv"
    r4_rf_path = r4_dir / "D3A3_RF_U_CORRECTED.csv"
    d3d_rf = {r["frame_tag"]: r for r in read_csv(d3d_rf_path)}
    r4_rf = {r["frame_tag"]: r for r in read_csv(r4_rf_path)}
    u2_diff = None
    rf_rel = None
    if d3d_tag in d3d_rf and r4_tag in r4_rf:
        u2_diff = abs(float(d3d_rf[d3d_tag]["top_u2_mean"]) - float(r4_rf[r4_tag]["top_u2_mean"]))
        rf_rel = rel_diff(float(r4_rf[r4_tag]["top_rf2_sum"]), float(d3d_rf[d3d_tag]["top_rf2_sum"]))
        if u2_diff > 1.0e-8:
            failures.append("TOP U2 difference = %s" % u2_diff)
        if rf_rel > 1.0e-4:
            failures.append("TOP RF relative difference = %s" % rf_rel)

    energy_rel = None
    d3d_e_path = d3d_dir / "D3D_RECONSTRUCTED_ENERGY_BY_FRAME.json"
    if not d3d_e_path.exists():
        d3d_e_path = d3d_dir / "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json"
    r4_e_path = r4_dir / "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json"
    if d3d_e_path.exists() and r4_e_path.exists():
        d3d_frames = {f["frame_tag"]: f for f in read_json(d3d_e_path).get("frames", [])}
        r4_frames = {f["frame_tag"]: f for f in read_json(r4_e_path).get("frames", [])}
        if d3d_tag in d3d_frames and r4_tag in r4_frames:
            e1 = float(r4_frames[r4_tag]["total_reconstructed_internal_energy"])
            e2 = float(d3d_frames[d3d_tag]["total_reconstructed_internal_energy"])
            energy_rel = rel_diff(e1, e2)
            if energy_rel > 1.0e-4:
                failures.append("reconstructed-energy relative difference = %s" % energy_rel)

    status = {
        "classification": (
            "stage_d3d_r4_prefix_reproduction_pass"
            if not failures
            else "stage_d3d_r4_prefix_reproduction_fail"
        ),
        "D3D_r4_prefix_ok": not failures,
        "failures": failures,
        "sdv15_max_difference": s15_max,
        "sdv16_max_difference": s16_max,
        "sdv15_compared_ips": s15_n,
        "sdv16_compared_ips": s16_n,
        "phase_max_difference": phase_max,
        "top_u2_difference": u2_diff,
        "top_rf_relative_difference": rf_rel,
        "energy_relative_difference": energy_rel,
    }
    write_json(d3d_dir / "D3D_R4_PREFIX_COMPARISON.json", status)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--d3d-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment"),
    )
    parser.add_argument(
        "--r4-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible"),
    )
    args = parser.parse_args()
    status = validate(args.d3d_dir, args.r4_dir)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["D3D_r4_prefix_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
