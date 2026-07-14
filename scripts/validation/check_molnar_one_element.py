#!/usr/bin/env python
"""Check the unchanged Molnar one-element ODB against source-defined relations.

Run with Abaqus Python, for example:

    abaqus python scripts/validation/check_molnar_one_element.py

The script reads the unchanged technical-gate ODB, extracts SDV fields for all
frames and integration points, and writes CSV/JSON/Markdown evidence. It does
not require or modify the preserved baseline source files.
"""

from __future__ import print_function

import argparse
import csv
import json
import math
import os
import sys


DEFAULT_RUN_DIR = os.path.join(
    "runs",
    "molnar_one_element_unchanged",
    "20260714_technical_gate_local",
)
DEFAULT_ODB = os.path.join(DEFAULT_RUN_DIR, "evidence", "OneElement.odb")
DEFAULT_OUTPUT_DIR = os.path.join(DEFAULT_RUN_DIR, "scientific_check")

E_MODULUS = 210.0
NU = 0.3
LENGTH_SCALE = 0.1
GC = 5.0e-3
RESIDUAL_STIFFNESS = 1.0e-7
# Provisional numerical tolerance for single-precision ODB field output values.
ABS_TOL = 1.0e-6
REL_TOL = 1.0e-5
MONOTONIC_TOL = 1.0e-9


def import_odb_access():
    try:
        from odbAccess import openOdb  # type: ignore
    except ImportError:
        print(
            "ERROR: odbAccess is unavailable. Run this script with Abaqus Python.",
            file=sys.stderr,
        )
        return None
    return openOdb


def plane_strain_matrix(e_modulus, nu):
    factor = e_modulus / ((1.0 + nu) * (1.0 - 2.0 * nu))
    return (
        (factor * (1.0 - nu), factor * nu, 0.0),
        (factor * nu, factor * (1.0 - nu), 0.0),
        (0.0, 0.0, factor * (0.5 - nu)),
    )


def mat_vec(matrix, vector):
    return [
        sum(matrix[row][col] * vector[col] for col in range(3))
        for row in range(3)
    ]


def max_abs(values):
    if not values:
        return 0.0
    return max(abs(value) for value in values)


def rel_error(actual, expected):
    denominator = max(abs(expected), ABS_TOL)
    return abs(actual - expected) / denominator


def within_tol(actual, expected, abs_tol=ABS_TOL, rel_tol=REL_TOL):
    return abs(actual - expected) <= max(abs_tol, rel_tol * max(abs(expected), ABS_TOL))


def homogeneous_phase(history):
    return (2.0 * history) / (GC / LENGTH_SCALE + 2.0 * history)


def value_data(value):
    data = value.data
    if isinstance(data, (list, tuple)):
        return float(data[0])
    return float(data)


def field_values_by_ip(frame, field_name):
    values = []
    field = frame.fieldOutputs[field_name]
    for index, value in enumerate(field.values):
        ip = getattr(value, "integrationPoint", None)
        element_label = getattr(value, "elementLabel", None)
        values.append(
            {
                "sort_key": (
                    element_label if element_label is not None else 0,
                    ip if ip is not None else index + 1,
                    index,
                ),
                "ip": ip if ip is not None else index + 1,
                "element": element_label,
                "value": value_data(value),
            }
        )
    values.sort(key=lambda item: item["sort_key"])
    return values


def extract_rows(odb_path):
    open_odb = import_odb_access()
    if open_odb is None:
        return None

    odb = open_odb(path=odb_path, readOnly=True)
    try:
        if "Static" not in odb.steps:
            raise RuntimeError("Expected step 'Static' was not found in ODB")
        step = odb.steps["Static"]
        rows = []
        required = ["SDV%d" % index for index in range(1, 17)]
        for frame_index, frame in enumerate(step.frames):
            missing = [name for name in required if name not in frame.fieldOutputs]
            if missing:
                raise RuntimeError(
                    "Frame %d is missing required field outputs: %s"
                    % (frame_index, ", ".join(missing))
                )
            fields = {name: field_values_by_ip(frame, name) for name in required}
            count = len(fields["SDV1"])
            for name in required:
                if len(fields[name]) != count:
                    raise RuntimeError(
                        "Frame %d has inconsistent value counts for %s" % (frame_index, name)
                    )
            for value_index in range(count):
                row = {
                    "frame": frame_index,
                    "time": float(frame.frameValue),
                    "element": fields["SDV1"][value_index]["element"],
                    "ip": fields["SDV1"][value_index]["ip"],
                }
                for sdv_index in range(1, 17):
                    row["sdv%d" % sdv_index] = fields["SDV%d" % sdv_index][value_index]["value"]
                rows.append(row)
        return rows
    finally:
        odb.close()


def add_expected_values(rows):
    matrix = plane_strain_matrix(E_MODULUS, NU)
    for row in rows:
        strain = [row["sdv3"], row["sdv4"], row["sdv5"]]
        elastic = mat_vec(matrix, strain)
        degradation = ((1.0 - row["sdv14"]) ** 2.0) + RESIDUAL_STIFFNESS
        phase_expected = homogeneous_phase(row["sdv16"])
        for index, value in enumerate(elastic, start=1):
            row["expected_sdv%d" % (8 + index)] = value
            row["expected_sdv%d" % (5 + index)] = degradation * value
        row["degradation_from_sdv14"] = degradation
        row["expected_sdv15"] = phase_expected
        row["sdv14_minus_sdv15"] = row["sdv14"] - row["sdv15"]
    return rows


def rows_by_frame(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row["frame"], []).append(row)
    return grouped


def metric_errors(rows, actual_names, expected_names):
    result = {}
    for actual_name, expected_name in zip(actual_names, expected_names):
        abs_errors = [abs(row[actual_name] - row[expected_name]) for row in rows]
        rel_errors = [rel_error(row[actual_name], row[expected_name]) for row in rows]
        result[actual_name] = {
            "max_abs_error": max_abs(abs_errors),
            "max_rel_error": max_abs(rel_errors),
            "pass": all(
                within_tol(row[actual_name], row[expected_name]) for row in rows
            ),
        }
    return result


def max_frame_range(rows, names):
    grouped = rows_by_frame(rows)
    result = {}
    for name in names:
        ranges = []
        for frame_rows in grouped.values():
            values = [row[name] for row in frame_rows]
            ranges.append(max(values) - min(values))
        result[name] = max_abs(ranges)
    return result


def monotonic_check(rows, name, start_time=None, end_time=None):
    grouped = rows_by_frame(rows)
    ip_keys = sorted(set((row["element"], row["ip"]) for row in rows))
    worst_drop = 0.0
    pass_check = True
    for key in ip_keys:
        sequence = []
        for frame_index in sorted(grouped):
            matches = [
                row
                for row in grouped[frame_index]
                if (row["element"], row["ip"]) == key
            ]
            if not matches:
                continue
            row = matches[0]
            time = row["time"]
            if start_time is not None and time < start_time - 1.0e-12:
                continue
            if end_time is not None and time > end_time + 1.0e-12:
                continue
            sequence.append(row[name])
        for previous, current in zip(sequence[:-1], sequence[1:]):
            drop = previous - current
            if drop > worst_drop:
                worst_drop = drop
            if drop > MONOTONIC_TOL:
                pass_check = False
    return {"pass": pass_check, "worst_drop": worst_drop}


def first_nonzero_frame(rows):
    grouped = rows_by_frame(rows)
    for frame_index in sorted(grouped):
        frame_rows = grouped[frame_index]
        if max_abs([row["sdv4"] for row in frame_rows]) > 1.0e-12:
            return frame_index, frame_rows
    return None, []


def build_summary(rows):
    elastic_errors = metric_errors(
        rows,
        ["sdv9", "sdv10", "sdv11"],
        ["expected_sdv9", "expected_sdv10", "expected_sdv11"],
    )
    degraded_errors = metric_errors(
        rows,
        ["sdv6", "sdv7", "sdv8"],
        ["expected_sdv6", "expected_sdv7", "expected_sdv8"],
    )
    phase_errors = metric_errors(rows, ["sdv15"], ["expected_sdv15"])
    consistency_names = [
        "sdv3",
        "sdv4",
        "sdv5",
        "sdv6",
        "sdv7",
        "sdv8",
        "sdv9",
        "sdv10",
        "sdv11",
        "sdv12",
        "sdv13",
        "sdv14",
        "sdv15",
        "sdv16",
    ]
    consistency = max_frame_range(rows, consistency_names)
    consistency_pass = all(value <= 1.0e-6 for value in consistency.values())
    history_monotonic = monotonic_check(rows, "sdv16")
    unloading_phase = monotonic_check(rows, "sdv15", start_time=0.2, end_time=0.4)
    frame_index, frame_rows = first_nonzero_frame(rows)
    matrix = plane_strain_matrix(E_MODULUS, NU)
    stiffness_sample = {}
    if frame_rows:
        sample = frame_rows[0]
        stiffness_sample = {
            "frame": frame_index,
            "time": sample["time"],
            "strain": [sample["sdv3"], sample["sdv4"], sample["sdv5"]],
            "sdv9_to_sdv11": [sample["sdv9"], sample["sdv10"], sample["sdv11"]],
            "expected_c_times_strain": [
                sample["expected_sdv9"],
                sample["expected_sdv10"],
                sample["expected_sdv11"],
            ],
            "plane_strain_matrix": matrix,
        }

    sdv14_sdv15_abs = [abs(row["sdv14_minus_sdv15"]) for row in rows]
    max_diff = max_abs(sdv14_sdv15_abs)
    max_diff_row = max(rows, key=lambda row: abs(row["sdv14_minus_sdv15"]))
    checks = {
        "initial_plane_strain_stiffness": all(item["pass"] for item in elastic_errors.values()),
        "undamaged_stress_matches_plane_strain": all(
            item["pass"] for item in elastic_errors.values()
        ),
        "degraded_stress_matches_sdv14_degradation": all(
            item["pass"] for item in degraded_errors.values()
        ),
        "sdv15_matches_homogeneous_phase_relation": phase_errors["sdv15"]["pass"],
        "sdv16_monotonic": history_monotonic["pass"],
        "sdv15_non_decreasing_during_unloading_0p2_to_0p4": unloading_phase["pass"],
        "integration_point_consistency_excluding_local_displacements": consistency_pass,
    }
    return {
        "classification": "scientific_pass" if all(checks.values()) else "scientific_review_required",
        "parameters": {
            "E": E_MODULUS,
            "nu": NU,
            "length_scale": LENGTH_SCALE,
            "Gc": GC,
            "residual_stiffness": RESIDUAL_STIFFNESS,
            "abs_tolerance": ABS_TOL,
            "rel_tolerance": REL_TOL,
            "monotonic_tolerance": MONOTONIC_TOL,
        },
        "row_count": len(rows),
        "frame_count": len(rows_by_frame(rows)),
        "integration_points_per_frame": len(rows) // len(rows_by_frame(rows)),
        "checks": checks,
        "elastic_errors": elastic_errors,
        "degraded_errors": degraded_errors,
        "phase_errors": phase_errors,
        "history_monotonic": history_monotonic,
        "unloading_phase_monotonic": unloading_phase,
        "integration_point_max_ranges": consistency,
        "stiffness_sample": stiffness_sample,
        "sdv14_sdv15_difference": {
            "max_abs": max_diff,
            "at_frame": max_diff_row["frame"],
            "at_time": max_diff_row["time"],
            "at_ip": max_diff_row["ip"],
            "signed_sdv14_minus_sdv15": max_diff_row["sdv14_minus_sdv15"],
        },
    }


def write_csv(path, rows):
    fieldnames = [
        "frame",
        "time",
        "element",
        "ip",
    ]
    fieldnames.extend("sdv%d" % index for index in range(1, 17))
    fieldnames.extend(
        [
            "expected_sdv6",
            "expected_sdv7",
            "expected_sdv8",
            "expected_sdv9",
            "expected_sdv10",
            "expected_sdv11",
            "expected_sdv15",
            "degradation_from_sdv14",
            "sdv14_minus_sdv15",
        ]
    )
    with open(path, "w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def format_metric_table(title, metrics):
    lines = [title, "", "| Quantity | Max abs error | Max rel error | Pass |", "|---|---:|---:|---|"]
    for name in sorted(metrics):
        item = metrics[name]
        lines.append(
            "| `%s` | %.6e | %.6e | `%s` |"
            % (name.upper(), item["max_abs_error"], item["max_rel_error"], item["pass"])
        )
    lines.append("")
    return lines


def write_markdown(path, summary, odb_path, csv_name, json_name):
    checks = summary["checks"]
    lines = [
        "# Molnar One-Element Scientific Check",
        "",
        "Date: 2026-07-14",
        "",
        "Classification: `%s`" % summary["classification"],
        "",
        "## Scope",
        "",
        "This is a quantitative check of the unchanged Molnar and Gravouil one-element run. It reads the technical-gate ODB and compares the UMAT visualization SDVs against relations implemented in the supplied source. It is not a remeshing or full benchmark validation.",
        "",
        "ODB: `%s`" % odb_path.replace("\\", "/"),
        "",
        "Companion outputs:",
        "",
        "- `%s`" % csv_name,
        "- `%s`" % json_name,
        "",
        "## Source-Defined Mapping",
        "",
        "| ODB variable | Quantity |",
        "|---|---|",
        "| `SDV1`, `SDV2` | Local displacement components |",
        "| `SDV3`-`SDV5` | Strain components `(epsilon11, epsilon22, gamma12)` |",
        "| `SDV6`-`SDV8` | Degraded stresses |",
        "| `SDV9`-`SDV11` | Undamaged elastic stresses |",
        "| `SDV12` | Degraded elastic energy |",
        "| `SDV13` | Undamaged elastic energy / current driving energy |",
        "| `SDV14` | Phase field used by the displacement element |",
        "| `SDV15` | Phase field from the phase-field element |",
        "| `SDV16` | Maximum energy-history field |",
        "",
        "## Checks",
        "",
        "| Check | Result |",
        "|---|---|",
    ]
    for name in sorted(checks):
        lines.append("| `%s` | `%s` |" % (name, checks[name]))
    lines.extend([""])
    lines.extend(format_metric_table("## Undamaged Stress vs Plane-Strain Elasticity", summary["elastic_errors"]))
    lines.extend(format_metric_table("## Degraded Stress vs `SDV14` Degradation", summary["degraded_errors"]))
    lines.extend(format_metric_table("## Phase Field vs Homogeneous Relation", summary["phase_errors"]))
    lines.extend(
        [
            "## Irreversibility",
            "",
            "- `SDV16` monotonic: `%s`; worst drop `%.6e`"
            % (
                summary["history_monotonic"]["pass"],
                summary["history_monotonic"]["worst_drop"],
            ),
            "- `SDV15` non-decreasing during unloading from `t=0.2` to `t=0.4`: `%s`; worst drop `%.6e`"
            % (
                summary["unloading_phase_monotonic"]["pass"],
                summary["unloading_phase_monotonic"]["worst_drop"],
            ),
            "",
            "## Integration-Point Consistency",
            "",
            "The consistency check excludes `SDV1` and `SDV2` because they are local displacement components and may differ by integration-point position. All strain, stress, energy, phase, and history SDVs are checked across the four integration points in each frame.",
            "",
            "| Quantity | Max range across integration points |",
            "|---|---:|",
        ]
    )
    for name in sorted(summary["integration_point_max_ranges"]):
        lines.append(
            "| `%s` | %.6e |"
            % (name.upper(), summary["integration_point_max_ranges"][name])
        )
    diff = summary["sdv14_sdv15_difference"]
    lines.extend(
        [
            "",
            "## `SDV14` / `SDV15` Staggering Note",
            "",
            "`SDV14` is the phase field used by the displacement element when stress and degraded energy are computed. `SDV15` is the phase field stored by the phase-field element. Differences are therefore recorded as staggered-update evidence, not treated automatically as an error.",
            "",
            "- Maximum absolute `SDV14 - SDV15`: `%.6e`" % diff["max_abs"],
            "- Location: frame `%s`, time `%.6f`, integration point `%s`"
            % (diff["at_frame"], diff["at_time"], diff["at_ip"]),
            "- Signed value at that location: `%.6e`" % diff["signed_sdv14_minus_sdv15"],
            "",
            "## Initial Stiffness Sample",
            "",
            "Plane-strain constitutive matrix used by the source:",
            "",
            "```text",
        ]
    )
    matrix = summary["stiffness_sample"]["plane_strain_matrix"]
    for row in matrix:
        lines.append("% .12e  % .12e  % .12e" % (row[0], row[1], row[2]))
    sample = summary["stiffness_sample"]
    lines.extend(
        [
            "```",
            "",
            "First nonzero-strain frame: `%s` at time `%.6f`."
            % (sample["frame"], sample["time"]),
            "",
            "| Quantity | Value | Expected |",
            "|---|---:|---:|",
        ]
    )
    for name, value, expected in zip(
        ["SDV9", "SDV10", "SDV11"],
        sample["sdv9_to_sdv11"],
        sample["expected_c_times_strain"],
    ):
        lines.append("| `%s` | %.12e | %.12e |" % (name, value, expected))
    lines.append("")
    with open(path, "w") as stream:
        stream.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odb", default=DEFAULT_ODB, help="Path to OneElement.odb")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for CSV, JSON, and Markdown evidence",
    )
    args = parser.parse_args()

    odb_path = os.path.abspath(args.odb)
    output_dir = os.path.abspath(args.output_dir)
    if not os.path.exists(odb_path):
        print("ERROR: ODB does not exist: %s" % odb_path, file=sys.stderr)
        return 2
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    rows = extract_rows(odb_path)
    if rows is None:
        return 2
    add_expected_values(rows)
    summary = build_summary(rows)

    csv_path = os.path.join(output_dir, "one_element_sdv_scientific_check.csv")
    json_path = os.path.join(output_dir, "one_element_scientific_check.json")
    md_path = os.path.join(output_dir, "ONE_ELEMENT_SCIENTIFIC_CHECK.md")

    write_csv(csv_path, rows)
    with open(json_path, "w") as stream:
        json.dump(summary, stream, indent=2, sort_keys=True)
        stream.write("\n")
    write_markdown(
        md_path,
        summary,
        os.path.relpath(odb_path, os.getcwd()),
        os.path.basename(csv_path),
        os.path.basename(json_path),
    )

    print("Classification: %s" % summary["classification"])
    print("Markdown: %s" % md_path)
    print("JSON: %s" % json_path)
    print("CSV: %s" % csv_path)
    return 0 if summary["classification"] == "scientific_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
