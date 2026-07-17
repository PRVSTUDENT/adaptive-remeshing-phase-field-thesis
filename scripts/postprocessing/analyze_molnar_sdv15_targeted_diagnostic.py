#!/usr/bin/env python3
"""Postprocess the Molnar v2 SDV15 targeted diagnostic run.

The diagnostic trace records every targeted U1 call.  A stage-101 record means
"values copied after this call", not "last converged call of the increment".
For scientific classification this script therefore first keeps only the last
stage-101 U1 call per (KSTEP, KINC, physical element, source-storage IP).
"""

from __future__ import print_function

import argparse
import csv
import json
import math
import os
from collections import Counter, defaultdict

NAN = float("nan")

FINAL_CLASSIFICATIONS = (
    "sdv15_completed_increment_monotone",
    "sdv15_completed_increment_possible_violation",
    "sdv15_completed_increment_review_incomplete",
)


def read_csv(path):
    if not path or not os.path.exists(path):
        return []
    with open(path, "r") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, rows, fieldnames):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, "w") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_text(path, text):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, "w") as fh:
        fh.write(text)


def to_float(value, default=NAN):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default=None):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def row_phase(row):
    return to_float(row.get("phase_after_u1"))


def row_sdv16(row):
    return to_float(row.get("sdv16_history"))


def source_ip_for_equivalent_row(row):
    odb_ip = str(row.get("odb_integration_point", "")).strip()
    if odb_ip == "3":
        return "4"
    if odb_ip == "4":
        return "3"
    return odb_ip


def make_frame_lookup(base_rows):
    lookup = {}
    for global_frame, row in enumerate(base_rows):
        step_name = row.get("step", "")
        step_number = 1 if step_name == "Step-1" else 2 if step_name == "Step-2" else None
        u2_mm = to_float(row.get("u2_mm"))
        step_time = NAN
        if not math.isnan(u2_mm):
            if step_number == 1:
                step_time = u2_mm / 0.005
            elif step_number == 2:
                step_time = (u2_mm - 0.005) / 0.002
        lookup[global_frame] = {
            "global_frame": global_frame,
            "step": step_name,
            "step_number": step_number,
            "step_frame": to_int(row.get("frame")),
            "step_time": step_time,
            "u2_mm": u2_mm,
            "rf2_kN": to_float(row.get("rf2_kN")),
        }
    return lookup


def ingest_trace(path):
    trace_rows = 0
    stage101_rows = 0
    final_by_increment = {}
    call_sequences = defaultdict(list)
    with open(path, "r") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            trace_rows += 1
            if str(row.get("source_layer_code", "")).strip() != "1":
                continue
            if str(row.get("update_stage_code", "")).strip() != "101":
                continue
            stage101_rows += 1
            kstep = to_int(row.get("kstep"))
            kinc = to_int(row.get("kinc"))
            phys = to_int(row.get("physical_element"))
            source_ip = to_int(row.get("source_storage_ip"))
            call_sequence = to_int(row.get("call_sequence"), -1)
            if None in (kstep, kinc, phys, source_ip):
                continue
            increment_key = (kstep, kinc, phys, source_ip)
            existing = final_by_increment.get(increment_key)
            if existing is None or call_sequence > to_int(existing.get("call_sequence"), -1):
                final_by_increment[increment_key] = row
            call_sequences[(phys, source_ip)].append(row)

    for rows in call_sequences.values():
        rows.sort(key=lambda r: to_int(r.get("call_sequence"), -1))
    return trace_rows, stage101_rows, final_by_increment, call_sequences


def build_final_sequences(final_by_increment):
    sequences = defaultdict(list)
    for (kstep, kinc, phys, source_ip), row in final_by_increment.items():
        sequences[(phys, source_ip)].append(row)
    for rows in sequences.values():
        rows.sort(key=lambda r: (to_int(r.get("kstep"), 0), to_int(r.get("kinc"), 0), to_float(r.get("time2"), 0.0)))
    return sequences


def detect_transitions(sequences, tolerance):
    phase_violations = []
    sdv16_violations = []
    transition_by_key = {}
    max_phase_drop = 0.0
    max_phase_key = None

    for (phys, source_ip), rows in sequences.items():
        for i in range(1, len(rows)):
            prev = rows[i - 1]
            curr = rows[i]
            phase_drop = row_phase(prev) - row_phase(curr)
            sdv16_drop = row_sdv16(prev) - row_sdv16(curr)
            transition_key = (
                phys,
                source_ip,
                to_int(prev.get("kstep")),
                to_int(prev.get("kinc")),
                to_int(curr.get("kstep")),
                to_int(curr.get("kinc")),
            )
            transition_by_key[transition_key] = {
                "physical_element": phys,
                "source_storage_ip": source_ip,
                "previous_kstep": to_int(prev.get("kstep")),
                "previous_kinc": to_int(prev.get("kinc")),
                "current_kstep": to_int(curr.get("kstep")),
                "current_kinc": to_int(curr.get("kinc")),
                "previous_time2": to_float(prev.get("time2")),
                "current_time2": to_float(curr.get("time2")),
                "previous_phase_after_u1": row_phase(prev),
                "current_phase_after_u1": row_phase(curr),
                "phase_drop": phase_drop,
                "previous_sdv16_history": row_sdv16(prev),
                "current_sdv16_history": row_sdv16(curr),
                "sdv16_drop": sdv16_drop,
            }
            if phase_drop > max_phase_drop:
                max_phase_drop = phase_drop
                max_phase_key = transition_key
            if phase_drop > tolerance:
                phase_violations.append(transition_by_key[transition_key])
            if sdv16_drop > tolerance:
                sdv16_violations.append(transition_by_key[transition_key])
    return phase_violations, sdv16_violations, transition_by_key, max_phase_drop, max_phase_key


def frame_to_increment_state(frame_info, phys, source_ip, sequences):
    if not frame_info or frame_info.get("step_number") is None:
        return None
    candidates = [
        row
        for row in sequences.get((phys, source_ip), [])
        if to_int(row.get("kstep")) == frame_info["step_number"]
    ]
    if not candidates:
        return None
    target_step_time = frame_info.get("step_time")
    if target_step_time is not None and not math.isnan(target_step_time):
        return min(candidates, key=lambda r: abs(to_float(r.get("time1")) - target_step_time))
    return None


def classify_event_transition(prev_state, curr_state, tolerance):
    if prev_state is None or curr_state is None:
        return "sdv15_completed_increment_review_incomplete"
    phase_drop = row_phase(prev_state) - row_phase(curr_state)
    if phase_drop > tolerance:
        return "sdv15_completed_increment_possible_violation"
    return "sdv15_completed_increment_monotone"


def classify_events(unresolved_rows, equiv_rows, frame_lookup, sequences, tolerance):
    event_rows = []
    counts = Counter()
    for row in unresolved_rows:
        phys = to_int(row.get("physical_label"))
        source_ip = to_int(row.get("source_storage_ip"))
        prev_frame = to_int(row.get("previous_global_frame"))
        curr_frame = to_int(row.get("current_global_frame"))
        prev_state = frame_to_increment_state(frame_lookup.get(prev_frame), phys, source_ip, sequences)
        curr_state = frame_to_increment_state(frame_lookup.get(curr_frame), phys, source_ip, sequences)
        category = classify_event_transition(prev_state, curr_state, tolerance)
        counts[category] += 1
        event_rows.append({
            "source_table": "sdv15_unresolved_event_mapping",
            "event_index": row.get("event_index", ""),
            "visualization_label": row.get("visualization_label", ""),
            "physical_element": phys,
            "source_storage_ip": source_ip,
            "previous_global_frame": prev_frame,
            "current_global_frame": curr_frame,
            "previous_kstep": "" if prev_state is None else prev_state.get("kstep", ""),
            "previous_kinc": "" if prev_state is None else prev_state.get("kinc", ""),
            "current_kstep": "" if curr_state is None else curr_state.get("kstep", ""),
            "current_kinc": "" if curr_state is None else curr_state.get("kinc", ""),
            "previous_phase_after_u1": "" if prev_state is None else row_phase(prev_state),
            "current_phase_after_u1": "" if curr_state is None else row_phase(curr_state),
            "phase_drop": "" if prev_state is None or curr_state is None else row_phase(prev_state) - row_phase(curr_state),
            "prior_category": row.get("final_category", ""),
            "diagnostic_category": category,
        })

    for row in equiv_rows:
        if row.get("final_category") != "staggered_sync_effect":
            continue
        phys = to_int(row.get("mapped_physical_element"))
        source_ip = to_int(source_ip_for_equivalent_row(row))
        curr_frame = to_int(row.get("current_global_frame"))
        prev_frame = None if curr_frame is None else curr_frame - 1
        prev_state = frame_to_increment_state(frame_lookup.get(prev_frame), phys, source_ip, sequences)
        curr_state = frame_to_increment_state(frame_lookup.get(curr_frame), phys, source_ip, sequences)
        category = classify_event_transition(prev_state, curr_state, tolerance)
        counts[category] += 1
        event_rows.append({
            "source_table": "sdv15_equivalent_state_comparison",
            "event_index": row.get("event_index", ""),
            "visualization_label": row.get("odb_element", ""),
            "physical_element": phys,
            "source_storage_ip": source_ip,
            "previous_global_frame": prev_frame,
            "current_global_frame": curr_frame,
            "previous_kstep": "" if prev_state is None else prev_state.get("kstep", ""),
            "previous_kinc": "" if prev_state is None else prev_state.get("kinc", ""),
            "current_kstep": "" if curr_state is None else curr_state.get("kstep", ""),
            "current_kinc": "" if curr_state is None else curr_state.get("kinc", ""),
            "previous_phase_after_u1": "" if prev_state is None else row_phase(prev_state),
            "current_phase_after_u1": "" if curr_state is None else row_phase(curr_state),
            "phase_drop": "" if prev_state is None or curr_state is None else row_phase(prev_state) - row_phase(curr_state),
            "prior_category": row.get("final_category", ""),
            "diagnostic_category": category,
        })
    return event_rows, counts


def extract_rf_u_from_odb(odb_path, out_csv, rp_node_label):
    try:
        from odbAccess import openOdb  # type: ignore
    except Exception as exc:
        return {"odb_available": False, "reason": "odbAccess import failed: %s" % exc}
    if not odb_path or not os.path.exists(odb_path):
        return {"odb_available": False, "reason": "ODB missing: %s" % odb_path}

    rows = []
    odb = openOdb(odb_path, readOnly=True)
    try:
        for step_name, step in odb.steps.items():
            for i, frame in enumerate(step.frames):
                u2 = NAN
                rf2 = NAN
                try:
                    for values in frame.fieldOutputs["U"].values:
                        if values.nodeLabel == rp_node_label:
                            u2 = float(values.data[1])
                            break
                except Exception:
                    pass
                try:
                    for values in frame.fieldOutputs["RF"].values:
                        if values.nodeLabel == rp_node_label:
                            rf2 = float(values.data[1])
                            break
                except Exception:
                    pass
                rows.append({"step": step_name, "frame": i, "u2_mm": u2, "rf2_kN": rf2})
    finally:
        odb.close()
    write_csv(out_csv, rows, ["step", "frame", "u2_mm", "rf2_kN"])
    return {"odb_available": True, "frames": len(rows), "rp_node_label": rp_node_label}


def compare_rf(base_rows, diag_rows, out_csv):
    rows = []
    n = min(len(base_rows), len(diag_rows))
    max_abs = 0.0
    max_norm = 0.0
    max_u = 0.0
    base_peak = max([abs(to_float(r.get("rf2_kN"))) for r in base_rows] or [0.0])
    diag_peak = max([abs(to_float(r.get("rf2_kN"))) for r in diag_rows] or [0.0])
    scale = max(base_peak, 1.0e-12)
    nan_rows = 0
    for i in range(n):
        br, dr = base_rows[i], diag_rows[i]
        b_rf = to_float(br.get("rf2_kN"))
        d_rf = to_float(dr.get("rf2_kN"))
        b_u = to_float(br.get("u2_mm"))
        d_u = to_float(dr.get("u2_mm"))
        if math.isnan(b_rf) or math.isnan(d_rf):
            nan_rows += 1
            diff = NAN
        else:
            diff = d_rf - b_rf
            max_abs = max(max_abs, abs(diff))
            max_norm = max(max_norm, abs(diff) / scale)
        if not math.isnan(b_u) and not math.isnan(d_u):
            max_u = max(max_u, abs(d_u - b_u))
        rows.append({
            "index": i,
            "baseline_u2_mm": b_u,
            "baseline_rf2_kN": b_rf,
            "diagnostic_u2_mm": d_u,
            "diagnostic_rf2_kN": d_rf,
            "rf2_difference": diff,
        })
    write_csv(out_csv, rows, ["index", "baseline_u2_mm", "baseline_rf2_kN", "diagnostic_u2_mm", "diagnostic_rf2_kN", "rf2_difference"])
    return {
        "matched_points": n,
        "nan_rows": nan_rows,
        "baseline_peak_abs_rf2_kN": base_peak,
        "diagnostic_peak_abs_rf2_kN": diag_peak,
        "max_abs_rf2_difference": max_abs,
        "max_normalized_rf2_difference": max_norm,
        "max_abs_u2_difference_mm": max_u,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diagnostic-csv", required=True)
    ap.add_argument("--prior-unresolved-events", required=True)
    ap.add_argument("--prior-equivalent-events", required=True)
    ap.add_argument("--baseline-rf", required=True)
    ap.add_argument("--odb")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--rp-node-label", type=int, default=34508)
    ap.add_argument("--phase-drop-tolerance", type=float, default=1.0e-8)
    args = ap.parse_args()

    if not os.path.isdir(args.outdir):
        os.makedirs(args.outdir)
    base_rf = read_csv(args.baseline_rf)
    frame_lookup = make_frame_lookup(base_rf)
    unresolved = read_csv(args.prior_unresolved_events)
    equiv = read_csv(args.prior_equivalent_events)

    trace_rows, stage101_rows, final_by_increment, call_sequences = ingest_trace(args.diagnostic_csv)
    final_sequences = build_final_sequences(final_by_increment)
    phase_violations, sdv16_violations, transition_by_key, max_phase_drop, max_phase_key = detect_transitions(
        final_sequences, args.phase_drop_tolerance
    )
    event_rows, event_counts = classify_events(unresolved, equiv, frame_lookup, final_sequences, args.phase_drop_tolerance)

    transition_rows = []
    for row in phase_violations:
        transition_rows.append(row)
    write_csv(
        os.path.join(args.outdir, "sdv15_completed_increment_violating_transitions.csv"),
        transition_rows,
        [
            "physical_element",
            "source_storage_ip",
            "previous_kstep",
            "previous_kinc",
            "current_kstep",
            "current_kinc",
            "previous_time2",
            "current_time2",
            "previous_phase_after_u1",
            "current_phase_after_u1",
            "phase_drop",
            "previous_sdv16_history",
            "current_sdv16_history",
            "sdv16_drop",
        ],
    )
    write_csv(
        os.path.join(args.outdir, "sdv15_event_completed_increment_reclassification.csv"),
        event_rows,
        [
            "source_table",
            "event_index",
            "visualization_label",
            "physical_element",
            "source_storage_ip",
            "previous_global_frame",
            "current_global_frame",
            "previous_kstep",
            "previous_kinc",
            "current_kstep",
            "current_kinc",
            "previous_phase_after_u1",
            "current_phase_after_u1",
            "phase_drop",
            "prior_category",
            "diagnostic_category",
        ],
    )

    worst_rows = [
        row for row in event_rows
        if str(row.get("visualization_label")) == "84131"
        and str(row.get("physical_element")) == "16427"
        and str(row.get("source_storage_ip")) in ("3", "4")
    ]
    write_csv(
        os.path.join(args.outdir, "worst_event_84131_16427_converged_increment_check.csv"),
        worst_rows,
        [
            "source_table",
            "event_index",
            "visualization_label",
            "physical_element",
            "source_storage_ip",
            "previous_global_frame",
            "current_global_frame",
            "previous_kstep",
            "previous_kinc",
            "current_kstep",
            "current_kinc",
            "previous_phase_after_u1",
            "current_phase_after_u1",
            "phase_drop",
            "prior_category",
            "diagnostic_category",
        ],
    )

    rf_status = {"odb_available": False, "reason": "ODB not supplied"}
    diag_rf = []
    if args.odb:
        rf_status = extract_rf_u_from_odb(args.odb, os.path.join(args.outdir, "diagnostic_rf_u.csv"), args.rp_node_label)
        diag_rf = read_csv(os.path.join(args.outdir, "diagnostic_rf_u.csv"))
    if not diag_rf:
        write_csv(os.path.join(args.outdir, "diagnostic_rf_u.csv"), [], ["step", "frame", "u2_mm", "rf2_kN"])
    rf_compare = compare_rf(base_rf, diag_rf, os.path.join(args.outdir, "diagnostic_vs_baseline_rf_u.csv")) if diag_rf else {
        "matched_points": 0,
        "nan_rows": 0,
        "baseline_peak_abs_rf2_kN": max([abs(to_float(r.get("rf2_kN"))) for r in base_rf] or [0.0]),
        "diagnostic_peak_abs_rf2_kN": 0.0,
        "max_abs_rf2_difference": NAN,
        "max_normalized_rf2_difference": NAN,
        "max_abs_u2_difference_mm": NAN,
    }

    if phase_violations:
        completed_increment_result = "sdv15_completed_increment_possible_violation"
    elif final_by_increment and not event_counts.get("sdv15_completed_increment_review_incomplete", 0):
        completed_increment_result = "sdv15_completed_increment_monotone"
    else:
        completed_increment_result = "sdv15_completed_increment_review_incomplete"

    metrics = {
        "trace_rows": trace_rows,
        "u1_stage101_call_rows": stage101_rows,
        "final_increment_states": len(final_by_increment),
        "element_ip_sequences": len(final_sequences),
        "unique_completed_increment_phase_violating_transitions": len(phase_violations),
        "completed_increment_event_classification_counts": dict(event_counts),
        "sdv16_decreases_in_completed_increment_sequences": len(sdv16_violations),
        "max_completed_increment_phase_drop": max_phase_drop,
        "max_completed_increment_phase_drop_key": list(max_phase_key) if max_phase_key else None,
        "call_level_result": "sdv15_call_level_nonmonotonicity_observed",
        "completed_increment_result": completed_increment_result,
        "rf_status": rf_status,
        "rf_compare": rf_compare,
        "nonintrusiveness_limits": {
            "rf_u_normalized_difference_limit": 0.001,
        },
    }
    write_text(
        os.path.join(args.outdir, "sdv15_targeted_diagnostic_metrics.json"),
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
    )

    decision = """# SDV15 Targeted Diagnostic Decision

PBS wrapper classification: `postprocess_python_compatibility_failure_after_successful_solve`

Abaqus classification: `molnar_v2_sdv15_diagnostic_r2_technical_pass`

Diagnostic instrumentation: `non_intrusive_pass` if the RF-U comparison remains
within the documented limit; see `sdv15_targeted_diagnostic_metrics.json`.

Scientific evidence: `sdv15_call_level_nonmonotonicity_observed`

Completed/converged increment classification: `{completed_increment_result}`

This decision is generated from a no-solution replay of the existing diagnostic
trace. It keeps only the last U1 stage-101 call for each `(KSTEP, KINC,
physical element, source-storage IP)` before checking monotonicity. Gate A3
remains `reference_data_insufficient`; this diagnostic does not authorize a
new PBS/Abaqus submission.

## Counts

- Trace rows: `{trace_rows}`
- U1 stage-101 call rows: `{stage101_rows}`
- Final increment states: `{final_increment_states}`
- Element/IP sequences: `{element_ip_sequences}`
- Unique completed-increment SDV15 violating transitions: `{violating_transitions}`
- Event reclassification counts: `{event_counts}`
- SDV16 decreases over completed-increment sequences: `{sdv16_decreases}`
- RF-U max normalized difference: `{rf_norm}`
""".format(
        completed_increment_result=completed_increment_result,
        trace_rows=trace_rows,
        stage101_rows=stage101_rows,
        final_increment_states=len(final_by_increment),
        element_ip_sequences=len(final_sequences),
        violating_transitions=len(phase_violations),
        event_counts=dict(event_counts),
        sdv16_decreases=len(sdv16_violations),
        rf_norm=rf_compare.get("max_normalized_rf2_difference"),
    )
    write_text(os.path.join(args.outdir, "SDV15_TARGETED_DIAGNOSTIC_DECISION.md"), decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
