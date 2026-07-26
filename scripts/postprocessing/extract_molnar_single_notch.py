#!/usr/bin/env python
"""Extract RF-U, phase-field summaries, and crack-path data from Molnar single-notch ODB.

Run with Abaqus Python:

    abaqus python scripts/postprocessing/extract_molnar_single_notch.py

Backward-compatible CLI options allow configuring displacement/reaction components,
RP set name, phase/history variables, and threshold for Mode-I and Mode-II extractions.
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


def extract_odb(
    odb_path,
    targets,
    disp_comp=2,
    react_comp=2,
    rp_set_name="RP",
    phase_var="SDV15",
    history_var="SDV16",
    path_threshold=0.5,
):
    open_odb = import_odb_access()
    if open_odb is None:
        return None

    odb = open_odb(path=odb_path, readOnly=True)
    try:
        assembly = odb.rootAssembly
        if rp_set_name not in assembly.nodeSets:
            raise RuntimeError("Assembly node set %s was not found in ODB" % rp_set_name)
        rp = assembly.nodeSets[rp_set_name]
        curve_rows = []
        field_names_by_step = {}
        history_names_by_step = {}
        element_count = 0
        node_count = 0
        if assembly.instances:
            for instance in assembly.instances.values():
                element_count += len(instance.elements)
                node_count += len(instance.nodes)

        disp_key = "rp_u%d" % disp_comp
        react_key = "rp_rf%d" % react_comp
        disp_idx = disp_comp - 1
        react_idx = react_comp - 1

        energy_rows = []
        energy_vars = ["ALLAE", "ALLCD", "ALLIE", "ALLKE", "ALLPD", "ALLSE", "ALLWK", "ETOTAL"]

        for step_name, step in odb.steps.items():
            history_names = []
            for region in step.historyRegions.values():
                for output_name, history_output in region.historyOutputs.items():
                    if output_name not in history_names:
                        history_names.append(output_name)
                    if output_name in energy_vars or output_name.startswith("ALL") or output_name == "ETOTAL":
                        for time_val, data_val in history_output.data:
                            energy_rows.append(
                                {
                                    "step": step_name,
                                    "step_time": float(time_val),
                                    "variable": output_name,
                                    "value": float(data_val),
                                }
                            )
            history_names_by_step[step_name] = sorted(history_names)

            for frame_index, frame in enumerate(step.frames):
                field_names_by_step.setdefault(step_name, sorted(frame.fieldOutputs.keys()))
                row = {
                    "step": step_name,
                    "frame": frame_index,
                    "step_time": float(frame.frameValue),
                    "description": frame.description,
                    disp_key: "",
                    react_key: "",
                    "max_sdv14": "",
                    "max_sdv15": "",
                    "max_sdv16": "",
                }
                if disp_key != "rp_u2":
                    row["rp_u2"] = ""
                if react_key != "rp_rf2":
                    row["rp_rf2"] = ""

                if "U" in frame.fieldOutputs:
                    value = get_single_subset_value(frame.fieldOutputs["U"], rp)
                    if value is not None:
                        row[disp_key] = value_component(value, disp_idx)
                        if "rp_u2" in row:
                            row["rp_u2"] = value_component(value, 1)
                if "RF" in frame.fieldOutputs:
                    value = get_single_subset_value(frame.fieldOutputs["RF"], rp)
                    if value is not None:
                        row[react_key] = value_component(value, react_idx)
                        if "rp_rf2" in row:
                            row["rp_rf2"] = value_component(value, 1)

                for sdv_name in ["SDV14", "SDV15", "SDV16"]:
                    if sdv_name in frame.fieldOutputs:
                        row["max_%s" % sdv_name.lower()] = max_scalar(frame.fieldOutputs[sdv_name])
                curve_rows.append(row)

        matched_rows = []
        for target in targets:
            candidates = [
                (abs(abs(row[disp_key]) - target), row)
                for row in curve_rows
                if row[disp_key] != ""
            ]
            if not candidates:
                continue
            candidates.sort(key=lambda item: item[0])
            match = dict(candidates[0][1])
            match["target_abs_u"] = target
            match["target_abs_u2"] = target
            match["abs_u_error"] = candidates[0][0]
            match["abs_u2_error"] = candidates[0][0]
            matched_rows.append(match)

        # Extract crack path elements where phase_var >= path_threshold in the final frame
        crack_path_rows = []
        if odb.steps:
            step_keys = list(odb.steps.keys())
            if step_keys:
                last_step_name = step_keys[-1]
                last_step = odb.steps[last_step_name]
                if last_step.frames:
                    last_frame = last_step.frames[-1]
                    if phase_var in last_frame.fieldOutputs:
                        fo = last_frame.fieldOutputs[phase_var]
                        elem_phase = {}
                        for val in fo.values:
                            elem_id = getattr(val, "elementLabel", None)
                            if elem_id is not None:
                                val_f = scalar_value(val)
                                if elem_id not in elem_phase or val_f > elem_phase[elem_id]:
                                    elem_phase[elem_id] = val_f
                        for elem_id, phase_val in sorted(elem_phase.items()):
                            if phase_val >= path_threshold:
                                crack_path_rows.append(
                                    {
                                        "element": elem_id,
                                        "phase_variable": phase_var,
                                        "phase_value": phase_val,
                                        "threshold": path_threshold,
                                        "step": last_step_name,
                                        "frame": len(last_step.frames) - 1,
                                    }
                                )

        # Irreversibility and Phase Bounds checking across element integration points
        phase_min = float("inf")
        phase_max = float("-inf")
        values_checked = 0

        prev_elem_ip_phase = {}
        prev_elem_ip_hist = {}
        phase_healing_violations = 0
        worst_phase_decrease = 0.0
        history_decrease_violations = 0
        worst_history_decrease = 0.0

        healing_tolerance = 1e-8
        history_decrease_tolerance = 1e-10

        for step_name, step in odb.steps.items():
            for frame_index, frame in enumerate(step.frames):
                if phase_var in frame.fieldOutputs:
                    fo_p = frame.fieldOutputs[phase_var]
                    curr_phase_map = {}
                    for val in fo_p.values:
                        elem_id = getattr(val, "elementLabel", None)
                        ip_id = getattr(val, "integrationPoint", None)
                        if elem_id is not None:
                            key = (elem_id, ip_id)
                            f_val = scalar_value(val)
                            curr_phase_map[key] = f_val
                            if f_val < phase_min:
                                phase_min = f_val
                            if f_val > phase_max:
                                phase_max = f_val
                            values_checked += 1

                    if prev_elem_ip_phase:
                        for key, curr_p in curr_phase_map.items():
                            if key in prev_elem_ip_phase:
                                prev_p = prev_elem_ip_phase[key]
                                if curr_p < prev_p - healing_tolerance:
                                    phase_healing_violations += 1
                                    dec = prev_p - curr_p
                                    if dec > worst_phase_decrease:
                                        worst_phase_decrease = dec
                    prev_elem_ip_phase = curr_phase_map

                if history_var in frame.fieldOutputs:
                    fo_h = frame.fieldOutputs[history_var]
                    curr_hist_map = {}
                    for val in fo_h.values:
                        elem_id = getattr(val, "elementLabel", None)
                        ip_id = getattr(val, "integrationPoint", None)
                        if elem_id is not None:
                            key = (elem_id, ip_id)
                            f_val = scalar_value(val)
                            curr_hist_map[key] = f_val

                    if prev_elem_ip_hist:
                        for key, curr_h in curr_hist_map.items():
                            if key in prev_elem_ip_hist:
                                prev_h = prev_elem_ip_hist[key]
                                if curr_h < prev_h - history_decrease_tolerance:
                                    history_decrease_violations += 1
                                    dec = prev_h - curr_h
                                    if dec > worst_history_decrease:
                                        worst_history_decrease = dec
                    prev_elem_ip_hist = curr_hist_map

        if values_checked == 0:
            phase_min = 0.0
            phase_max = 0.0

        irreversibility_summary = {
            "phase_healing_violation_count": phase_healing_violations,
            "worst_phase_decrease": worst_phase_decrease,
            "history_decrease_violation_count": history_decrease_violations,
            "worst_history_decrease": worst_history_decrease,
            "healing_tolerance": healing_tolerance,
            "history_decrease_tolerance": history_decrease_tolerance,
        }

        phase_bounds_summary = {
            "minimum_phase": phase_min,
            "maximum_phase": phase_max,
            "values_checked": values_checked,
        }

        return {
            "curve_rows": curve_rows,
            "matched_rows": matched_rows,
            "crack_path_rows": crack_path_rows,
            "energy_rows": energy_rows,
            "irreversibility_summary": irreversibility_summary,
            "phase_bounds_summary": phase_bounds_summary,
            "field_names_by_step": field_names_by_step,
            "history_names_by_step": history_names_by_step,
            "element_count": element_count,
            "node_count": node_count,
            "disp_key": disp_key,
            "react_key": react_key,
        }
    finally:
        odb.close()


def extract_contours(
    odb_path,
    matched_rows,
    output_dir,
    disp_comp=2,
    react_comp=2,
    phase_var="SDV15",
    history_var="SDV16",
):
    open_odb = import_odb_access()
    if open_odb is None:
        return []
    odb = open_odb(path=odb_path, readOnly=True)
    written = []
    disp_key = "rp_u%d" % disp_comp
    react_key = "rp_rf%d" % react_comp
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
            with open(path, "w") as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=[
                        "step",
                        "frame",
                        "step_time",
                        "target_abs_u",
                        disp_key,
                        react_key,
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
                            "target_abs_u": match.get("target_abs_u", match.get("target_abs_u2", "")),
                            disp_key: match.get(disp_key, ""),
                            react_key: match.get(react_key, ""),
                            "element": element,
                            "integration_point": ip,
                            "sdv14": values.get("sdv14", ""),
                            "sdv15": values.get("sdv15", ""),
                            "sdv16": values.get("sdv16", ""),
                        }
                    )
            written.append(os.path.basename(path))

        # Also write consolidated sdv14_sdv15_sdv16_contours.csv if written files exist
        if written:
            consolidated_path = os.path.join(output_dir, "sdv14_sdv15_sdv16_contours.csv")
            with open(consolidated_path, "w") as out_stream:
                header_written = False
                for fname in written:
                    fpath = os.path.join(output_dir, fname)
                    with open(fpath, "r") as in_stream:
                        for line_idx, line in enumerate(in_stream):
                            if line_idx == 0:
                                if not header_written:
                                    out_stream.write(line)
                                    header_written = True
                            else:
                                out_stream.write(line)

        return written
    finally:
        odb.close()


def read_text(path):
    if not path or not os.path.exists(path):
        return ""
    with open(path, "rb") as stream:
        return stream.read().decode("utf-8", "replace")


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


def write_curve_csv(path, rows, disp_comp=2, react_comp=2):
    disp_key = "rp_u%d" % disp_comp
    react_key = "rp_rf%d" % react_comp
    fieldnames = [
        "step",
        "frame",
        "step_time",
        disp_key,
        react_key,
        "max_sdv14",
        "max_sdv15",
        "max_sdv16",
        "description",
    ]
    if "rp_u2" not in fieldnames and any("rp_u2" in r for r in rows):
        fieldnames.insert(3, "rp_u2")
    if "rp_rf2" not in fieldnames and any("rp_rf2" in r for r in rows):
        fieldnames.insert(4, "rp_rf2")

    with open(path, "w") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def write_matched_csv(path, rows, disp_comp=2, react_comp=2):
    disp_key = "rp_u%d" % disp_comp
    react_key = "rp_rf%d" % react_comp
    fieldnames = [
        "target_abs_u",
        "abs_u_error",
        "step",
        "frame",
        "step_time",
        disp_key,
        react_key,
        "max_sdv14",
        "max_sdv15",
        "max_sdv16",
    ]
    with open(path, "w") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def write_crack_path_csv(path, rows):
    fieldnames = ["element", "phase_variable", "phase_value", "threshold", "step", "frame"]
    with open(path, "w") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def write_energy_history_csv(path, rows):
    fieldnames = ["step", "step_time", "variable", "value"]
    with open(path, "w") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def write_markdown(path, summary, curve_name, matched_name, contour_names):
    lines = [
        "# Molnar Single-Notch Extraction",
        "",
        "Date: 2026-07-26",
        "",
        "Classification: `%s`" % summary["classification"],
        "",
        "## Scope",
        "",
        "This extraction reads the Molnar single-notch ODB and records benchmark technical evidence plus RF-U and phase/history summaries.",
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
            "| Target abs U | Matched step | Frame | U | RF | Max SDV15 | Max SDV16 |",
            "|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    disp_key = "rp_u%d" % summary.get("disp_component", 2)
    react_key = "rp_rf%d" % summary.get("react_component", 2)
    for row in summary["matched_rows"]:
        lines.append(
            "| %.6e | `%s` | %s | %.6e | %.6e | %.6e | %.6e |"
            % (
                row.get("target_abs_u", row.get("target_abs_u2", 0.0)),
                row["step"],
                row["frame"],
                row.get(disp_key, 0.0),
                row.get(react_key, 0.0),
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
        help="Comma-separated absolute RP U targets for contour extraction",
    )
    parser.add_argument(
        "--displacement-component",
        type=int,
        choices=[1, 2],
        default=2,
        help="Displacement component index (1 or 2, default 2)",
    )
    parser.add_argument(
        "--reaction-component",
        type=int,
        choices=[1, 2],
        default=2,
        help="Reaction force component index (1 or 2, default 2)",
    )
    parser.add_argument(
        "--rp-set",
        default="RP",
        help="Reference point node set name (default RP)",
    )
    parser.add_argument(
        "--phase-variable",
        default="SDV15",
        help="Phase field variable name (default SDV15)",
    )
    parser.add_argument(
        "--history-variable",
        default="SDV16",
        help="History variable name (default SDV16)",
    )
    parser.add_argument(
        "--path-threshold",
        type=float,
        default=0.5,
        help="Phase field threshold for crack path extraction (default 0.5)",
    )
    args = parser.parse_args()

    targets = [float(item.strip()) for item in args.target_displacements.split(",") if item.strip()]
    output_dir = os.path.abspath(args.output_dir)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    extracted = extract_odb(
        os.path.abspath(args.odb),
        targets,
        disp_comp=args.displacement_component,
        react_comp=args.reaction_component,
        rp_set_name=args.rp_set,
        phase_var=args.phase_variable,
        history_var=args.history_variable,
        path_threshold=args.path_threshold,
    )
    if extracted is None:
        return 2

    contour_names = extract_contours(
        os.path.abspath(args.odb),
        extracted["matched_rows"],
        output_dir,
        disp_comp=args.displacement_component,
        react_comp=args.reaction_component,
        phase_var=args.phase_variable,
        history_var=args.history_variable,
    )

    disp_comp = args.displacement_component
    react_comp = args.reaction_component

    if disp_comp == 1 and react_comp == 1:
        curve_path = os.path.join(output_dir, "rf1_u1_curve.csv")
    else:
        curve_path = os.path.join(output_dir, "single_notch_rf_u_phase_summary.csv")

    matched_path = os.path.join(output_dir, "matched_states.csv")
    crack_path_file = os.path.join(
        output_dir,
        "crack_path_%s_ge_0p%d.csv"
        % (args.phase_variable.lower(), int(args.path_threshold * 10)),
    )
    energy_history_file = os.path.join(output_dir, "energy_history.csv")
    json_path = os.path.join(output_dir, "single_notch_extraction_summary.json")
    md_path = os.path.join(output_dir, "SINGLE_NOTCH_EXTRACTION.md")

    write_curve_csv(curve_path, extracted["curve_rows"], disp_comp=disp_comp, react_comp=react_comp)
    write_matched_csv(matched_path, extracted["matched_rows"], disp_comp=disp_comp, react_comp=react_comp)
    write_crack_path_csv(crack_path_file, extracted["crack_path_rows"])
    write_energy_history_csv(energy_history_file, extracted["energy_rows"])

    sta_text = read_text(args.sta)
    dat_text = read_text(args.dat)
    status_parsed = parse_status(sta_text)
    warnings_parsed = parse_warnings(dat_text)
    time_summaries = parse_job_time(dat_text)

    summary = {
        "classification": "technical_pass_scientific_unchecked",
        "odb_readable": True,
        "disp_component": disp_comp,
        "react_component": react_comp,
        "rp_set": args.rp_set,
        "phase_variable": args.phase_variable,
        "history_variable": args.history_variable,
        "path_threshold": args.path_threshold,
        "status": status_parsed,
        "warnings": warnings_parsed,
        "job_time_summaries": time_summaries,
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

    # Write new JSON summaries
    irreversibility_path = os.path.join(output_dir, "irreversibility_summary.json")
    with open(irreversibility_path, "w") as stream:
        json.dump(extracted["irreversibility_summary"], stream, indent=2, sort_keys=True)
        stream.write("\n")

    phase_bounds_path = os.path.join(output_dir, "phase_bounds_summary.json")
    with open(phase_bounds_path, "w") as stream:
        json.dump(extracted["phase_bounds_summary"], stream, indent=2, sort_keys=True)
        stream.write("\n")

    runtime_inventory_path = os.path.join(output_dir, "runtime_output_inventory.json")
    runtime_inventory_data = {
        "field_names_by_step": extracted["field_names_by_step"],
        "history_names_by_step": extracted["history_names_by_step"],
        "element_count": extracted["element_count"],
        "node_count": extracted["node_count"],
    }
    with open(runtime_inventory_path, "w") as stream:
        json.dump(runtime_inventory_data, stream, indent=2, sort_keys=True)
        stream.write("\n")

    # Additional inventories
    field_inventory_path = os.path.join(output_dir, "field_output_inventory.json")
    with open(field_inventory_path, "w") as stream:
        json.dump(extracted["field_names_by_step"], stream, indent=2, sort_keys=True)
        stream.write("\n")

    history_inventory_path = os.path.join(output_dir, "history_output_inventory.json")
    with open(history_inventory_path, "w") as stream:
        json.dump(extracted["history_names_by_step"], stream, indent=2, sort_keys=True)
        stream.write("\n")

    job_status_path = os.path.join(output_dir, "job_status.json")
    with open(job_status_path, "w") as stream:
        json.dump(status_parsed, stream, indent=2, sort_keys=True)
        stream.write("\n")

    resource_summary_path = os.path.join(output_dir, "resource_summary.json")
    with open(resource_summary_path, "w") as stream:
        json.dump({"job_time_summaries": time_summaries}, stream, indent=2, sort_keys=True)
        stream.write("\n")

    manifest_path = os.path.join(output_dir, "extraction_manifest.json")
    manifest_data = {
        "classification": "stage_f_extraction_manifest_pass",
        "disp_component": disp_comp,
        "react_component": react_comp,
        "rp_set": args.rp_set,
        "phase_variable": args.phase_variable,
        "history_variable": args.history_variable,
        "path_threshold": args.path_threshold,
        "extracted_files": [
            os.path.basename(curve_path),
            os.path.basename(matched_path),
            os.path.basename(crack_path_file),
            "energy_history.csv",
            "irreversibility_summary.json",
            "phase_bounds_summary.json",
            "runtime_output_inventory.json",
            "single_notch_extraction_summary.json",
            "field_output_inventory.json",
            "history_output_inventory.json",
            "job_status.json",
            "resource_summary.json",
        ] + contour_names,
    }
    with open(manifest_path, "w") as stream:
        json.dump(manifest_data, stream, indent=2, sort_keys=True)
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
    print("Crack path CSV: %s" % crack_path_file)
    print("Energy history CSV: %s" % energy_history_file)
    print("Contour CSV files: %d" % len(contour_names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
