#!/usr/bin/env python3
"""Validate D3A3-R3 compatible active-set release-hold outputs.

Creates D3A3_R3.ok and D3A3.ok only when every scientific gate passes.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


CHECKPOINT_U2 = 0.003000000026077032
EXPECTED_NODES = 6601
EXPECTED_ACTIVE = 1880
EXPECTED_FREE = 4721
EXPECTED_IP = 6400 * 4
ACTIVE_PHASE_DRIFT_TOL = 1.0e-10
FREE_RESIDUAL_TOL = 1.0e-8
ACTIVE_MULTIPLIER_TOL = -1.0e-8
ACTIVE_BOUND_ERROR_TOL = 1.0e-10
PHASE_ADJUSTMENT_MAX_TOL = 0.01
RF_RELEASE_JUMP_TOL = 0.05
ENERGY_JUMP_TOL = 0.05
PASS_CLASSIFICATION = "stage_d3a3_r3_compatible_release_pass"
FAIL_CLASSIFICATION = "stage_d3a3_r3_active_set_release_fail"
KKT_FAIL_CLASSIFICATION = "stage_d3a3_r3_fixed_state_needs_reprojection"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bool_value(value):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "1", "yes"):
        return True
    if text in ("false", "0", "no"):
        return False
    raise ValueError("cannot parse boolean: %r" % value)


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


def rel_change(a, b):
    return abs(b - a) / max(abs(a), abs(b), 1.0e-30)


def write_report(path: Path, status: dict):
    lines = [
        "# D3A3-R3 Compatible Hold Validation Report",
        "",
        "- Classification: `%s`" % status.get("classification"),
        "- D3A3_R3.ok: `%s`" % status.get("D3A3_R3_ok"),
        "- D3A3.ok: `%s`" % status.get("D3A3_ok"),
        "",
        "## Scientific gates",
        "",
        "- Active-node phase drift max abs: `%s` (tol %s)"
        % (status.get("active_node_phase_drift_max_abs"), ACTIVE_PHASE_DRIFT_TOL),
        "- F3 d decrease from F1 violations: `%s`" % status.get("F3_d_decrease_from_F1_violations"),
        "- F3 below original lower-bound violations: `%s`" % status.get("F3_below_lower_bound_violations"),
        "- H decrease violations: `%s`" % status.get("H_decrease_violations"),
        "- Free residual infinity norm: `%s` (tol %s)"
        % (status.get("free_set_residual_infinity_norm"), FREE_RESIDUAL_TOL),
        "- Minimum active multiplier: `%s` (tol %s)"
        % (status.get("minimum_active_set_multiplier"), ACTIVE_MULTIPLIER_TOL),
        "- Active-node bound error: `%s` (tol %s)"
        % (status.get("active_node_bound_error"), ACTIVE_BOUND_ERROR_TOL),
        "- State reset: `%s`" % status.get("state_reset"),
        "- Spatial variation retained: `%s`" % status.get("spatial_variation_retained"),
        "- Maximum phase adjustment: `%s` (tol %s)"
        % (status.get("maximum_phase_adjustment"), PHASE_ADJUSTMENT_MAX_TOL),
        "- RF release jump: `%s` (tol %s)" % (status.get("RF_release_jump"), RF_RELEASE_JUMP_TOL),
        "- Reconstructed energy release jump: `%s` (tol %s)"
        % (status.get("reconstructed_energy_release_jump"), ENERGY_JUMP_TOL),
        "",
        "## Failures",
        "",
    ]
    failures = status.get("failures") or []
    if not failures:
        lines.append("- none")
    else:
        for item in failures:
            lines.append("- %s" % item)
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def evaluate_active_free_gates(node_rows, expected_nodes=None, expected_active=None, expected_free=None):
    """Evaluate active/free lower-bound and drift gates on phase-node rows.

    Each row must provide:
      active_lower_bound, d_F1, d_F3, d_lower_bound, F3_minus_F1, F3_minus_lower_bound
    """
    if expected_nodes is None:
        expected_nodes = EXPECTED_NODES
    if expected_active is None:
        expected_active = EXPECTED_ACTIVE
    if expected_free is None:
        expected_free = EXPECTED_FREE
    failures = []
    active_rows = [row for row in node_rows if bool_value(row["active_lower_bound"])]
    free_rows = [row for row in node_rows if not bool_value(row["active_lower_bound"])]
    if len(node_rows) != expected_nodes:
        failures.append("phase node coverage = %s expected %s" % (len(node_rows), expected_nodes))
    if len(active_rows) != expected_active:
        failures.append("active nodes = %s expected %s" % (len(active_rows), expected_active))
    if len(free_rows) != expected_free:
        failures.append("free nodes = %s expected %s" % (len(free_rows), expected_free))

    active_drift = []
    f3_decrease_violations = 0
    f3_below_lb_violations = 0
    for row in node_rows:
        d_f1 = float(row["d_F1"])
        d_f3 = float(row["d_F3"])
        lb = float(row["d_lower_bound"])
        delta = d_f3 - d_f1
        if bool_value(row["active_lower_bound"]):
            active_drift.append(abs(delta))
        if delta < -1.0e-10:
            f3_decrease_violations += 1
        if d_f3 < lb - 1.0e-10:
            f3_below_lb_violations += 1

    active_drift_max = max(active_drift) if active_drift else None
    if active_drift_max is None or active_drift_max > ACTIVE_PHASE_DRIFT_TOL:
        failures.append("active-node phase drift = %s > %s" % (active_drift_max, ACTIVE_PHASE_DRIFT_TOL))
    if f3_decrease_violations != 0:
        failures.append("F3 d decrease from F1 violations = %s" % f3_decrease_violations)
    if f3_below_lb_violations != 0:
        failures.append("F3 below original lower-bound violations = %s" % f3_below_lb_violations)

    return {
        "failures": failures,
        "active_node_phase_drift_max_abs": active_drift_max,
        "F3_d_decrease_from_F1_violations": f3_decrease_violations,
        "F3_below_lower_bound_violations": f3_below_lb_violations,
        "active_nodes": len(active_rows),
        "free_nodes": len(free_rows),
        "all_nodes": len(node_rows),
    }


def evaluate_kkt_gates(kkt):
    failures = []
    free_res = float(kkt.get("free_set_residual_infinity_norm", float("inf")))
    min_mult = float(kkt.get("minimum_active_set_multiplier", float("-inf")))
    bound_err = float(kkt.get("active_node_bound_error", float("inf")))
    if free_res > FREE_RESIDUAL_TOL:
        failures.append("free-node residual infinity norm = %s > %s" % (free_res, FREE_RESIDUAL_TOL))
    if min_mult < ACTIVE_MULTIPLIER_TOL:
        failures.append("minimum active multiplier = %s < %s" % (min_mult, ACTIVE_MULTIPLIER_TOL))
    if bound_err > ACTIVE_BOUND_ERROR_TOL:
        failures.append("active-node bound error = %s > %s" % (bound_err, ACTIVE_BOUND_ERROR_TOL))
    if kkt.get("classification") == KKT_FAIL_CLASSIFICATION or not kkt.get("D3A3_R3_fixed_state_kkt_ok", False):
        # Preserve analyzer failures unless already covered.
        for item in kkt.get("failures") or []:
            if item not in failures:
                failures.append(item)
    return {
        "failures": failures,
        "free_set_residual_infinity_norm": free_res,
        "minimum_active_set_multiplier": min_mult,
        "active_node_bound_error": bound_err,
        "kkt_classification": kkt.get("classification"),
    }


def validate(target_dir: Path, d3a4_dir: Path):
    failures = []
    required = [
        "D3A3_TRANSFER_VS_ODB.csv",
        "D3A3_STATE_BY_FRAME.csv",
        "D3A3_RF_U_CORRECTED.csv",
        "D3A3_RELEASE_JUMP.json",
        "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json",
        "D3A3_R3_ACTIVE_NODE_STATE.csv",
        "D3A3_R3_FREE_NODE_STATE.csv",
        "D3A3_R3_PHASE_NODE_STATE_BY_FRAME.csv",
        "D3A3_R3_LOWER_BOUND_AUDIT.json",
        "D3A3_R3_F1_KKT_METRICS.json",
        "D3A3_R3_F1_RESIDUAL_BY_NODE.csv",
    ]
    for name in required:
        if not (target_dir / name).exists():
            failures.append(name + " missing")
    if failures:
        status = {
            "classification": "stage_d3a3_r3_ingestion_fail",
            "failures": failures,
            "D3A3_R3_ok": False,
            "D3A3_ok": False,
        }
        return status

    transfer = read_csv(target_dir / "D3A3_TRANSFER_VS_ODB.csv")
    state = read_csv(target_dir / "D3A3_STATE_BY_FRAME.csv")
    rf = read_csv(target_dir / "D3A3_RF_U_CORRECTED.csv")
    release = read_json(target_dir / "D3A3_RELEASE_JUMP.json")
    energy = read_json(target_dir / "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json")
    phase_nodes = read_csv(target_dir / "D3A3_R3_PHASE_NODE_STATE_BY_FRAME.csv")
    lb_audit = read_json(target_dir / "D3A3_R3_LOWER_BOUND_AUDIT.json")
    kkt = read_json(target_dir / "D3A3_R3_F1_KKT_METRICS.json")
    active = read_csv(d3a4_dir / "D3A4_ACTIVE_SET_BY_NODE.csv")

    sdv15 = metric(floats(transfer, "sdv15_error"))
    sdv16 = metric(floats(transfer, "sdv16_error"))
    if sdv15["count"] != EXPECTED_IP or sdv15["max_abs"] is None or sdv15["max_abs"] > 1.0e-8:
        failures.append("SDV15 compatible-transfer error fails: %s" % sdv15)
    if sdv16["count"] != EXPECTED_IP or sdv16["max_abs"] is None or sdv16["max_abs"] > 1.0e-8:
        failures.append("SDV16 compatible-transfer error fails: %s" % sdv16)
    # EXPECTED_* are module attributes so synthetic tests can patch them.

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
        rf_jump = rel_change(
            float(rf_by["F1_equilibrated"]["top_rf2_sum"]),
            float(rf_by["F3_release_last"]["top_rf2_sum"]),
        )
        if rf_jump > RF_RELEASE_JUMP_TOL:
            failures.append("RF release jump exceeds 5%: %s" % rf_jump)
    else:
        rf_jump = None

    jump = release.get("equilibrated_vs_released", {})
    h_decrease = int(jump.get("H_decrease_violations", -1))
    if h_decrease != 0:
        failures.append("H decrease violations = %s" % h_decrease)

    # Prefer explicit phase-node F3-vs-F1 decrease count; keep release-jump as backup signal.
    if int(jump.get("d_healing_violations", -1)) not in (0, -1) and int(jump.get("d_healing_violations", -1)) != 0:
        # Still recorded via phase-node gate; do not double-fail unless phase file missing later.
        pass

    rec = {row["frame_tag"]: row for row in energy.get("frames", [])}
    energy_jump = None
    if "F1_equilibrated" in rec and "F3_release_last" in rec:
        e1 = float(rec["F1_equilibrated"]["total_reconstructed_internal_energy"])
        e3 = float(rec["F3_release_last"]["total_reconstructed_internal_energy"])
        energy_jump = rel_change(e1, e3)
        if energy_jump > ENERGY_JUMP_TOL:
            failures.append("reconstructed energy release jump exceeds 5%: %s" % energy_jump)
    for tag in ["F1_equilibrated", "F3_release_last"]:
        frame = rec.get(tag, {})
        for key in ["missing_phase_node_values", "missing_sdv12_values", "missing_sdv13_values", "non_positive_detJ_count"]:
            if int(frame.get(key, -1)) != 0:
                failures.append("%s nonzero for %s: %s" % (key, tag, frame.get(key)))

    state_f1 = {
        (int(r["element"]), int(r["uel_integration_point"])): float(r["odb_sdv15"])
        for r in state
        if r["frame_tag"] == "F1_equilibrated"
    }
    state_f3 = {
        (int(r["element"]), int(r["uel_integration_point"])): float(r["odb_sdv15"])
        for r in state
        if r["frame_tag"] == "F3_release_last"
    }
    phase_diffs = [state_f3[k] - state_f1[k] for k in state_f1 if k in state_f3]
    phase_adjust = metric(phase_diffs)
    if phase_adjust["max_abs"] is None or phase_adjust["max_abs"] > PHASE_ADJUSTMENT_MAX_TOL:
        failures.append("maximum phase adjustment exceeds 0.01: %s" % phase_adjust["max_abs"])

    final_rows = [r for r in state if r.get("frame_tag") == "F3_release_last"]
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

    if lb_audit.get("classification") != "stage_d3a3_r3_lower_bound_audit_pass":
        failures.append("lower-bound audit classification = %s" % lb_audit.get("classification"))
    if int(lb_audit.get("missing_recovered_values", -1)) != 0:
        failures.append("missing recovered phase-node values = %s" % lb_audit.get("missing_recovered_values"))

    af = evaluate_active_free_gates(phase_nodes)
    failures.extend(af["failures"])

    kkt_eval = evaluate_kkt_gates(kkt)
    failures.extend(kkt_eval["failures"])

    kkt_failed = (
        kkt.get("classification") == KKT_FAIL_CLASSIFICATION
        or not kkt.get("D3A3_R3_fixed_state_kkt_ok", False)
        or bool(kkt_eval["failures"])
    )
    if failures and kkt_failed and all(
        any(token in f for token in ("residual", "multiplier", "bound error", "reprojection", "detJ", "node coverage"))
        for f in failures
    ):
        classification = KKT_FAIL_CLASSIFICATION
    elif failures:
        classification = FAIL_CLASSIFICATION
    else:
        classification = PASS_CLASSIFICATION

    status = {
        "classification": classification,
        "D3A3_R3_ok": not failures,
        "D3A3_ok": not failures,
        "failures": failures,
        "transfer_sdv15_error": sdv15,
        "transfer_sdv16_error": sdv16,
        "RF_release_jump": rf_jump,
        "reconstructed_energy_release_jump": energy_jump,
        "phase_adjustment": phase_adjust,
        "maximum_phase_adjustment": phase_adjust["max_abs"],
        "active_nodes_expected": sum(1 for row in active if bool_value(row["active_lower_bound"])),
        "active_node_phase_drift_max_abs": af["active_node_phase_drift_max_abs"],
        "F3_d_decrease_from_F1_violations": af["F3_d_decrease_from_F1_violations"],
        "F3_below_lower_bound_violations": af["F3_below_lower_bound_violations"],
        "H_decrease_violations": h_decrease,
        "free_set_residual_infinity_norm": kkt_eval["free_set_residual_infinity_norm"],
        "minimum_active_set_multiplier": kkt_eval["minimum_active_set_multiplier"],
        "active_node_bound_error": kkt_eval["active_node_bound_error"],
        "state_reset": state_reset,
        "spatial_variation_retained": spatial_variation_retained,
        "lower_bound_audit": lb_audit.get("classification"),
        "kkt_classification": kkt_eval["kkt_classification"],
    }
    return status


def apply_status(target_dir: Path, status: dict):
    write_json(target_dir / "D3A3_R3_STATUS.json", status)
    write_report(target_dir / "D3A3_R3_REPORT.md", status)
    ok_r3 = target_dir / "D3A3_R3.ok"
    ok_all = target_dir / "D3A3.ok"
    if status.get("D3A3_ok"):
        ok_r3.write_text(PASS_CLASSIFICATION + "\n", encoding="utf-8")
        ok_all.write_text(PASS_CLASSIFICATION + "\n", encoding="utf-8")
    else:
        if ok_r3.exists():
            ok_r3.unlink()
        if ok_all.exists():
            ok_all.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r3_compatible"),
    )
    parser.add_argument(
        "--d3a4-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/compatibility_projection_d3a4"),
    )
    args = parser.parse_args()
    status = validate(args.target_dir, args.d3a4_dir)
    apply_status(args.target_dir, status)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["D3A3_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
