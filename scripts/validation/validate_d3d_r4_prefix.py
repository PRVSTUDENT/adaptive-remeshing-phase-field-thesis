#!/usr/bin/env python3
"""Compare D3D prefix endpoint against accepted R4 F3 release state."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


EXPECTED_IPS = 25600
EXPECTED_NODES = 6601
EXPECTED_TOP_NODES = 81
SDV_TOL = 1.0e-8
PHASE_TOL = 1.0e-8
U2_TOL = 1.0e-8
RF_REL_TOL = 1.0e-4
ENERGY_REL_TOL = 1.0e-4


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
        key = tuple(int(row[k]) for k in key_fields)
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


def load_d3d_phase_f3(phase_path: Path):
    """Load recovered nodal phase at F3 from long or wide format."""
    rows = read_csv(phase_path)
    if not rows:
        return {}
    # Long recovery format used by the D3D extractor copy.
    if "recovered_d_mean" in rows[0] and "frame_tag" in rows[0]:
        return {
            int(r["node"]): float(r["recovered_d_mean"])
            for r in rows
            if r.get("frame_tag") == "F3_release_last"
        }
    # Explicit wide format only if present.
    if "d_F3" in rows[0]:
        return {int(r["node"]): float(r["d_F3"]) for r in rows if r.get("d_F3") not in ("", None)}
    raise ValueError(
        "D3D phase file has neither recovered_d_mean long format nor d_F3 wide format: %s"
        % phase_path
    )


def load_r4_phase_f3(phase_path: Path):
    rows = read_csv(phase_path)
    if not rows:
        return {}
    if "d_F3" in rows[0]:
        return {int(r["node"]): float(r["d_F3"]) for r in rows if r.get("d_F3") not in ("", None)}
    if "recovered_d_mean" in rows[0] and "frame_tag" in rows[0]:
        return {
            int(r["node"]): float(r["recovered_d_mean"])
            for r in rows
            if r.get("frame_tag") == "F3_release_last"
        }
    raise ValueError("unsupported R4 phase format: %s" % phase_path)


def validate(d3d_dir: Path, r4_dir: Path):
    failures = []
    d3d_state_path = d3d_dir / "D3D_STATE_BY_FRAME.csv"
    if not d3d_state_path.exists():
        d3d_state_path = d3d_dir / "D3A3_STATE_BY_FRAME.csv"
    r4_state_path = r4_dir / "D3A3_STATE_BY_FRAME.csv"
    if not d3d_state_path.exists():
        failures.append("D3D state-by-frame missing")
    if not r4_state_path.exists():
        failures.append("accepted R4 state-by-frame missing")
    if failures:
        status = {
            "classification": "stage_d3d_r4_prefix_reproduction_fail",
            "D3D_r4_prefix_ok": False,
            "failures": failures,
        }
        write_json(d3d_dir / "D3D_R4_PREFIX_COMPARISON.json", status)
        return status

    d3d_state = read_csv(d3d_state_path)
    r4_state = read_csv(r4_state_path)
    d3d_tag = "F3_release_last"
    r4_tag = "F3_release_last"

    d3d_s15 = floats_by_key(d3d_state, ["element", "uel_integration_point"], "odb_sdv15", d3d_tag)
    r4_s15 = floats_by_key(r4_state, ["element", "uel_integration_point"], "odb_sdv15", r4_tag)
    d3d_s16 = floats_by_key(d3d_state, ["element", "uel_integration_point"], "odb_sdv16", d3d_tag)
    r4_s16 = floats_by_key(r4_state, ["element", "uel_integration_point"], "odb_sdv16", r4_tag)
    s15_max, s15_n = max_abs_diff(d3d_s15, r4_s15)
    s16_max, s16_n = max_abs_diff(d3d_s16, r4_s16)
    if len(d3d_s15) != EXPECTED_IPS or len(r4_s15) != EXPECTED_IPS or s15_n != EXPECTED_IPS:
        failures.append(
            "SDV15 coverage != 25600 (d3d=%s r4=%s compared=%s)"
            % (len(d3d_s15), len(r4_s15), s15_n)
        )
    if len(d3d_s16) != EXPECTED_IPS or len(r4_s16) != EXPECTED_IPS or s16_n != EXPECTED_IPS:
        failures.append(
            "SDV16 coverage != 25600 (d3d=%s r4=%s compared=%s)"
            % (len(d3d_s16), len(r4_s16), s16_n)
        )
    if s15_max is None or s15_max > SDV_TOL:
        failures.append("SDV15 max difference from accepted R4 F3 = %s" % s15_max)
    if s16_max is None or s16_max > SDV_TOL:
        failures.append("SDV16 max difference from accepted R4 F3 = %s" % s16_max)

    phase_max = None
    phase_n = 0
    d3d_phase_path = d3d_dir / "D3D_PHASE_NODE_STATE_BY_FRAME.csv"
    r4_phase_path = r4_dir / "D3A3_R4_PHASE_NODE_STATE_BY_FRAME.csv"
    if not d3d_phase_path.exists():
        failures.append("D3D_PHASE_NODE_STATE_BY_FRAME.csv missing")
    if not r4_phase_path.exists():
        failures.append("accepted R4 phase node state missing")
    if d3d_phase_path.exists() and r4_phase_path.exists():
        try:
            d3d_ph = load_d3d_phase_f3(d3d_phase_path)
            r4_ph = load_r4_phase_f3(r4_phase_path)
        except ValueError as exc:
            failures.append(str(exc))
            d3d_ph, r4_ph = {}, {}
        phase_max, phase_n = max_abs_diff(d3d_ph, r4_ph)
        if len(d3d_ph) != EXPECTED_NODES or len(r4_ph) != EXPECTED_NODES or phase_n != EXPECTED_NODES:
            failures.append(
                "phase node coverage != 6601 (d3d=%s r4=%s compared=%s)"
                % (len(d3d_ph), len(r4_ph), phase_n)
            )
        if phase_max is None or phase_max > PHASE_TOL:
            failures.append("recovered nodal phase max difference = %s" % phase_max)

    d3d_rf_path = d3d_dir / "D3D_TOP_RF_U.csv"
    if not d3d_rf_path.exists():
        d3d_rf_path = d3d_dir / "D3A3_RF_U_CORRECTED.csv"
    r4_rf_path = r4_dir / "D3A3_RF_U_CORRECTED.csv"
    u2_diff = None
    rf_rel = None
    top_nodes = None
    if not d3d_rf_path.exists() or not r4_rf_path.exists():
        failures.append("TOP RF/U evidence missing for prefix comparison")
    else:
        d3d_rf = {r["frame_tag"]: r for r in read_csv(d3d_rf_path)}
        r4_rf = {r["frame_tag"]: r for r in read_csv(r4_rf_path)}
        if d3d_tag not in d3d_rf or r4_tag not in r4_rf:
            failures.append("F3_release_last missing from TOP RF/U tables")
        else:
            top_nodes = int(float(d3d_rf[d3d_tag]["top_node_count"]))
            if top_nodes != EXPECTED_TOP_NODES:
                failures.append("TOP node count at F3 = %s (expected 81)" % top_nodes)
            u2_diff = abs(float(d3d_rf[d3d_tag]["top_u2_mean"]) - float(r4_rf[r4_tag]["top_u2_mean"]))
            rf_rel = rel_diff(float(r4_rf[r4_tag]["top_rf2_sum"]), float(d3d_rf[d3d_tag]["top_rf2_sum"]))
            if u2_diff > U2_TOL:
                failures.append("TOP U2 difference = %s" % u2_diff)
            if rf_rel > RF_REL_TOL:
                failures.append("TOP RF relative difference = %s" % rf_rel)

    energy_rel = None
    d3d_e_path = d3d_dir / "D3D_RECONSTRUCTED_ENERGY_BY_FRAME.json"
    if not d3d_e_path.exists():
        d3d_e_path = d3d_dir / "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json"
    r4_e_path = r4_dir / "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json"
    if not d3d_e_path.exists() or not r4_e_path.exists():
        failures.append("reconstructed-energy evidence missing for prefix comparison")
    else:
        d3d_frames = {f["frame_tag"]: f for f in read_json(d3d_e_path).get("frames", [])}
        r4_frames = {f["frame_tag"]: f for f in read_json(r4_e_path).get("frames", [])}
        if d3d_tag not in d3d_frames or r4_tag not in r4_frames:
            failures.append("F3_release_last missing from reconstructed energy")
        else:
            e1 = float(r4_frames[r4_tag]["total_reconstructed_internal_energy"])
            e2 = float(d3d_frames[d3d_tag]["total_reconstructed_internal_energy"])
            energy_rel = rel_diff(e1, e2)
            if energy_rel > ENERGY_REL_TOL:
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
        "phase_compared_nodes": phase_n,
        "top_u2_difference": u2_diff,
        "top_rf_relative_difference": rf_rel,
        "top_node_count": top_nodes,
        "energy_relative_difference": energy_rel,
        "required_sdv_ips": EXPECTED_IPS,
        "required_phase_nodes": EXPECTED_NODES,
        "required_top_nodes": EXPECTED_TOP_NODES,
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
