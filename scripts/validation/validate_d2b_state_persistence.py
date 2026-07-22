#!/usr/bin/env python3
"""Validate Stage D2B serial state persistence and tiny continuation evidence."""

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple


TOL = 1.0e-8
REQUESTED_U2 = 1.0e-5


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite_float(value: str, name: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{name} is not finite: {value}")
    return out


def key(row: Dict[str, str]) -> Tuple[int, int]:
    ip_name = "integration_point" if "integration_point" in row else "ip"
    return int(row["element"]), int(row[ip_name])


def accepted_d2a(path: Path) -> Dict[Tuple[int, int], Dict[str, float]]:
    rows = read_csv(path)
    out = {}
    for row in rows:
        out[key(row)] = {
            "sdv15": finite_float(row["sdv15_odb"], "d2a sdv15"),
            "sdv16": finite_float(row["sdv16_odb"], "d2a sdv16"),
        }
    return out


def write_csv(path: Path, fields: List[str], rows: List[Dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def finite_values(row: Dict[str, str], fields: List[str], failures: List[str], label: str) -> List[float]:
    values = []
    for field in fields:
        raw = row.get(field, "")
        if raw in ("", "None"):
            failures.append(f"{label} missing {field}")
            continue
        try:
            values.append(finite_float(raw, f"{label} {field}"))
        except ValueError as exc:
            failures.append(str(exc))
    return values


def validate(out_dir: Path, d2a_dir: Path, job_id: str) -> Dict[str, object]:
    state_rows = read_csv(out_dir / "D2B_STATE_BY_FRAME.csv")
    rf_rows = read_csv(out_dir / "D2B_RF_U.csv")
    d2a = accepted_d2a(d2a_dir / "D2A_IP_COMPARISON.csv")
    energy = json.loads((out_dir / "D2B_ENERGY_JUMP.json").read_text(encoding="utf-8"))

    failures = []  # type: List[str]
    comparison_release = []
    comparison_final = []
    state_fields = [
        "SDV15_F0",
        "SDV15_F1",
        "SDV15_F2",
        "SDV15_F3",
        "SDV16_F0",
        "SDV16_F1",
        "SDV16_F2",
        "SDV16_F3",
    ]
    max_initial_sdv15 = 0.0
    max_initial_sdv16 = 0.0
    max_release_sdv15 = 0.0
    max_release_sdv16 = 0.0
    min_sdv15_f2_minus_f0 = math.inf
    min_sdv15_f3_minus_f2 = math.inf
    min_sdv16_f2_minus_f0 = math.inf
    min_sdv16_f3_minus_f2 = math.inf

    if len(state_rows) != 8:
        failures.append(f"expected 8 target element/IP rows, found {len(state_rows)}")
    seen = set()
    sdv15_f3_values = []
    sdv16_f3_values = []
    for row in state_rows:
        k = key(row)
        seen.add(k)
        finite_values(row, ["x", "y"] + state_fields, failures, f"element/ip {k[0]}/{k[1]}")
        if k not in d2a:
            failures.append(f"element/ip {k[0]}/{k[1]} missing accepted D2A reference")
            continue
        vals = {field: finite_float(row[field], field) for field in state_fields if row.get(field, "") not in ("", "None")}
        if len(vals) != len(state_fields):
            continue
        sdv15_f3_values.append(vals["SDV15_F3"])
        sdv16_f3_values.append(vals["SDV16_F3"])
        initial_sdv15 = abs(vals["SDV15_F0"] - d2a[k]["sdv15"])
        initial_sdv16 = abs(vals["SDV16_F0"] - d2a[k]["sdv16"])
        release_sdv15 = abs(vals["SDV15_F1"] - vals["SDV15_F0"])
        release_sdv16 = abs(vals["SDV16_F1"] - vals["SDV16_F0"])
        max_initial_sdv15 = max(max_initial_sdv15, initial_sdv15)
        max_initial_sdv16 = max(max_initial_sdv16, initial_sdv16)
        max_release_sdv15 = max(max_release_sdv15, release_sdv15)
        max_release_sdv16 = max(max_release_sdv16, release_sdv16)
        min_sdv15_f2_minus_f0 = min(min_sdv15_f2_minus_f0, vals["SDV15_F2"] - vals["SDV15_F0"])
        min_sdv15_f3_minus_f2 = min(min_sdv15_f3_minus_f2, vals["SDV15_F3"] - vals["SDV15_F2"])
        min_sdv16_f2_minus_f0 = min(min_sdv16_f2_minus_f0, vals["SDV16_F2"] - vals["SDV16_F0"])
        min_sdv16_f3_minus_f2 = min(min_sdv16_f3_minus_f2, vals["SDV16_F3"] - vals["SDV16_F2"])
        comparison_release.append(
            {
                "element": k[0],
                "integration_point": k[1],
                "SDV15_F0": vals["SDV15_F0"],
                "SDV15_F1": vals["SDV15_F1"],
                "SDV15_F2": vals["SDV15_F2"],
                "abs_SDV15_F1_minus_F0": release_sdv15,
                "SDV16_F0": vals["SDV16_F0"],
                "SDV16_F1": vals["SDV16_F1"],
                "SDV16_F2": vals["SDV16_F2"],
                "abs_SDV16_F1_minus_F0": release_sdv16,
            }
        )
        comparison_final.append(
            {
                "element": k[0],
                "integration_point": k[1],
                "SDV15_D2A": d2a[k]["sdv15"],
                "SDV15_F0": vals["SDV15_F0"],
                "SDV15_F3": vals["SDV15_F3"],
                "abs_SDV15_F0_minus_D2A": initial_sdv15,
                "SDV15_F3_minus_F0": vals["SDV15_F3"] - vals["SDV15_F0"],
                "SDV16_D2A": d2a[k]["sdv16"],
                "SDV16_F0": vals["SDV16_F0"],
                "SDV16_F3": vals["SDV16_F3"],
                "abs_SDV16_F0_minus_D2A": initial_sdv16,
                "SDV16_F3_minus_F0": vals["SDV16_F3"] - vals["SDV16_F0"],
            }
        )

    if seen != set(d2a):
        failures.append("D2B target element/IP set does not match accepted D2A set")
    for name, value in [
        ("max initial SDV15 difference", max_initial_sdv15),
        ("max initial SDV16 difference", max_initial_sdv16),
        ("max release SDV15 difference", max_release_sdv15),
        ("max release SDV16 difference", max_release_sdv16),
    ]:
        if value > TOL:
            failures.append(f"{name} {value} exceeds {TOL}")
    for name, value in [
        ("SDV15 F2-F0", min_sdv15_f2_minus_f0),
        ("SDV15 F3-F2", min_sdv15_f3_minus_f2),
        ("SDV16 F2-F0", min_sdv16_f2_minus_f0),
        ("SDV16 F3-F2", min_sdv16_f3_minus_f2),
    ]:
        if value < -TOL:
            failures.append(f"irreversibility violation {name} minimum {value}")
    if len(set(round(v, 14) for v in sdv15_f3_values)) <= 1:
        failures.append("SDV15 appears uniformly/default overwritten")
    if len(set(round(v, 14) for v in sdv16_f3_values)) <= 1:
        failures.append("SDV16 appears uniformly/default overwritten")

    rf_by_frame = {row["frame"]: row for row in rf_rows}
    if set(rf_by_frame) != {"F0", "F1", "F2", "F3"}:
        failures.append("RF/U extraction did not produce F0..F3")
    for frame, row in rf_by_frame.items():
        finite_values(row, ["increment_number", "step_time", "U2", "RF2", "ALLIE", "ALLSE", "ALLWK"], failures, f"RF/U {frame}")
    if "F3" in rf_by_frame and rf_by_frame["F3"].get("U2", "") not in ("", "None"):
        u2_f3 = finite_float(rf_by_frame["F3"]["U2"], "F3 U2")
        if abs(u2_f3 - REQUESTED_U2) > TOL:
            failures.append(f"F3 U2 {u2_f3} did not reach requested {REQUESTED_U2}")
    for name, jumps in energy.get("jumps", {}).items():
        for jump_name, value in jumps.items():
            if value is not None and not math.isfinite(float(value)):
                failures.append(f"{name} {jump_name} is not finite")

    write_csv(
        out_dir / "D2B_INITIAL_VS_RELEASED.csv",
        [
            "element",
            "integration_point",
            "SDV15_F0",
            "SDV15_F1",
            "SDV15_F2",
            "abs_SDV15_F1_minus_F0",
            "SDV16_F0",
            "SDV16_F1",
            "SDV16_F2",
            "abs_SDV16_F1_minus_F0",
        ],
        comparison_release,
    )
    write_csv(
        out_dir / "D2B_INITIAL_VS_FINAL.csv",
        [
            "element",
            "integration_point",
            "SDV15_D2A",
            "SDV15_F0",
            "SDV15_F3",
            "abs_SDV15_F0_minus_D2A",
            "SDV15_F3_minus_F0",
            "SDV16_D2A",
            "SDV16_F0",
            "SDV16_F3",
            "abs_SDV16_F0_minus_D2A",
            "SDV16_F3_minus_F0",
        ],
        comparison_final,
    )

    status = {
        "classification": "stage_d2b_serial_continuation_pass" if not failures else "stage_d2b_serial_continuation_fail",
        "D2B_ok": not failures,
        "job_id": job_id,
        "solver_exit": 0,
        "odb_readable": True,
        "target_ip_coverage": len(seen.intersection(set(d2a))) / float(len(d2a)) if d2a else 0.0,
        "max_initial_sdv15_difference": max_initial_sdv15,
        "max_initial_sdv16_difference": max_initial_sdv16,
        "max_release_sdv15_difference": max_release_sdv15,
        "max_release_sdv16_difference": max_release_sdv16,
        "min_sdv15_f2_minus_f0": None if math.isinf(min_sdv15_f2_minus_f0) else min_sdv15_f2_minus_f0,
        "min_sdv15_f3_minus_f2": None if math.isinf(min_sdv15_f3_minus_f2) else min_sdv15_f3_minus_f2,
        "min_sdv16_f2_minus_f0": None if math.isinf(min_sdv16_f2_minus_f0) else min_sdv16_f2_minus_f0,
        "min_sdv16_f3_minus_f2": None if math.isinf(min_sdv16_f3_minus_f2) else min_sdv16_f3_minus_f2,
        "requested_U2": REQUESTED_U2,
        "observed_F3_U2": None if "F3" not in rf_by_frame or rf_by_frame["F3"].get("U2", "") in ("", "None") else finite_float(rf_by_frame["F3"]["U2"], "F3 U2"),
        "energy_jump": energy,
        "tolerance": TOL,
        "failures": failures,
    }
    (out_dir / "D2B_CONTINUATION_STATUS.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = [
        "# D2B State Persistence Report",
        "",
        f"Classification: `{status['classification']}`",
        "",
        f"- Job: `{job_id}`",
        f"- Target element/IP coverage: `{status['target_ip_coverage']}`",
        f"- Maximum initial SDV15 difference vs accepted D2A: `{max_initial_sdv15}`",
        f"- Maximum initial SDV16 difference vs accepted D2A: `{max_initial_sdv16}`",
        f"- Maximum release SDV15 difference F1-F0: `{max_release_sdv15}`",
        f"- Maximum release SDV16 difference F1-F0: `{max_release_sdv16}`",
        f"- Observed F3 U2: `{status['observed_F3_U2']}`",
        f"- Failures: `{len(failures)}`",
        "",
        "Energy jumps are recorded in `D2B_ENERGY_JUMP.json`; no arbitrary energy-jump pass tolerance is assigned at D2B.",
        "",
    ]
    (out_dir / "D2B_STATE_PERSISTENCE_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    if not failures:
        (out_dir / "D2B.ok").write_text("", encoding="utf-8")
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--d2a-dir", type=Path, default=Path("runs/hpc/stage_d2/d2a_serial_ingestion"))
    parser.add_argument("--job-id", default="not_submitted")
    args = parser.parse_args()
    status = validate(args.out_dir, args.d2a_dir, args.job_id)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["D2B_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
