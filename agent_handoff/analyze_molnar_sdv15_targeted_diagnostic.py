#!/usr/bin/env python3
"""Postprocess the Molnar v2 SDV15 targeted diagnostic run."""

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


CATEGORIES = {
    "numerical_roundoff",
    "retained_precision_effect",
    "staggered_sync_effect",
    "copied_visualization_state_lag",
    "possible_irreversibility_violation",
    "diagnostic_output_incomplete",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def f(row: dict[str, str], key: str, default: float = math.nan) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def extract_rf_u_from_odb(odb_path: Path, out_csv: Path) -> dict[str, object]:
    try:
        from odbAccess import openOdb  # type: ignore
    except Exception as exc:
        return {"odb_available": False, "reason": f"odbAccess import failed: {exc}"}
    if not odb_path.exists():
        return {"odb_available": False, "reason": f"ODB missing: {odb_path}"}
    rows = []
    odb = openOdb(str(odb_path), readOnly=True)
    try:
        for step_name, step in odb.steps.items():
            for i, frame in enumerate(step.frames):
                u2 = math.nan
                rf2 = math.nan
                try:
                    for values in frame.fieldOutputs["U"].values:
                        if values.nodeLabel == 1:
                            u2 = values.data[1]
                            break
                except Exception:
                    pass
                try:
                    for values in frame.fieldOutputs["RF"].values:
                        if values.nodeLabel == 1:
                            rf2 = values.data[1]
                            break
                except Exception:
                    pass
                rows.append({"step": step_name, "frame": i, "step_time": frame.frameValue, "rp_u2": u2, "rp_rf2": rf2})
    finally:
        odb.close()
    write_csv(out_csv, rows, ["step", "frame", "step_time", "rp_u2", "rp_rf2"])
    return {"odb_available": True, "frames": len(rows)}


def classify_event(event: dict[str, str], completed_by_key: dict[tuple[int, int], list[dict[str, str]]]) -> str:
    phys = int(event.get("physical_label") or event.get("mapped_physical_element"))
    source_ip = int(event.get("source_storage_ip") or event.get("odb_integration_point"))
    seq = completed_by_key.get((phys, source_ip), [])
    if len(seq) < 2:
        return "diagnostic_output_incomplete"
    vals = [f(r, "phase_after_u1") for r in seq if not math.isnan(f(r, "phase_after_u1"))]
    if len(vals) < 2:
        return "diagnostic_output_incomplete"
    tol = 1.0e-10
    if all(vals[i] + tol >= vals[i - 1] for i in range(1, len(vals))):
        return "copied_visualization_state_lag"
    max_drop = max(vals[i - 1] - vals[i] for i in range(1, len(vals)))
    if max_drop <= 1.0e-8:
        return "numerical_roundoff"
    return "possible_irreversibility_violation"


def compare_rf(base_rows: list[dict[str, str]], diag_rows: list[dict[str, str]], out_csv: Path) -> dict[str, object]:
    rows = []
    n = min(len(base_rows), len(diag_rows))
    max_abs = 0.0
    max_norm = 0.0
    base_peak = max((abs(f(r, "rp_rf2")) for r in base_rows), default=0.0)
    diag_peak = max((abs(f(r, "rp_rf2")) for r in diag_rows), default=0.0)
    scale = max(base_peak, 1.0e-12)
    for i in range(n):
        br, dr = base_rows[i], diag_rows[i]
        diff = f(dr, "rp_rf2") - f(br, "rp_rf2")
        max_abs = max(max_abs, abs(diff))
        max_norm = max(max_norm, abs(diff) / scale)
        rows.append({"index": i, "baseline_u2": f(br, "rp_u2"), "baseline_rf2": f(br, "rp_rf2"), "diagnostic_u2": f(dr, "rp_u2"), "diagnostic_rf2": f(dr, "rp_rf2"), "rf2_difference": diff})
    write_csv(out_csv, rows, ["index", "baseline_u2", "baseline_rf2", "diagnostic_u2", "diagnostic_rf2", "rf2_difference"])
    return {"matched_points": n, "baseline_peak_abs_rf2": base_peak, "diagnostic_peak_abs_rf2": diag_peak, "max_abs_rf2_difference": max_abs, "max_normalized_rf2_difference": max_norm}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diagnostic-csv", required=True)
    ap.add_argument("--prior-unresolved-events", required=True)
    ap.add_argument("--prior-equivalent-events", required=True)
    ap.add_argument("--baseline-rf", required=True)
    ap.add_argument("--odb")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    trace = read_csv(Path(args.diagnostic_csv))
    write_csv(outdir / "diagnostic_call_trace.csv", trace, list(trace[0].keys()) if trace else ["diagnostic_output_incomplete"])

    completed = [r for r in trace if r.get("source_layer_code") == "1" and r.get("update_stage_code") == "101"]
    completed.sort(key=lambda r: int(r["call_sequence"]))
    completed_by_key = defaultdict(list)
    for r in completed:
        completed_by_key[(int(r["physical_element"]), int(r["source_storage_ip"]))].append(r)
    write_csv(outdir / "completed_phase_state_sequences.csv", completed, list(completed[0].keys()) if completed else ["diagnostic_output_incomplete"])

    unresolved = read_csv(Path(args.prior_unresolved_events))
    equiv = read_csv(Path(args.prior_equivalent_events))
    reclass_rows = []
    for row in unresolved:
        category = classify_event(row, completed_by_key)
        reclass_rows.append({"source_table": "sdv15_unresolved_event_mapping", "event_index": row["event_index"], "physical_element": row["physical_label"], "source_storage_ip": row["source_storage_ip"], "prior_category": row.get("final_category", ""), "diagnostic_category": category})
    for row in equiv:
        if row.get("final_category") != "staggered_sync_effect":
            continue
        phys = row["mapped_physical_element"]
        source_ip = "4" if row["odb_integration_point"] == "3" else "3" if row["odb_integration_point"] == "4" else row["odb_integration_point"]
        reclass_rows.append({"source_table": "sdv15_equivalent_state_comparison", "event_index": row["event_index"], "physical_element": phys, "source_storage_ip": source_ip, "prior_category": row.get("final_category", ""), "diagnostic_category": classify_event({"physical_label": phys, "source_storage_ip": source_ip}, completed_by_key)})
    write_csv(outdir / "sdv15_event_reclassification.csv", reclass_rows, ["source_table", "event_index", "physical_element", "source_storage_ip", "prior_category", "diagnostic_category"])

    worst = [r for r in trace if r.get("physical_element") == "16427" and r.get("source_storage_ip") in {"3", "4"}]
    write_csv(outdir / "worst_event_targeted_history.csv", worst, list(worst[0].keys()) if worst else ["diagnostic_output_incomplete"])

    rf_status = {"odb_available": False, "reason": "ODB not supplied"}
    if args.odb:
        rf_status = extract_rf_u_from_odb(Path(args.odb), outdir / "diagnostic_rf_u.csv")
    if not (outdir / "diagnostic_rf_u.csv").exists():
        write_csv(outdir / "diagnostic_rf_u.csv", [], ["step", "frame", "step_time", "rp_u2", "rp_rf2"])

    base_rf = read_csv(Path(args.baseline_rf))
    diag_rf = read_csv(outdir / "diagnostic_rf_u.csv")
    rf_compare = compare_rf(base_rf, diag_rf, outdir / "diagnostic_vs_baseline_rf_u.csv")

    counts = defaultdict(int)
    for row in reclass_rows:
        counts[row["diagnostic_category"]] += 1
    sdv16_decreases = 0
    for key, rows in completed_by_key.items():
        vals = [f(r, "sdv16_history") for r in rows]
        sdv16_decreases += sum(1 for i in range(1, len(vals)) if vals[i] + 1.0e-10 < vals[i - 1])
    metrics = {
        "trace_rows": len(trace),
        "completed_u1_rows": len(completed),
        "event_classification_counts": dict(counts),
        "sdv16_decreases_in_completed_u1_sequences": sdv16_decreases,
        "rf_status": rf_status,
        "rf_compare": rf_compare,
        "nonintrusiveness_limits": {
            "peak_force_relative_limit": 0.001,
            "rf_u_normalized_difference_limit": 0.001,
        },
    }
    (outdir / "sdv15_targeted_diagnostic_metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    diagnostic_result = "sdv15_diagnostic_output_incomplete"
    if counts.get("possible_irreversibility_violation", 0):
        diagnostic_result = "sdv15_completed_state_possible_violation"
    elif trace and counts and not counts.get("diagnostic_output_incomplete", 0):
        diagnostic_result = "sdv15_completed_state_monotone"
    if rf_compare.get("max_normalized_rf2_difference", 0.0) > 0.001:
        diagnostic_result = "diagnostic_instrumentation_intrusive"

    decision = f"""# SDV15 Targeted Diagnostic Decision

Diagnostic classification: `{diagnostic_result}`

This decision is generated from the source-side diagnostic call trace. Gate A3
is not automatically passed by this diagnostic result; RF-U reference acceptance
and supervisor tolerance decisions remain separate.

## Counts

- Trace rows: `{len(trace)}`
- Completed U1 rows: `{len(completed)}`
- Reclassified event rows: `{len(reclass_rows)}`
- SDV16 decreases in completed U1 sequences: `{sdv16_decreases}`
- Event categories: `{dict(counts)}`

## Non-Intrusiveness

RF-U comparison metrics are recorded in
`diagnostic_vs_baseline_rf_u.csv` and `sdv15_targeted_diagnostic_metrics.json`.
If the RF-U difference exceeds the documented limit, this script classifies the
result as `diagnostic_instrumentation_intrusive`.
"""
    (outdir / "SDV15_TARGETED_DIAGNOSTIC_DECISION.md").write_text(decision, encoding="utf-8")
    missing = CATEGORIES - set(counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
