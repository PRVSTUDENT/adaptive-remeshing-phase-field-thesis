#!/usr/bin/env python3
"""Final D3D-A1H0 scientific classifier."""

import argparse
import csv
import json
import math
from pathlib import Path

PASS = "stage_d3d_a1h0_mechanical_checkpoint_pass"
UPDATE = "stage_d3d_a1h0_actual_history_update_required"
POSTFAIL = "stage_d3d_a1h0_postprocessing_fail"


def csv_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_metrics(target, baseline):
    required = [
        "D3D_A1H0_TRANSFER_VALIDATION.json", "D3D_A1H0_ACTUAL_HISTORY_KKT.json",
        "D3D_A1H0_STATE_BY_FRAME.csv", "D3D_A1H0_PHASE_NODE_STATE_BY_FRAME.csv",
        "D3D_A1H0_TOP_RF_U.csv", "D3D_A1H0_RECONSTRUCTED_ENERGY_BY_FRAME.json",
    ]
    missing = [name for name in required if not (target / name).exists()]
    if missing:
        raise ValueError("missing required evidence: " + ",".join(missing))
    phase = csv_rows(target / "D3D_A1H0_PHASE_NODE_STATE_BY_FRAME.csv")
    state = csv_rows(target / "D3D_A1H0_STATE_BY_FRAME.csv")
    rf = csv_rows(target / "D3D_A1H0_TOP_RF_U.csv")
    kkt = json.loads((target / "D3D_A1H0_ACTUAL_HISTORY_KKT.json").read_text(encoding="utf-8"))
    transfer = json.loads((target / "D3D_A1H0_TRANSFER_VALIDATION.json").read_text(encoding="utf-8"))
    energy = json.loads((target / "D3D_A1H0_RECONSTRUCTED_ENERGY_BY_FRAME.json").read_text(encoding="utf-8"))["frames"]
    base_rf = {r["frame_tag"]: r for r in csv_rows(baseline / "D3D_TOP_RF_U.csv")}["F3_release_last"]
    base_energy = {r["frame_tag"]: r for r in json.loads((baseline / "D3D_RECONSTRUCTED_ENERGY_BY_FRAME.json").read_text(encoding="utf-8"))["frames"]}["F3_release_last"]
    p0 = {int(r["node"]): float(r["recovered_d_mean"]) for r in phase if r["frame_tag"] == "F0_ingested"}
    p1 = {int(r["node"]): float(r["recovered_d_mean"]) for r in phase if r["frame_tag"] == "F1_equilibrated"}
    h0 = {(r["element"], r["uel_integration_point"]): float(r["odb_sdv16"]) for r in state if r["frame_tag"] == "F0_ingested"}
    h1 = {(r["element"], r["uel_integration_point"]): float(r["odb_sdv16"]) for r in state if r["frame_tag"] == "F1_equilibrated"}
    final_rf = {r["frame_tag"]: r for r in rf}["F1_equilibrated"]
    final_energy = {r["frame_tag"]: r for r in energy}["F1_equilibrated"]
    h_delta = [h1[k] - h0[k] for k in h0]
    denom_h = math.sqrt(sum(v * v for v in h0.values())) or 1.0
    endpoint_finite = all(math.isfinite(v) for v in p1.values()) and all(math.isfinite(v) for v in h1.values())
    state_reset = not (
        len(p1) == 6601 and len(h1) == 25600 and endpoint_finite
        and max(abs(v) for v in p1.values()) > 0.0
        and max(abs(v) for v in h1.values()) > 0.0
    )
    return {
        "phase_node_coverage": len(p1), "history_coverage": len(h1),
        "top_node_count": int(final_rf["top_node_count"]),
        "top_u2_error": float(final_rf["top_u2_mean"]) - 0.003000000026077032,
        "top_rf": float(final_rf["top_rf2_sum"]),
        "maximum_phase_drift": max(abs(p1[n] - p0[n]) for n in p0),
        "phase_decrease_violations": sum(p1[n] < p0[n] - 1e-10 for n in p0),
        "H_decrease_violations": sum(v < -1e-10 for v in h_delta),
        "maximum_H_increase": max(h_delta),
        "normalized_L2_H_increase": math.sqrt(sum(v * v for v in h_delta)) / denom_h,
        "relative_top_rf_change": abs(float(final_rf["top_rf2_sum"]) - float(base_rf["top_rf2_sum"])) / max(abs(float(base_rf["top_rf2_sum"])), 1e-30),
        "relative_energy_change": abs(float(final_energy["total_reconstructed_internal_energy"]) - float(base_energy["total_reconstructed_internal_energy"])) / max(abs(float(base_energy["total_reconstructed_internal_energy"])), 1e-30),
        "state_reset": state_reset,
        "endpoint_values_finite": endpoint_finite,
        "phase_range": max(p1.values()) - min(p1.values()),
        "spatial_variation_retained": max(p1.values()) - min(p1.values()) > 1e-6,
        "transfer_validation_pass": transfer.get("classification") == "stage_d3d_a1h0_transfer_pass" and not transfer.get("failures"),
        **kkt,
    }


def classify(m):
    technical = []
    for key, ok in {
        "phase_coverage": m.get("phase_node_coverage") == 6601,
        "H_coverage": m.get("history_coverage") == 25600,
        "top_nodes": m.get("top_node_count") == 81,
        "top_u2": abs(m.get("top_u2_error", float("inf"))) <= 1e-8,
        "top_rf": math.isfinite(m.get("top_rf", float("nan"))),
        "phase_drift": m.get("maximum_phase_drift", float("inf")) <= 1e-10,
        "phase_decrease": m.get("phase_decrease_violations") == 0,
        "H_decrease": m.get("H_decrease_violations") == 0,
        "rf_continuity": m.get("relative_top_rf_change", float("inf")) <= 0.01,
        "energy_continuity": m.get("relative_energy_change", float("inf")) <= 0.01,
        "free_residual": m.get("free_residual_infinity_norm", float("inf")) <= 1e-8,
        "active_bound": m.get("active_bound_error", float("inf")) <= 1e-10,
        "kkt_analysis_complete": m.get("analysis_complete") is True,
        "kkt_node_coverage": m.get("node_coverage") == 6601,
        "kkt_ip_coverage": m.get("ip_coverage") == 25600,
        "kkt_detJ": m.get("non_positive_detJ") == 0,
        "kkt_finite": m.get("all_values_finite") is True,
        "transfer_validation": m.get("transfer_validation_pass", True),
        "state_reset": not m.get("state_reset", True),
        "endpoint_finite": m.get("endpoint_values_finite", True),
        "spatial_variation": m.get("spatial_variation_retained", False) and m.get("phase_range", 1e-5) > 1e-6,
    }.items():
        if not ok:
            technical.append(key)
    if technical:
        return POSTFAIL, technical
    if m.get("minimum_active_multiplier", -float("inf")) < -1e-8:
        return UPDATE, []
    return PASS, []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-json", type=Path)
    parser.add_argument("--target-dir", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path, default=Path("runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment"))
    args = parser.parse_args()
    metrics = json.loads(args.metrics_json.read_text(encoding="utf-8")) if args.metrics_json else build_metrics(args.target_dir, args.baseline_dir)
    classification, failures = classify(metrics)
    status = {**metrics, "classification": classification, "failures": failures}
    args.target_dir.mkdir(parents=True, exist_ok=True)
    history = {
        "H_decrease_violations": metrics.get("H_decrease_violations"),
        "maximum_H_increase": metrics.get("maximum_H_increase"),
        "normalized_L2_H_increase": metrics.get("normalized_L2_H_increase"),
        "state_reset": metrics.get("state_reset"),
    }
    continuity = {
        "relative_top_rf_change": metrics.get("relative_top_rf_change"),
        "relative_reconstructed_energy_change": metrics.get("relative_energy_change"),
        "top_rf_limit": 0.01,
        "energy_limit": 0.01,
    }
    (args.target_dir / "D3D_A1H0_HISTORY_COMPARISON.json").write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.target_dir / "D3D_A1H0_MECHANICAL_CONTINUITY.json").write_text(json.dumps(continuity, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.target_dir / "D3D_A1H0_STATUS.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.target_dir / "D3D_A1H0_REPORT.md").write_text("# D3D-A1H0 Checkpoint Hold\n\nClassification: `%s`\n" % classification, encoding="utf-8")
    print(json.dumps(status, indent=2, sort_keys=True))
    ok = args.target_dir / "D3D_A1H0.ok"
    update = args.target_dir / "D3D_A1H0_ACTUAL_HISTORY_UPDATE_REQUIRED.json"
    if classification == PASS:
        ok.write_text(PASS + "\n", encoding="utf-8")
        if update.exists(): update.unlink()
        return 0
    if ok.exists(): ok.unlink()
    if classification == UPDATE:
        update.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 23
    if update.exists(): update.unlink()
    return 24


if __name__ == "__main__":
    raise SystemExit(main())
