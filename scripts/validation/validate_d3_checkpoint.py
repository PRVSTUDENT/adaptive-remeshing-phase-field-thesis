#!/usr/bin/env python3
"""Validate D3A checkpoint extraction evidence."""

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple


EXPECTED_PHYSICAL_ELEMENTS = 3930
MIN_SPATIAL_VARIATION = 1.0e-12


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite_float(value: str, name: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{name} is not finite: {value}")
    return out


def validate(out_dir: Path, provenance_path: Path, job_id: str) -> Dict[str, object]:
    failures = []
    selection = json.loads((out_dir / "D3_CHECKPOINT_SELECTION.json").read_text(encoding="utf-8"))
    energy = json.loads((out_dir / "D3_CHECKPOINT_ENERGY.json").read_text(encoding="utf-8"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    rows = read_csv(out_dir / "D3_CHECKPOINT_STATE.csv")

    seen = set()
    d_values = []
    h_values = []
    for row in rows:
        key = (int(row["element"]), int(row["integration_point"]))
        if key in seen:
            failures.append(f"duplicate element/IP key {key[0]}/{key[1]}")
        seen.add(key)
        try:
            x = finite_float(row["x"], "x")
            y = finite_float(row["y"], "y")
            d = finite_float(row["SDV15_d"], "SDV15_d")
            h = finite_float(row["SDV16_H"], "SDV16_H")
        except Exception as exc:
            failures.append(str(exc))
            continue
        if d < -1.0e-12 or d > 1.0 + 1.0e-12:
            failures.append(f"d out of bounds for {key[0]}/{key[1]}: {d}")
        if h < -1.0e-12:
            failures.append(f"H is negative for {key[0]}/{key[1]}: {h}")
        d_values.append(d)
        h_values.append(h)
    element_count = len(set(k[0] for k in seen))
    if element_count != EXPECTED_PHYSICAL_ELEMENTS:
        failures.append(f"expected {EXPECTED_PHYSICAL_ELEMENTS} physical elements, found {element_count}")
    if len(seen) != len(rows):
        failures.append("state rows contain duplicate element/IP keys")
    if not d_values or max(d_values) - min(d_values) <= MIN_SPATIAL_VARIATION:
        failures.append("SDV15 has no spatial variation")
    if not h_values or max(h_values) - min(h_values) <= MIN_SPATIAL_VARIATION:
        failures.append("SDV16 has no spatial variation")
    if not selection.get("pre_peak"):
        failures.append("selected checkpoint is not clearly pre-peak")
    if abs(float(selection["actual_U2"]) - 0.003) > 2.0e-4:
        failures.append("selected checkpoint is not close enough to target U2=0.003 mm")
    if not math.isfinite(float(selection["checkpoint_RF2"])):
        failures.append("checkpoint RF2 is not finite")
    for name in ["ALLIE", "ALLSE", "ALLWK"]:
        if energy.get(name) is None:
            failures.append(f"energy {name} was not reported")
        elif not math.isfinite(float(energy[name])):
            failures.append(f"energy {name} is not finite")
    if provenance.get("classification") != "stage_d3a0_existing_h0_source_eligible":
        failures.append("source provenance is not eligible")

    coverage = element_count / float(EXPECTED_PHYSICAL_ELEMENTS)
    status = {
        "classification": "stage_d3a_checkpoint_pass" if not failures else "stage_d3a_checkpoint_fail",
        "D3A_ok": not failures,
        "job_id": job_id,
        "odb_readable": True,
        "source_provenance_complete": provenance.get("source_provenance_complete", False),
        "actual_checkpoint_U2": selection.get("actual_U2"),
        "checkpoint_RF2": selection.get("checkpoint_RF2"),
        "checkpoint_RF2_over_H0_peak_RF2": selection.get("checkpoint_RF2_over_H0_peak_RF2"),
        "target_ip_coverage": coverage,
        "state_rows": len(rows),
        "physical_element_count": element_count,
        "max_d": max(d_values) if d_values else None,
        "ip_count_d_ge_0p1": sum(1 for v in d_values if v >= 0.1),
        "ip_count_d_ge_0p5": sum(1 for v in d_values if v >= 0.5),
        "max_H": max(h_values) if h_values else None,
        "failures": failures,
    }
    (out_dir / "D3_CHECKPOINT_STATUS.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not failures:
        (out_dir / "D3A.ok").write_text("", encoding="utf-8")
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--job-id", default="not_submitted")
    args = parser.parse_args()
    status = validate(args.out_dir, args.provenance, args.job_id)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["D3A_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
