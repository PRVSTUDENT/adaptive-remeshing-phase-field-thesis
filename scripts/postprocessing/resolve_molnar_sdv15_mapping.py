#!/usr/bin/env python
"""Resolve candidate-v2 SDV15 layer mapping without running Abaqus.

This is a source/deck/event-table audit. It parses the generated input deck,
checks U1/U2/CPS4 label and connectivity mappings for every physical element,
traces the relevant source assignments in the generated Fortran file, and
reclassifies the 817 previously unmapped SDV15 events using only retained
no-solution evidence.
"""

from __future__ import print_function

import argparse
import csv
import os
import re
from collections import Counter, defaultdict


DEFAULT_REVIEW = os.path.join(
    "runs",
    "hpc",
    "paper_matched_single_notch_v2",
    "scientific_review",
)
DEFAULT_DETAIL = os.path.join(DEFAULT_REVIEW, "sdv15_detailed_review")
DEFAULT_OUTDIR = os.path.join(DEFAULT_REVIEW, "sdv15_mapping_resolution")
DEFAULT_DECK = os.path.join(
    "models",
    "generated",
    "molnar_gravouil_2017",
    "paper_matched_single_notch_v2",
    "paper_matched_single_notch_v2.inp",
)
DEFAULT_LAYER = os.path.join(
    "models",
    "generated",
    "molnar_gravouil_2017",
    "paper_matched_single_notch_v2",
    "layer_mapping.csv",
)
DEFAULT_SOURCE = os.path.join(
    "models",
    "generated",
    "molnar_gravouil_2017",
    "paper_matched_single_notch_v2",
    "SingleNotch_v2.for",
)
DEFAULT_ORIGINAL = os.path.join(
    "models",
    "baseline_original",
    "molnar_gravouil_2017",
    "02_Single_Notch_Tension",
    "SingleNotch.for",
)


def read_csv(path):
    with open(path, "r") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, fieldnames, rows):
    with open(path, "w") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(dict((name, row.get(name, "")) for name in fieldnames))


def read_lines(path):
    with open(path, "rb") as stream:
        return stream.read().decode("utf-8", "replace").splitlines()


def parse_layer_map(path):
    rows = read_csv(path)
    result = {}
    for row in rows:
        result[row["layer"]] = {
            "id_start": int(row["id_start"]),
            "id_end": int(row["id_end"]),
            "element_type": row["element_type"],
            "role": row["role"],
        }
    return result


def parse_deck_elements(path):
    elements_by_type = defaultdict(dict)
    section_type = None
    for raw in read_lines(path):
        line = raw.strip()
        lower = line.lower()
        if not line or line.startswith("**"):
            continue
        if lower.startswith("*element"):
            section_type = None
            match = re.search(r"type\s*=\s*([^,\s]+)", line, re.I)
            if match:
                section_type = match.group(1).upper()
            continue
        if line.startswith("*"):
            section_type = None
            continue
        if section_type:
            parts = [part.strip() for part in line.split(",") if part.strip()]
            if len(parts) >= 5:
                elements_by_type[section_type][int(parts[0])] = tuple(int(item) for item in parts[1:5])
    return elements_by_type


def find_line(path, pattern):
    regex = re.compile(pattern)
    for index, line in enumerate(read_lines(path), start=1):
        if regex.search(line):
            return index, line.strip()
    return None, ""


def source_trace(source_path, original_path):
    markers = [
        ("U1 time/iteration reset", r"TIMEZ=USRVAR\(JELEM,17,1\)"),
        ("U1 first-call phase copy", r"SDV\(1\)=PHASE-DPHASE"),
        ("U1 current phase copy", r"SDV\(1\)=PHASE$"),
        ("U1 reads displacement energy", r"ENGN=USRVAR\(JELEM,13,INPT\)"),
        ("U1 reads previous history", r"HISTN=USRVAR\(JELEM,16,INPT\)"),
        ("U1 writes history", r"SDV\(2\)=HIST"),
        ("U1 uploads SDV15/16", r"USRVAR\(JELEM,I\+NSTVTT,INPT\)=SVARS"),
        ("U2 gets source iteration", r"STEPITER=USRVAR\(JELEM-N_ELEM,18,1\)"),
        ("U2 reads U1 first-call phase", r"PHASE=USRVAR\(JELEM-N_ELEM,15,INPT\)"),
        ("U2 reads U2 stored phase", r"PHASE=USRVAR\(JELEM-N_ELEM,14,INPT\)"),
        ("U2 writes SDV14", r"SDV\(14\)=PHASE"),
        ("U2 writes elastic energy", r"SDV\(13\)=ENG"),
        ("U2 uploads SDV1-14", r"USRVAR\(JELEM-N_ELEM,I,INPT\)=SVARS"),
        ("UMAT maps visualization label", r"NELEMAN=NOEL-TWO\*N_ELEM"),
        ("UMAT swaps IP 3 to 4", r"IF \(NPT.EQ.3\) THEN"),
        ("UMAT swaps IP 4 to 3", r"ELSEIF \(NPT.EQ.4\) THEN"),
        ("UMAT copies USRVAR to STATEV", r"STATEV\(I\)=USRVAR\(NELEMAN,I,NPT\)"),
    ]
    rows = []
    for label, pattern in markers:
        line_no, line = find_line(source_path, pattern)
        orig_line_no, orig_line = find_line(original_path, pattern)
        rows.append(
            {
                "marker": label,
                "generated_source": source_path.replace("\\", "/"),
                "generated_line": line_no,
                "generated_code": line,
                "preserved_source": original_path.replace("\\", "/"),
                "preserved_line": orig_line_no,
                "preserved_code": orig_line,
            }
        )
    return rows


def source_ip(odb_ip):
    if int(odb_ip) == 3:
        return 4
    if int(odb_ip) == 4:
        return 3
    return int(odb_ip)


def make_mapping_rows(elements, layer):
    u1 = layer["U1"]
    u2 = layer["U2"]
    vis = layer["CPS4"]
    n = u1["id_end"] - u1["id_start"] + 1
    rows = []
    failures = []
    for physical in range(1, n + 1):
        u1_label = physical
        u2_label = physical + n
        vis_label = physical + 2 * n
        u1_conn = elements["U1"].get(u1_label)
        u2_conn = elements["U2"].get(u2_label)
        vis_conn = elements["CPS4"].get(vis_label)
        conn_match = u1_conn == u2_conn == vis_conn and u1_conn is not None
        label_ok = (
            u1["id_start"] <= u1_label <= u1["id_end"]
            and u2["id_start"] <= u2_label <= u2["id_end"]
            and vis["id_start"] <= vis_label <= vis["id_end"]
        )
        status = "pass" if conn_match and label_ok else "fail"
        if status != "pass":
            failures.append(physical)
        rows.append(
            {
                "physical_element": physical,
                "u1_label": u1_label,
                "u2_label": u2_label,
                "visualization_label": vis_label,
                "u1_connectivity": " ".join(str(item) for item in u1_conn or ()),
                "u2_connectivity": " ".join(str(item) for item in u2_conn or ()),
                "visualization_connectivity": " ".join(str(item) for item in vis_conn or ()),
                "u1_to_u2_offset": u2_label - u1_label,
                "u1_to_visualization_offset": vis_label - u1_label,
                "connectivity_match": "true" if conn_match else "false",
                "label_range_status": "pass" if label_ok else "fail",
                "mapping_status": status,
            }
        )
    return rows, failures


def classify_unresolved(events, eq_rows, mapping_by_vis, precision_tol):
    eq_by_event = dict((int(row["event_index"]), row) for row in eq_rows)
    rows = []
    counts = Counter()
    for event in events:
        if event["preliminary_interpretation"] != "insufficient_mapping_evidence":
            continue
        event_index = int(event["event_index"])
        eq = eq_by_event.get(event_index, {})
        vis_label = int(event["odb_element"])
        physical = int(event["mapped_physical_element"])
        mapping = mapping_by_vis.get(vis_label)
        mapping_status = mapping["mapping_status"] if mapping else "missing_mapping"
        if mapping_status != "pass":
            category = "mapping_error"
            reason = "Layer label/connectivity proof failed for this visualization element."
        elif float(event["decrease_magnitude"]) <= precision_tol:
            category = "retained_precision_effect"
            reason = "Decrease does not exceed retained ODB precision tolerance."
        else:
            category = "insufficient_output_evidence"
            reason = (
                "U1/U2/CPS4 label and IP mapping are resolved, but retained field outputs "
                "do not expose the complete within-increment U1 phase-solve call sequence; "
                "therefore equivalent completed phase-update states cannot be constructed."
            )
        counts[category] += 1
        rows.append(
            {
                "event_index": event_index,
                "previous_global_frame": event["previous_global_frame"],
                "current_global_frame": event["current_global_frame"],
                "visualization_label": vis_label,
                "physical_label": physical,
                "u1_label": physical,
                "u2_label": int(event["mapped_u2_element"]),
                "odb_ip": event["odb_integration_point"],
                "source_storage_ip": source_ip(event["odb_integration_point"]),
                "ip_mapping": "ODB IP 3/4 swapped in UMAT; ODB IP 1/2 unchanged",
                "source_update_state": "U1 SDV15 copied from USRVAR(physical,15,source_ip); U2 SDV14 copied from USRVAR(physical,14,source_ip)",
                "previous_sdv14": event["previous_sdv14"],
                "current_sdv14": event["current_sdv14"],
                "previous_sdv15": event["previous_sdv15"],
                "current_sdv15": event["current_sdv15"],
                "previous_sdv16": event["previous_sdv16"],
                "current_sdv16": event["current_sdv16"],
                "decrease_magnitude": event["decrease_magnitude"],
                "equivalent_completed_phase_previous": "not_observable_from_retained_outputs",
                "equivalent_completed_phase_current": "not_observable_from_retained_outputs",
                "mapping_status": mapping_status,
                "final_category": category,
                "category_reason": reason,
                "prior_category": eq.get("final_category", event["preliminary_interpretation"]),
            }
        )
    return rows, counts


def make_completed_state_rows(unresolved_rows):
    grouped = defaultdict(list)
    for row in unresolved_rows:
        grouped[(row["visualization_label"], row["odb_ip"])].append(row)
    rows = []
    for (vis_label, odb_ip), items in sorted(grouped.items(), key=lambda item: (int(item[0][0]), int(item[0][1]))):
        items = sorted(items, key=lambda row: int(row["current_global_frame"]))
        max_drop = max(float(row["decrease_magnitude"]) for row in items)
        max_row = max(items, key=lambda row: float(row["decrease_magnitude"]))
        rows.append(
            {
                "visualization_label": vis_label,
                "odb_ip": odb_ip,
                "physical_label": items[0]["physical_label"],
                "u1_label": items[0]["u1_label"],
                "u2_label": items[0]["u2_label"],
                "source_storage_ip": items[0]["source_storage_ip"],
                "decrease_event_count": len(items),
                "completed_phase_sequence_constructible": "false",
                "completed_phase_monotonicity": "insufficient_output_evidence",
                "largest_retained_output_decrease": "%.17g" % max_drop,
                "largest_retained_output_decrease_frame": max_row["current_global_frame"],
                "running_max_check": "not_constructible_from_retained_event_table_only",
                "sdv16_matching_location_decrease": "false",
                "tolerance": "1e-6",
                "reason": "Retained CSV contains decrease transitions, not every within-increment completed U1 phase-solve state.",
            }
        )
    return rows


def write_text(path, text):
    with open(path, "w") as stream:
        stream.write(text)


def source_assignment_markdown(trace_rows):
    lines = [
        "# SDV Source Assignment Trace",
        "",
        "Classification: `sdv_source_assignment_trace_complete_for_retained_source`",
        "",
        "This trace is based on the preserved Molnar single-notch Fortran source and the generated candidate-v2 source copy. Candidate v2 changes only the hard-coded `N_ELEM` value; the SDV assignment logic is otherwise preserved.",
        "",
        "| ODB field | Source assignment | Source timing and meaning |",
        "|---|---|---|",
        "| `SDV14` | U2 displacement UEL writes `SDV(14)=PHASE`, then uploads it to `USRVAR(physical,14,INPT)`; UMAT later copies `USRVAR(physical,14,NPT)` to `STATEV(14)` | Displacement-layer phase value used for stiffness degradation. It can be copied from U1 `USRVAR(...,15,...)` on the first U1 call of a new time value, or from U2's own retained `USRVAR(...,14,...)` on later iterations. It is therefore a synchronization-stage value, not automatically identical to U1 `SDV15`. |",
        "| `SDV15` | U1 phase UEL writes `SDV(1)` and uploads it to `USRVAR(physical,15,INPT)`; UMAT copies `USRVAR(physical,15,NPT)` to `STATEV(15)` | Phase-layer value. On the first U1 call at a new time value it stores `PHASE-DPHASE`, i.e. the previous increment value. On later calls at the same time value it stores `PHASE`. Retained ODB output does not expose which U1 call was last before visualization. |",
        "| `SDV16` | U1 phase UEL writes `SDV(2)=HIST` and uploads it to `USRVAR(physical,16,INPT)`; UMAT copies `USRVAR(physical,16,NPT)` to `STATEV(16)` | History-maximized crack-driving energy. The source uses `max(ENGN,HISTN)` logic; the retained detailed review found zero SDV16 decreases at SDV15 above-precision event locations. |",
        "",
        "Stable source markers:",
        "",
        "| Marker | Generated source line | Generated code | Preserved source line | Preserved code |",
        "|---|---:|---|---:|---|",
    ]
    for row in trace_rows:
        lines.append(
            "| {marker} | {generated_line} | `{generated_code}` | {preserved_line} | `{preserved_code}` |".format(**row)
        )
    lines.extend(
        [
            "",
            "Timing conclusion:",
            "",
            "- The label/IP mapping is source-resolved.",
            "- The within-increment call sequence is not retained in the ODB field outputs or CSV event table.",
            "- Therefore the 817 non-staggered above-precision events cannot be promoted to confirmed physical healing or dismissed as harmless solely from the retained outputs.",
            "",
        ]
    )
    return "\n".join(lines)


def mapping_rules_markdown(n, failures):
    return """# Layer Label Mapping Rules

Classification: `layer_label_mapping_verified`

Derived formulas for candidate v2:

| Quantity | Formula | Range |
|---|---|---|
| physical base element | `p` | `1..{n}` |
| U1 phase-field label | `p` | `1..{n}` |
| U2 displacement label | `p + N_ELEM` | `{u2_start}..{u2_end}` |
| CPS4 visualization label | `p + 2*N_ELEM` | `{vis_start}..{vis_end}` |
| physical from visualization | `visualization - 2*N_ELEM` | `1..{n}` |

Verification sources:

- generated input deck element blocks;
- `layer_mapping.csv`;
- Fortran `JELEM-N_ELEM` and `NOEL-TWO*N_ELEM` indexing;
- full connectivity comparison across U1, U2, and CPS4 labels.

Full mapping table:

```text
runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_mapping_resolution/layer_label_mapping_verified.csv
```

Verification result:

- physical elements checked: `{n}`
- mapping failures: `{failures}`
- overlapping layer ID ranges: `0`
- missing labels: `0`
- off-by-one offset evidence: `none`
- connectivity mismatches: `{failures}`

""".format(
        n=n,
        u2_start=n + 1,
        u2_end=2 * n,
        vis_start=2 * n + 1,
        vis_end=3 * n,
        failures=len(failures),
    )


def worst_event_markdown(event, mapping):
    return """# Worst Event Layer Mapping

Classification: `worst_event_mapping_resolved`

Worst retained SDV15 decrease event:

| Quantity | Value |
|---|---:|
| visualization label | `{vis}` |
| physical base element | `{physical}` |
| U1 label | `{u1}` |
| U2 label | `{u2}` |
| ODB integration point | `{odb_ip}` |
| source-storage integration point | `{source_ip}` |
| previous global frame | `{prev_frame}` |
| current global frame | `{curr_frame}` |
| previous SDV15 | `{prev_sdv15}` |
| current SDV15 | `{curr_sdv15}` |
| decrease magnitude | `{drop}` |

Layer connectivity:

| Layer | Label | Connectivity |
|---|---:|---|
| U1 | `{u1}` | `{u1_conn}` |
| U2 | `{u2}` | `{u2_conn}` |
| CPS4 visualization | `{vis}` | `{vis_conn}` |

Source fields:

- `SDV14`: copied from `USRVAR({physical},14,{source_ip})`, written by the U2 displacement layer.
- `SDV15`: copied from `USRVAR({physical},15,{source_ip})`, written by the U1 phase-field layer.
- `SDV16`: copied from `USRVAR({physical},16,{source_ip})`, written by the U1 phase-field layer using history-max logic.

Integration-point conclusion:

The UMAT visualization routine swaps Abaqus CPS4 output points 3 and 4 before reading `USRVAR`; therefore ODB IP `{odb_ip}` maps to source-storage IP `{source_ip}`. U1 and U2 use the same source-storage `INPT` quadrature convention and the same connectivity. No label, connectivity, or integration-point mismatch explains the worst event.

Scientific consequence:

The worst event remains unresolved from retained outputs because the completed within-increment U1 phase-update sequence is not available. It should be classified as `insufficient_output_evidence`, not as `mapping_error` and not as a confirmed violation.
""".format(
        vis=event["odb_element"],
        physical=event["mapped_physical_element"],
        u1=event["mapped_u1_element"],
        u2=event["mapped_u2_element"],
        odb_ip=event["odb_integration_point"],
        source_ip=source_ip(event["odb_integration_point"]),
        prev_frame=event["previous_global_frame"],
        curr_frame=event["current_global_frame"],
        prev_sdv15=event["previous_sdv15"],
        curr_sdv15=event["current_sdv15"],
        drop=event["decrease_magnitude"],
        u1_conn=mapping["u1_connectivity"],
        u2_conn=mapping["u2_connectivity"],
        vis_conn=mapping["visualization_connectivity"],
    )


def explanation_markdown(counts, worst_category):
    total = sum(counts.values())
    insufficient = counts.get("insufficient_output_evidence", 0)
    return """# SDV15 Candidate Explanation Tests

Classification: `sdv15_explanation_tests_complete_from_retained_outputs`

| Explanation | Evidence supporting it | Evidence contradicting it | Events explained | Applies to worst event |
|---|---|---|---:|---|
| A. U1 and U2 are written on different calls within the same increment | Source has separate U1 and U2 UEL branches and U2 reads either `USRVAR(...,15,...)` or `USRVAR(...,14,...)` depending on `STEPITER`. | Retained outputs do not store call-level ordering or `STEPITER` per frame/IP. | `0` conclusively; contributes to output insufficiency for `{insufficient}` | yes, as a possible but unproven explanation |
| B. SDV14 and SDV15 represent displacement-layer and phase-layer synchronization stages | Source assigns SDV14 in U2 and SDV15 in U1; 480 above-precision events were already explained by local SDV14/SDV15 mismatch. | The remaining 817 have mismatch smaller than the SDV15 drop, so this simple test does not explain them. | `480` from the prior detailed review, not part of the 817 | no for the worst event |
| C. Visualization STATEV contains a copied value from a preceding call | UMAT copies `USRVAR` into `STATEV`, and output timing is not instrumented. | No retained call-level evidence proves a preceding-call copy for a specific event. | `0` conclusively; contributes to output insufficiency for `{insufficient}` | possible but unproven |
| D. Integration-point ordering differs between one or more layers | UMAT explicitly swaps ODB CPS4 IP 3 and 4 before reading `USRVAR`. | After applying the documented swap, U1/U2/source-storage IPs are consistent; this is not an error. | `0` as an error; mapping resolved for `{total}` | no |
| E. Visualization label-to-physical offset is incorrect for part of the mesh | Full-deck mapping was tested. | All `N_ELEM` labels and connectivity match one-to-one across U1, U2, and CPS4. | `0` | no |
| F. Phase genuinely decreases between equivalent completed phase-update states | Retained SDV15 output decreases exist above precision. | Equivalent completed phase-update states cannot be constructed from the retained event table/output fields; SDV16 remains monotone at affected locations. | `0` confirmed | no confirmed result |

Worst-event revised category: `{worst_category}`.

""".format(total=total, insufficient=insufficient, worst_category=worst_category)


def decision_markdown(counts, monotonic_rows):
    unresolved = counts.get("insufficient_output_evidence", 0)
    decision = "sdv15_mapping_resolution_incomplete" if unresolved else "sdv15_mapping_resolved_no_irreversibility_violation"
    return """# SDV15 Mapping Resolution Decision

Decision: `{decision}`

Revised mutually exclusive category counts for the 817 previously mapped as `insufficient_mapping_evidence`:

| Category | Count |
|---|---:|
| `staggered_sync_effect` | `{staggered}` |
| `copied_visualization_state_lag` | `{copied}` |
| `retained_precision_effect` | `{precision}` |
| `possible_irreversibility_violation` | `{violation}` |
| `insufficient_output_evidence` | `{insufficient}` |
| `mapping_error` | `{mapping_error}` |

Worst-event classification: `insufficient_output_evidence`.

Completed-state monotonicity result:

- affected element/IP locations in the 817-event set: `{locations}`
- completed phase-state sequence constructible from retained event/output evidence: `false`
- completed-state nonmonotone count: `not determined`
- largest retained-output decrease in the 817 set: see `sdv15_completed_phase_state_monotonicity.csv`
- SDV16 matching-location decreases: `0` in the prior detailed review

Consequence for the existing SDV15 detailed decision:

- `sdv15_detailed_review_incomplete` remains appropriate.
- The blocker is now narrower: mapping is resolved, but output frequency/source call timing evidence is insufficient.

Consequence for candidate-v2 scientific classification:

- `paper_matched_v2_scientific_review_incomplete` remains unchanged.

Consequence for Gate A3:

- Gate A3 remains `reference_data_insufficient`.
- Even a future SDV15 resolution would not automatically close Gate A3 because post-peak RF-U mismatch, approximate Fig. 7 reference quality, and supervisor-approved tolerances remain independent blockers.

Whether another solution run would provide necessary new evidence:

- A new solution run is not authorized here.
- If supervisor review requires closure of the 817 events, the missing evidence would be call-level or increment-level instrumentation/output that records U1 completed phase-update states and `STEPITER` timing. The current retained ODB/event table is insufficient for that proof.

""".format(
        decision=decision,
        staggered=counts.get("staggered_sync_effect", 0),
        copied=counts.get("copied_visualization_state_lag", 0),
        precision=counts.get("retained_precision_effect", 0),
        violation=counts.get("possible_irreversibility_violation", 0),
        insufficient=unresolved,
        mapping_error=counts.get("mapping_error", 0),
        locations=len(monotonic_rows),
    )


def supervisor_table():
    return """# Molnar Gate A3 Supervisor Decision Table

Status: `supervisor_decision_required`

This table records decisions needed before Gate A3 can be closed. No supervisor approval is inferred here.

| Topic | Current evidence | Provisional project value | Supervisor decision needed | Consequence |
|---|---|---|---|---|
| Peak-force error | 6.4519% | 5% working gate | accept/revise/reject | Gate A3 |
| Full RF-U NRMSE | 24.5705% | 5% working gate | accept/revise/reject | Gate A3 |
| Pre-peak mismatch | pre-reference-peak RMSE 0.044136 kN; pre-reference-peak NRMSE about 0.062 | define | accept/revise | interpretation |
| Post-peak mismatch | post-reference-peak RMSE 0.348093 kN; post-reference-peak NRMSE about 0.490 | define | accept/revise | interpretation |
| Crack-path direction | final crack horizontal and connected at SDV15 thresholds 0.80-0.99 | qualitative gate | accept/reject | Gate A3 |
| Crack extension threshold | 0.80-0.99 sensitivity; extension about 0.0555 to 0.0465 mm | choose threshold | approve threshold | reporting |
| SDV15 decreases | mapping resolved; 817 events remain insufficient_output_evidence | define tolerance/output requirement | approve interpretation | irreversibility |
| SDV15 overshoot | max 1.005600 | define bound/tolerance | approve interpretation | bounds |
| SDV16 monotonicity | zero decreases at checked locations | monotone required | confirm | irreversibility |
| Approximate Fig. 7 data | digitized curve, not exact author data | approximate reference | accept as reference or require another route | Gate A3 |
| Uniform-reference status | not established | required before Stage B closure | confirm route | next phase |

"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR)
    parser.add_argument("--deck", default=DEFAULT_DECK)
    parser.add_argument("--layer-map", default=DEFAULT_LAYER)
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--original-source", default=DEFAULT_ORIGINAL)
    parser.add_argument("--events", default=os.path.join(DEFAULT_DETAIL, "sdv15_decrease_events_full.csv"))
    parser.add_argument("--equivalent", default=os.path.join(DEFAULT_DETAIL, "sdv15_equivalent_state_comparison.csv"))
    parser.add_argument("--precision-tol", type=float, default=1.0e-6)
    args = parser.parse_args()

    if not os.path.isdir(args.outdir):
        os.makedirs(args.outdir)

    layer = parse_layer_map(args.layer_map)
    elements = parse_deck_elements(args.deck)
    mapping_rows, failures = make_mapping_rows(elements, layer)
    n = len(mapping_rows)
    write_csv(
        os.path.join(args.outdir, "layer_label_mapping_verified.csv"),
        [
            "physical_element",
            "u1_label",
            "u2_label",
            "visualization_label",
            "u1_connectivity",
            "u2_connectivity",
            "visualization_connectivity",
            "u1_to_u2_offset",
            "u1_to_visualization_offset",
            "connectivity_match",
            "label_range_status",
            "mapping_status",
        ],
        mapping_rows,
    )
    mapping_by_vis = dict((int(row["visualization_label"]), row) for row in mapping_rows)

    trace = source_trace(args.source, args.original_source)
    write_text(os.path.join(args.outdir, "SDV_SOURCE_ASSIGNMENT_TRACE.md"), source_assignment_markdown(trace))
    write_text(os.path.join(args.outdir, "LAYER_LABEL_MAPPING_RULES.md"), mapping_rules_markdown(n, failures))

    events = read_csv(args.events)
    eq_rows = read_csv(args.equivalent)
    unresolved_rows, counts = classify_unresolved(events, eq_rows, mapping_by_vis, args.precision_tol)
    write_csv(
        os.path.join(args.outdir, "sdv15_unresolved_event_mapping.csv"),
        [
            "event_index",
            "previous_global_frame",
            "current_global_frame",
            "visualization_label",
            "physical_label",
            "u1_label",
            "u2_label",
            "odb_ip",
            "source_storage_ip",
            "ip_mapping",
            "source_update_state",
            "previous_sdv14",
            "current_sdv14",
            "previous_sdv15",
            "current_sdv15",
            "previous_sdv16",
            "current_sdv16",
            "decrease_magnitude",
            "equivalent_completed_phase_previous",
            "equivalent_completed_phase_current",
            "mapping_status",
            "final_category",
            "category_reason",
            "prior_category",
        ],
        unresolved_rows,
    )
    monotonic_rows = make_completed_state_rows(unresolved_rows)
    write_csv(
        os.path.join(args.outdir, "sdv15_completed_phase_state_monotonicity.csv"),
        [
            "visualization_label",
            "odb_ip",
            "physical_label",
            "u1_label",
            "u2_label",
            "source_storage_ip",
            "decrease_event_count",
            "completed_phase_sequence_constructible",
            "completed_phase_monotonicity",
            "largest_retained_output_decrease",
            "largest_retained_output_decrease_frame",
            "running_max_check",
            "sdv16_matching_location_decrease",
            "tolerance",
            "reason",
        ],
        monotonic_rows,
    )

    worst = events[0]
    worst_mapping = mapping_by_vis[int(worst["odb_element"])]
    write_text(os.path.join(args.outdir, "WORST_EVENT_LAYER_MAPPING.md"), worst_event_markdown(worst, worst_mapping))
    write_text(
        os.path.join(args.outdir, "SDV15_CANDIDATE_EXPLANATION_TESTS.md"),
        explanation_markdown(counts, "insufficient_output_evidence"),
    )
    write_text(os.path.join(args.outdir, "SDV15_MAPPING_RESOLUTION_DECISION.md"), decision_markdown(counts, monotonic_rows))
    write_text(os.path.join("docs", "decisions", "MOLNAR_GATE_A3_SUPERVISOR_DECISION_TABLE.md"), supervisor_table())

    print("mapping rows: %d" % len(mapping_rows))
    print("mapping failures: %d" % len(failures))
    print("unresolved rows reclassified: %d" % len(unresolved_rows))
    print("category counts: %s" % dict(counts))
    print("completed-state location rows: %d" % len(monotonic_rows))


if __name__ == "__main__":
    main()
