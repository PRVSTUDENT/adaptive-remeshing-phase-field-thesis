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
FREE_RES_TOL = 1.0e-8
ACTIVE_BOUND_TOL = 1.0e-10
U2_TOL = 1.0e-8
SEGMENT_U2 = 0.0031
EXPECTED_TOP_NODES = 81
MIN_STEP4_FRAMES = 11
MIN_CONTINUATION_INCREMENTS = 10
EXPECTED_NODES = 6601
EXPECTED_IPS = 25600

REQUIRED_FILES = [
    "D3D_FRAME_MANIFEST.json",
    "D3D_R4_PREFIX_COMPARISON.json",
    "D3D_PER_FRAME_KKT.csv",
    "D3D_PER_FRAME_KKT_SUMMARY.json",
    "D3D_IRREVERSIBILITY_AUDIT.json",
    "D3D_TOP_RF_U.csv",
    "D3D_STATE_BY_FRAME.csv",
    "D3D_PHASE_NODE_STATE_BY_FRAME.csv",
    "D3D_RECONSTRUCTED_ENERGY_BY_FRAME.json",
]


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_continuation(tag: str) -> bool:
    return str(tag).startswith("F4_segment")


def require_int_field(data: dict, key: str, failures: list, label: str):
    if key not in data or data[key] is None:
        failures.append("%s missing required field %s" % (label, key))
        return None
    return int(data[key])


def floats_from_state(state_rows, tag, column):
    out = []
    for row in state_rows:
        if row.get("frame_tag") != tag:
            continue
        val = row.get(column, "")
        if val not in ("", None):
            out.append(float(val))
    return out


def validate(target_dir: Path):
    technical = []
    scientific = []

    missing = [name for name in REQUIRED_FILES if not (target_dir / name).exists()]
    if missing:
        status = {
            "classification": POST_FAIL,
            "D3D_ok": False,
            "failures": ["missing evidence: " + n for n in missing],
        }
        write_json(target_dir / "D3D_STATUS.json", status)
        _write_report(target_dir, status)
        _clear_ok(target_dir)
        return status

    prefix = read_json(target_dir / "D3D_R4_PREFIX_COMPARISON.json")
    kkt_sum = read_json(target_dir / "D3D_PER_FRAME_KKT_SUMMARY.json")
    kkt_rows = read_csv(target_dir / "D3D_PER_FRAME_KKT.csv")
    irr = read_json(target_dir / "D3D_IRREVERSIBILITY_AUDIT.json")
    manifest = read_json(target_dir / "D3D_FRAME_MANIFEST.json")
    rf_rows = read_csv(target_dir / "D3D_TOP_RF_U.csv")
    state_rows = read_csv(target_dir / "D3D_STATE_BY_FRAME.csv")
    energy = read_json(target_dir / "D3D_RECONSTRUCTED_ENERGY_BY_FRAME.json")

    # --- Prefix ---
    if not prefix.get("D3D_r4_prefix_ok", False):
        technical.extend(
            ["prefix: " + f for f in prefix.get("failures", [])] or ["R4 prefix reproduction failed"]
        )

    # --- KKT analysis completeness ---
    if not kkt_sum.get("analysis_complete", False):
        technical.append("KKT analysis incomplete")
        technical.extend(["kkt: " + f for f in kkt_sum.get("failures", [])])

    # --- Irreversibility: never default missing totals to zero ---
    if not irr.get("audit_complete", False):
        technical.append("irreversibility audit incomplete")
        technical.extend(["irr: " + f for f in irr.get("failures", []) or []])
    phase_dec = require_int_field(irr, "phase_decrease_violations", technical, "irreversibility")
    h_dec = require_int_field(irr, "H_decrease_violations", technical, "irreversibility")
    lb_dec = require_int_field(irr, "below_lower_bound_violations", technical, "irreversibility")
    if phase_dec is not None and phase_dec != 0:
        scientific.append("phase decrease violations = %s" % phase_dec)
    if h_dec is not None and h_dec != 0:
        scientific.append("H decrease violations = %s" % h_dec)
    if lb_dec is not None and lb_dec != 0:
        scientific.append("phase below lower-bound violations = %s" % lb_dec)

    # --- Frame manifest / increment count / endpoint ---
    step4_frames = int(manifest.get("step4_frame_count", 0) or 0)
    accepted_inc = int(manifest.get("accepted_continuation_increments", 0) or 0)
    if step4_frames < MIN_STEP4_FRAMES:
        technical.append("Step-4 frames = %s (< %s)" % (step4_frames, MIN_STEP4_FRAMES))
    if accepted_inc < MIN_CONTINUATION_INCREMENTS:
        technical.append(
            "accepted continuation increments = %s (< %s)"
            % (accepted_inc, MIN_CONTINUATION_INCREMENTS)
        )
    first_t = manifest.get("step4_first_time")
    last_t = manifest.get("step4_last_time")
    if first_t is None or abs(float(first_t) - 0.0) > 1.0e-12:
        technical.append("first Step-4 time != 0: %s" % first_t)
    if last_t is None or abs(float(last_t) - 1.0) > 1.0e-8:
        technical.append("last Step-4 time != 1: %s" % last_t)
    end_expected = manifest.get("step4_endpoint_expected_u2")
    if end_expected is None or abs(float(end_expected) - SEGMENT_U2) > U2_TOL:
        technical.append("endpoint expected U2 != 0.0031: %s" % end_expected)

    frames = manifest.get("frames") or []
    step4_manifest = [f for f in frames if f.get("step_name") == "ACTIVE_SET_VALIDITY_SEGMENT"]
    rf_by_tag = {r["frame_tag"]: r for r in rf_rows}
    for f in step4_manifest:
        tag = f["frame_tag"]
        try:
            top_n = int(float(f.get("top_node_count", rf_by_tag.get(tag, {}).get("top_node_count", -1))))
        except (TypeError, ValueError):
            top_n = -1
        if top_n != EXPECTED_TOP_NODES:
            technical.append("%s TOP node count = %s" % (tag, top_n))
        try:
            expected = float(f["expected_top_u2"])
            actual = float(f.get("actual_top_u2_mean", rf_by_tag.get(tag, {}).get("top_u2_mean")))
        except (TypeError, ValueError, KeyError):
            technical.append("%s TOP U2 missing/non-numeric" % tag)
            continue
        if abs(actual - expected) > U2_TOL:
            technical.append("%s TOP U2 actual %s vs prescribed %s" % (tag, actual, expected))
        rf_val = f.get("top_rf2_sum", rf_by_tag.get(tag, {}).get("top_rf2_sum"))
        try:
            rf_f = float(rf_val)
            if not math.isfinite(rf_f):
                technical.append("%s nonfinite TOP RF" % tag)
        except (TypeError, ValueError):
            technical.append("%s nonfinite/missing TOP RF" % tag)

    # Endpoint from RF table as well.
    end_tags = [f["frame_tag"] for f in step4_manifest if f["frame_tag"] == "F4_segment_end"]
    if not end_tags and step4_manifest:
        end_tags = [step4_manifest[-1]["frame_tag"]]
    for tag in end_tags:
        row = rf_by_tag.get(tag)
        if not row:
            technical.append("endpoint RF row missing for %s" % tag)
            continue
        if abs(float(row["top_u2_mean"]) - SEGMENT_U2) > U2_TOL:
            technical.append("endpoint TOP U2 mismatch = %s" % row["top_u2_mean"])

    # --- Per-frame KKT on continuation only ---
    mult_below = 0
    free_res_fail = 0
    for row in kkt_rows:
        tag = row.get("frame_tag", "")
        if not is_continuation(tag):
            continue
        try:
            free_res = float(row.get("free_residual_inf", "nan"))
            min_mult = float(row.get("minimum_active_multiplier", "nan"))
            bound = float(row.get("active_bound_error", "nan"))
            node_cov = int(float(row.get("node_coverage", 0)))
            ip_cov = int(float(row.get("ip_coverage", 0)))
            detj = int(float(row.get("non_positive_detJ", 0) or 0))
        except (TypeError, ValueError):
            technical.append("non-numeric KKT row for %s" % tag)
            continue
        if node_cov != EXPECTED_NODES or ip_cov != EXPECTED_IPS:
            technical.append("%s coverage node/ip = %s/%s" % (tag, node_cov, ip_cov))
        if detj != 0:
            technical.append("%s non-positive detJ = %s" % (tag, detj))
        if free_res > FREE_RES_TOL:
            free_res_fail += 1
            technical.append("%s free residual = %s" % (tag, free_res))
        if bound > ACTIVE_BOUND_TOL:
            technical.append("%s active bound error = %s" % (tag, bound))
        if min_mult < ACTIVE_MULT_TOL:
            mult_below += 1
            scientific.append("%s minimum active multiplier = %s" % (tag, min_mult))

    # --- State reset / spatial variation at endpoint ---
    end_tag = end_tags[0] if end_tags else None
    if end_tag:
        final_d = floats_from_state(state_rows, end_tag, "odb_sdv15")
        final_h = floats_from_state(state_rows, end_tag, "odb_sdv16")
        state_reset = (
            not final_d
            or not final_h
            or max(abs(v) for v in final_d) < 1.0e-14
            or max(abs(v) for v in final_h) < 1.0e-14
        )
        if state_reset:
            technical.append("state reset = true")
        spatial_variation_retained = bool(final_d) and (max(final_d) - min(final_d)) > 1.0e-6
        if not spatial_variation_retained:
            technical.append("spatial variation retained = false")
        if len(final_d) != EXPECTED_IPS or len(final_h) != EXPECTED_IPS:
            technical.append(
                "endpoint IP coverage sdv15/sdv16 = %s/%s" % (len(final_d), len(final_h))
            )
    else:
        state_reset = True
        spatial_variation_retained = False
        technical.append("endpoint frame tag missing for state-reset audit")

    # Energy presence (malformed structure).
    if "frames" not in energy:
        technical.append("reconstructed energy missing frames list")

    # Classification
    if technical:
        classification = POST_FAIL
    elif scientific:
        classification = UPDATE
    else:
        classification = PASS

    failures = technical + scientific
    candidates_path = target_dir / "D3D_ACTIVE_MULTIPLIER_CANDIDATES.csv"
    candidates = read_csv(candidates_path) if candidates_path.exists() else []

    status = {
        "classification": classification,
        "D3D_ok": classification == PASS,
        "failures": failures,
        "technical_failures": technical,
        "scientific_failures": scientific,
        "prefix": {
            "D3D_r4_prefix_ok": prefix.get("D3D_r4_prefix_ok"),
            "failures": prefix.get("failures"),
        },
        "kkt_summary": {
            "analysis_complete": kkt_sum.get("analysis_complete"),
            "continuation_frames_evaluated": kkt_sum.get("continuation_frames_evaluated"),
            "continuation_frames_kkt_ok": kkt_sum.get("continuation_frames_kkt_ok"),
            "first_continuation_frame_with_negative_multiplier": kkt_sum.get(
                "first_continuation_frame_with_negative_multiplier"
            ),
            "most_negative_continuation_multiplier": kkt_sum.get(
                "most_negative_continuation_multiplier"
            ),
            "maximum_free_residual": kkt_sum.get("maximum_free_residual"),
            "maximum_active_bound_error": kkt_sum.get("maximum_active_bound_error"),
        },
        "phase_decrease_violations": phase_dec,
        "H_decrease_violations": h_dec,
        "below_lower_bound_violations": lb_dec,
        "frames_with_active_multiplier_below_tol": mult_below,
        "free_residual_failure_frames": free_res_fail,
        "step4_frame_count": step4_frames,
        "accepted_continuation_increments": accepted_inc,
        "state_reset": state_reset,
        "spatial_variation_retained": spatial_variation_retained,
        "first_frame_with_negative_active_multiplier": kkt_sum.get(
            "first_continuation_frame_with_negative_multiplier"
        ),
        "most_negative_active_multiplier": kkt_sum.get("most_negative_continuation_multiplier"),
    }
    write_json(target_dir / "D3D_STATUS.json", status)
    _write_report(target_dir, status)

    if classification == PASS:
        (target_dir / "D3D.ok").write_text(PASS + "\n", encoding="utf-8")
    else:
        _clear_ok(target_dir)

    if classification == UPDATE:
        write_json(
            target_dir / "D3D_ACTIVE_SET_UPDATE_REQUIRED.json",
            {
                "classification": UPDATE,
                "reason": scientific,
                "first_frame_with_negative_active_multiplier": status[
                    "first_frame_with_negative_active_multiplier"
                ],
                "most_negative_active_multiplier": status["most_negative_active_multiplier"],
                "phase_decrease_violations": phase_dec,
                "H_decrease_violations": h_dec,
                "below_lower_bound_violations": lb_dec,
                "candidates": candidates,
            },
        )
    elif (target_dir / "D3D_ACTIVE_SET_UPDATE_REQUIRED.json").exists():
        (target_dir / "D3D_ACTIVE_SET_UPDATE_REQUIRED.json").unlink()

    return status


def _clear_ok(target_dir: Path):
    ok = target_dir / "D3D.ok"
    if ok.exists():
        ok.unlink()


def _write_report(target_dir: Path, status: dict):
    report = [
        "# D3D Active-Set Validity Segment Report",
        "",
        "- Classification: `%s`" % status.get("classification"),
        "- D3D.ok: `%s`" % status.get("D3D_ok"),
        "",
        "## Failures",
        "",
    ]
    failures = status.get("failures") or []
    if failures:
        report.extend("- %s" % f for f in failures)
    else:
        report.append("- none")
    report.append("")
    (target_dir / "D3D_REPORT.md").write_text("\n".join(report), encoding="utf-8")


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
