#!/usr/bin/env python
"""Extract RF-U and phase-field summaries from the unchanged Molnar single-notch ODB.

Run with Abaqus Python:

    abaqus python scripts/postprocessing/extract_molnar_single_notch.py

The script is intentionally read-only with respect to the ODB. It writes
lightweight CSV/JSON/Markdown evidence for the unchanged benchmark technical
gate and first scientific-review extraction.
"""

from __future__ import print_function

import argparse
import csv
import json
import os
import re
import sys


DEFAULT_RUN_DIR = os.path.join(
    "runs",
    "molnar_single_notch_unchanged",
    "20260714_technical_gate_local",
)
DEFAULT_ODB = os.path.join(DEFAULT_RUN_DIR, "work", "SingleNotch.odb")
DEFAULT_STA = os.path.join(DEFAULT_RUN_DIR, "work", "SingleNotch.sta")
DEFAULT_DAT = os.path.join(DEFAULT_RUN_DIR, "work", "SingleNotch.dat")
DEFAULT_MSG = os.path.join(DEFAULT_RUN_DIR, "work", "SingleNotch.msg")
DEFAULT_OUTPUT_DIR = os.path.join(DEFAULT_RUN_DIR, "extracted")
DEFAULT_TARGET_DISPLACEMENTS = [0.002, 0.005, 0.006, 0.007]


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


def value_component(value, component_index):
    data = value.data
    try:
        return float(data[component_index])
    except (TypeError, IndexError):
        return float(data)


def scalar_value(value):
    data = value.data
    try:
        return float(data[0])
    except (TypeError, IndexError):
        return float(data)


def get_single_subset_value(field, region):
    subset = field.getSubset(region=region)
    if not subset.values:
        return None
    return subset.values[0]


def max_scalar(field):
    if not field.values:
        return None
    return max(scalar_value(value) for value in field.values)


def extract_odb(odb_path, targets):
    open_odb = import_odb_access()
    if open_odb is None:
        return None

    odb = open_odb(path=odb_path, readOnly=True)
    try:
        assembly = odb.rootAssembly
        if "RP" not in assembly.nodeSets:
            raise RuntimeError("Assembly node set RP was not found in ODB")
        rp = assembly.nodeSets["RP"]
        curve_rows = []
        contour_candidates = []
        field_names_by_step = {}
        history_names_by_step = {}
        element_count = 0
        node_count = 0
        if assembly.instances:
            for instance in assembly.instances.values():
                element_count += len(instance.elements)
                node_count += len(instance.nodes)
        for step_name, step in odb.steps.items():
            history_names = []
            for region in step.historyRegions.values():
                for output_name in region.historyOutputs.keys():
                    if output_name not in history_names:
                        history_names.append(output_name)
            history_names_by_step[step_name] = sorted(history_names)
            for frame_index, frame in enumerate(step.frames):
                field_names_by_step.setdefault(step_name, sorted(frame.fieldOutputs.keys()))
                row = {
                    "step": step_name,
                    "frame": frame_index,
                    "step_time": float(frame.frameValue),
                    "description": frame.description,
                    "rp_u2": "",
                    "rp_rf2": "",
                    "max_sdv14": "",
                    "max_sdv15": "",
                    "max_sdv16": "",
                }
                if "U" in frame.fieldOutputs:
                    value = get_single_subset_value(frame.fieldOutputs["U"], rp)
                    if value is not None:
                        row["rp_u2"] = value_component(value, 1)
                if "RF" in frame.fieldOutputs:
                    value = get_single_subset_value(frame.fieldOutputs["RF"], rp)
                    if value is not None:
                        row["rp_rf2"] = value_component(value, 1)
                for sdv_name in ["SDV14", "SDV15", "SDV16"]:
                    if sdv_name in frame.fieldOutputs:
                        row["max_%s" % sdv_name.lower()] = max_scalar(frame.fieldOutputs[sdv_name])
                curve_rows.append(row)
                if row["rp_u2"] != "":
                    contour_candidates.append((abs(abs(row["rp_u2"]) - abs_target(row["rp_u2"])), row))

        matched_rows = []
        for target in targets:
            candidates = [
                (abs(abs(row["rp_u2"]) - target), row)
                for row in curve_rows
                if row["rp_u2"] != ""
            ]
            if not candidates:
                continue
            candidates.sort(key=lambda item: item[0])
            match = dict(candidates[0][1])
            match["target_abs_u2"] = target
            match["abs_u2_error"] = candidates[0][0]
            matched_rows.append(match)

        return {
            "curve_rows": curve_rows,
            "matched_rows": matched_rows,
            "field_names_by_step": field_names_by_step,
            "history_names_by_step": history_names_by_step,
            "element_count": element_count,
            "node_count": node_count,
        }
    finally:
        odb.close()


def abs_target(value):
    return abs(float(value))


def extract_contours(odb_path, matched_rows, output_dir):
    open_odb = import_odb_access()
    if open_odb is None:
        return []
    odb = open_odb(path=odb_path, readOnly=True)
    written = []
    try:
        for index, match in enumerate(matched_rows, start=1):
            step = odb.steps[match["step"]]
            frame = step.frames[int(match["frame"])]
            path = os.path.join(
                output_dir,
                "matched_state_%02d_%s_frame_%04d_contour_sdv14_sdv15_sdv16.csv"
                % (index, match["step"], int(match["frame"])),
            )
            field_data = {}
            for name in ["SDV14", "SDV15", "SDV16"]:
                if name in frame.fieldOutputs:
                    for value_index, value in enumerate(frame.fieldOutputs[name].values):
                        key = (
                            getattr(value, "elementLabel", None),
                            getattr(value, "integrationPoint", None),
                            value_index,
                        )
                        field_data.setdefault(key, {})[name.lower()] = scalar_value(value)
            with open(path, "w", newline="") as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=[
                        "step",
                        "frame",
                        "step_time",
                        "target_abs_u2",
                        "rp_u2",
                        "rp_rf2",
                        "element",
                        "integration_point",
                        "sdv14",
                        "sdv15",
                        "sdv16",
                    ],
                )
                writer.writeheader()
                for key in sorted(field_data):
                    element, ip, _ = key
                    values = field_data[key]
                    writer.writerow(
                        {
                            "step": match["step"],
                            "frame": match["frame"],
                            "step_time": match["step_time"],
                            "target_abs_u2": match["target_abs_u2"],
                            "rp_u2": match["rp_u2"],
                            "rp_rf2": match["rp_rf2"],
                            "element": element,
                            "integration_point": ip,
                            "sdv14": values.get("sdv14", ""),
                            "sdv15": values.get("sdv15", ""),
                            "sdv16": values.get("sdv16", ""),
                        }
                    )
            written.append(os.path.basename(path))
        return written
    finally:
        odb.close()


def read_text(path):
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", errors="replace") as stream:
        return stream.read()


def parse_warnings(dat_text):
    warnings = []
    lines = dat_text.splitlines()
    for index, line in enumerate(lines):
        if "***WARNING" in line:
            snippet = [line.strip()]
            if index + 1 < len(lines):
                snippet.append(lines[index + 1].strip())
            warnings.append(" ".join(snippet).strip())
    return warnings


def parse_status(sta_text):
    return {
        "analysis_completed_successfully": "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in sta_text,
        "errors_seen": bool(re.search(r"\bERROR\b", sta_text, re.IGNORECASE)),
        "warning_lines_seen": bool(re.search(r"\bWARNING\b", sta_text, re.IGNORECASE)),
        "sta_line_count": len(sta_text.splitlines()),
    }


def parse_job_time(dat_text):
    summaries = []
    lines = dat_text.splitlines()
    for index, line in enumerate(lines):
        if "JOB TIME SUMMARY" in line:
            summaries.append("\n".join(lines[index : index + 8]))
    return summaries


def write_curve_csv(path, rows):
    fieldnames = [
        "step",
        "frame",
        "step_time",
        "rp_u2",
        "rp_rf2",
        "max_sdv14",
        "max_sdv15",
        "max_sdv16",
        "description",
    ]
    with open(path, "w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def write_matched_csv(path, rows):
    fieldnames = [
        "target_abs_u2",
        "abs_u2_error",
        "step",
        "frame",
        "step_time",
        "rp_u2",
        "rp_rf2",
        "max_sdv14",
        "max_sdv15",
        "max_sdv16",
    ]
    with open(path, "w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def write_markdown(path, summary, curve_name, matched_name, contour_names):
    lines = [
        "# Molnar Single-Notch Extraction",
        "",
        "Date: 2026-07-14",
        "",
        "Classification: `%s`" % summary["classification"],
        "",
        "## Scope",
        "",
        "This extraction reads the unchanged Molnar single-notch ODB and records the first benchmark technical evidence plus RF-U and phase/history summaries. It does not compare the curve or crack evolution against the paper yet.",
        "",
        "## Technical Status",
        "",
        "- ODB readable: `%s`" % summary["odb_readable"],
        "- Analysis completed successfully in `.sta`: `%s`"
        % summary["status"]["analysis_completed_successfully"],
        "- Node count: `%s`" % summary["node_count"],
        "- Element count: `%s`" % summary["element_count"],
        "- Curve rows: `%s`" % summary["curve_row_count"],
        "",
        "## Outputs",
        "",
        "- `%s`" % curve_name,
        "- `%s`" % matched_name,
    ]
    for name in contour_names:
        lines.append("- `%s`" % name)
    lines.extend(
        [
            "",
            "## Matched Displacement States",
            "",
            "| Target abs U2 | Matched step | Frame | U2 | RF2 | Max SDV15 | Max SDV16 |",
            "|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in summary["matched_rows"]:
        lines.append(
            "| %.6e | `%s` | %s | %.6e | %.6e | %.6e | %.6e |"
            % (
                row["target_abs_u2"],
                row["step"],
                row["frame"],
                row["rp_u2"],
                row["rp_rf2"],
                row["max_sdv15"],
                row["max_sdv16"],
            )
        )
    lines.extend(["", "## Warnings", ""])
    if summary["warnings"]:
        for warning in summary["warnings"]:
            lines.append("- %s" % warning)
    else:
        lines.append("- None found in `.dat`.")
    lines.extend(["", "## Field Outputs By Step", ""])
    for step, fields in summary["field_names_by_step"].items():
        lines.append("- `%s`: `%s`" % (step, ", ".join(fields)))
    lines.extend(["", "## History Outputs By Step", ""])
    for step, fields in summary["history_names_by_step"].items():
        lines.append("- `%s`: `%s`" % (step, ", ".join(fields) if fields else "none"))
    lines.extend(["", "## Job Time Summary", ""])
    for item in summary["job_time_summaries"]:
        lines.extend(["```text", item, "```", ""])
    with open(path, "w") as stream:
        stream.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odb", default=DEFAULT_ODB)
    parser.add_argument("--sta", default=DEFAULT_STA)
    parser.add_argument("--dat", default=DEFAULT_DAT)
    parser.add_argument("--msg", default=DEFAULT_MSG)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--target-displacements",
        default=",".join(str(value) for value in DEFAULT_TARGET_DISPLACEMENTS),
        help="Comma-separated absolute RP U2 targets for contour extraction",
    )
    args = parser.parse_args()

    targets = [float(item.strip()) for item in args.target_displacements.split(",") if item.strip()]
    output_dir = os.path.abspath(args.output_dir)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    extracted = extract_odb(os.path.abspath(args.odb), targets)
    if extracted is None:
        return 2

    contour_names = extract_contours(os.path.abspath(args.odb), extracted["matched_rows"], output_dir)
    curve_path = os.path.join(output_dir, "single_notch_rf_u_phase_summary.csv")
    matched_path = os.path.join(output_dir, "single_notch_matched_displacement_states.csv")
    json_path = os.path.join(output_dir, "single_notch_extraction_summary.json")
    md_path = os.path.join(output_dir, "SINGLE_NOTCH_EXTRACTION.md")

    write_curve_csv(curve_path, extracted["curve_rows"])
    write_matched_csv(matched_path, extracted["matched_rows"])

    sta_text = read_text(args.sta)
    dat_text = read_text(args.dat)
    summary = {
        "classification": "technical_pass_scientific_unchecked",
        "odb_readable": True,
        "status": parse_status(sta_text),
        "warnings": parse_warnings(dat_text),
        "job_time_summaries": parse_job_time(dat_text),
        "field_names_by_step": extracted["field_names_by_step"],
        "history_names_by_step": extracted["history_names_by_step"],
        "element_count": extracted["element_count"],
        "node_count": extracted["node_count"],
        "curve_row_count": len(extracted["curve_rows"]),
        "matched_rows": extracted["matched_rows"],
        "contour_files": contour_names,
    }

    with open(json_path, "w") as stream:
        json.dump(summary, stream, indent=2, sort_keys=True)
        stream.write("\n")
    write_markdown(
        md_path,
        summary,
        os.path.basename(curve_path),
        os.path.basename(matched_path),
        contour_names,
    )

    print("Classification: %s" % summary["classification"])
    print("Markdown: %s" % md_path)
    print("JSON: %s" % json_path)
    print("Curve CSV: %s" % curve_path)
    print("Matched states CSV: %s" % matched_path)
    print("Contour CSV files: %d" % len(contour_names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
