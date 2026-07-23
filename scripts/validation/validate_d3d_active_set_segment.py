#!/usr/bin/env python3
"""Final scientific validation for the D3D Route-B active-set segment."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


PASS = "stage_d3d_active_set_segment_pass"
UPDATE = "stage_d3d_active_set_update_required"
POST_FAIL = "stage_d3d_postprocessing_fail"
ACTIVE_MULT_TOL = -1.0e-8


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate(target_dir: Path):
    failures = []
    scientific_update = False
    required = [
        "D3D_R4_PREFIX_COMPARISON.json",
        "D3D_PER_FRAME_KKT_SUMMARY.json",
        "D3D_PER_FRAME_KKT.csv",
    ]
    for name in required:
        if not (target_dir / name).exists():
            failures.append(name + " missing")
    if failures:
        status = {
            "classification": POST_FAIL,
            "D3D_ok": False,
            "failures": failures,
        }
        write_json(target_dir / "D3D_STATUS.json", status)
        return status

    prefix = read_json(target_dir / "D3D_R4_PREFIX_COMPARISON.json")
    kkt_sum = read_json(target_dir / "D3D_PER_FRAME_KKT_SUMMARY.json")
    kkt_rows = read_csv(target_dir / "D3D_PER_FRAME_KKT.csv")

    if not prefix.get("D3D_r4_prefix_ok", False):
        failures.extend(["prefix: " + f for f in prefix.get("failures", [])] or ["R4 prefix reproduction failed"])
        status = {
            "classification": POST_FAIL,
            "D3D_ok": False,
            "failures": failures,
            "prefix": prefix,
            "kkt_summary": kkt_sum,
        }
        write_json(target_dir / "D3D_STATUS.json", status)
        return status

    # Irreversibility if present.
    irr_path = target_dir / "D3D_IRREVERSIBILITY_AUDIT.json"
    phase_dec = 0
    h_dec = 0
    if irr_path.exists():
        irr = read_json(irr_path)
        phase_dec = int(irr.get("phase_decrease_violations", 0))
        h_dec = int(irr.get("H_decrease_violations", 0))
        if phase_dec != 0 or h_dec != 0:
            scientific_update = True
            failures.append("irreversibility phase/H violations = %s/%s" % (phase_dec, h_dec))

    # Per-frame KKT over continuation-ish frames and overall.
    mult_below = 0
    free_res_fail = 0
    for row in kkt_rows:
        tag = row.get("frame_tag", "")
        if tag in ("F0_ingested", "F1_equilibrated", "F2_release_first"):
            continue
        try:
            free_res = float(row.get("free_residual_inf", "nan"))
            min_mult = float(row.get("minimum_active_multiplier", "nan"))
            bound = float(row.get("active_bound_error", "nan"))
        except ValueError:
            failures.append("non-numeric KKT row for %s" % tag)
            continue
        if free_res > 1.0e-8:
            free_res_fail += 1
            failures.append("%s free residual = %s" % (tag, free_res))
        if min_mult < ACTIVE_MULT_TOL:
            mult_below += 1
            scientific_update = True
            failures.append("%s minimum active multiplier = %s" % (tag, min_mult))
        if bound > 1.0e-10:
            failures.append("%s active bound error = %s" % (tag, bound))

    if scientific_update and not any("prefix" in f for f in failures):
        classification = UPDATE
    elif failures:
        classification = POST_FAIL if free_res_fail and not scientific_update else (
            UPDATE if scientific_update else POST_FAIL
        )
    else:
        classification = PASS

    # Refine: pure multiplier/irreversibility issues => UPDATE; coverage/tech => POST_FAIL
    if classification != PASS:
        if scientific_update and free_res_fail == 0 and not any("prefix" in f for f in failures):
            classification = UPDATE
        elif scientific_update:
            classification = UPDATE
        else:
            classification = POST_FAIL

    status = {
        "classification": classification,
        "D3D_ok": classification == PASS,
        "failures": failures,
        "prefix": prefix,
        "kkt_summary": kkt_sum,
        "phase_decrease_violations": phase_dec,
        "H_decrease_violations": h_dec,
        "frames_with_active_multiplier_below_tol": mult_below,
        "first_frame_with_negative_active_multiplier": kkt_sum.get(
            "first_frame_with_negative_active_multiplier"
        ),
        "most_negative_active_multiplier": kkt_sum.get("most_negative_active_multiplier"),
    }
    write_json(target_dir / "D3D_STATUS.json", status)

    report = [
        "# D3D Active-Set Validity Segment Report",
        "",
        "- Classification: `%s`" % classification,
        "- D3D.ok: `%s`" % (classification == PASS),
        "",
        "## Failures",
        "",
    ]
    if failures:
        report.extend("- %s" % f for f in failures)
    else:
        report.append("- none")
    report.append("")
    (target_dir / "D3D_REPORT.md").write_text("\n".join(report), encoding="utf-8")

    if classification == PASS:
        (target_dir / "D3D.ok").write_text(PASS + "\n", encoding="utf-8")
    else:
        if (target_dir / "D3D.ok").exists():
            (target_dir / "D3D.ok").unlink()
    if classification == UPDATE:
        write_json(
            target_dir / "D3D_ACTIVE_SET_UPDATE_REQUIRED.json",
            {
                "classification": UPDATE,
                "reason": failures,
                "first_frame_with_negative_active_multiplier": status[
                    "first_frame_with_negative_active_multiplier"
                ],
                "most_negative_active_multiplier": status["most_negative_active_multiplier"],
            },
        )
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment"),
    )
    args = parser.parse_args()
    status = validate(args.target_dir)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["D3D_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
