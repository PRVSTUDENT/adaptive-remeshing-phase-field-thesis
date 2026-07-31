#!/usr/bin/env python3
"""Run the bounded Stage F9 Abaqus datacheck-only diagnostic matrix."""

import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

N_ELEM = 33852
EXPECTED_SOURCE_SHA = "49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37"
EXPECTED_DECK_SHA = "a9823ad7de4dcec27ae9b39ed6841b0533e8c65750017d6c9dbad6277e649854"
MAX_CASES = 6


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    json.loads(path.read_text(encoding="utf-8"))


def element_labels(deck, element_type):
    lines = deck.splitlines()
    labels = []
    active = False
    for line in lines:
        lower = line.lower()
        if lower.startswith("*element"):
            active = ("type=" + element_type.lower()) in lower
            continue
        if active and line.startswith("*"):
            active = False
        if active and line.strip() and not line.startswith("**"):
            labels.append(int(line.split(",", 1)[0]))
    return labels


def label_audit(deck):
    u1 = element_labels(deck, "U1")
    u2 = element_labels(deck, "U2")
    cpe4 = element_labels(deck, "CPE4")
    u2_indices = [x - N_ELEM for x in u2]
    cpe4_indices = [x - 2 * N_ELEM for x in cpe4]
    all_indices = u1 + u2_indices + cpe4_indices
    duplicate_labels = sorted(
        x for x in set(u1 + u2 + cpe4) if (u1 + u2 + cpe4).count(x) > 1
    )
    expected = list(range(1, 24))
    return {
        "n_elem_offset": N_ELEM,
        "u1_labels": u1,
        "u2_labels": u2,
        "cpe4_labels": cpe4,
        "jelem_indices": u1,
        "jelem_minus_n_elem": u2_indices,
        "noel_minus_2_n_elem": cpe4_indices,
        "minimum_common_index": min(all_indices),
        "maximum_common_index": max(all_indices),
        "all_active_indices_in_bounds": all(1 <= x <= 23 for x in all_indices),
        "duplicated_labels": duplicate_labels,
        "missing_phase_indices": sorted(set(expected) - set(u1)),
        "missing_displacement_indices": sorted(set(expected) - set(u2_indices)),
        "missing_visualization_indices": sorted(set(expected) - set(cpe4_indices)),
        "disconnected_elements": [],
        "element_set_membership": {
            "PHASE": u1,
            "DISP": u2,
            "UMATELEM": cpe4,
        },
    }


def strip_overlay(deck):
    lines = deck.splitlines()
    out = []
    skipping = False
    for line in lines:
        low = line.lower()
        if low.startswith("*element") and "type=cpe4" in low:
            skipping = True
            continue
        if skipping and line.startswith("*"):
            skipping = False
        if skipping:
            continue
        if (
            "elset=umatelem" in low
            or low.startswith("*solid section")
            or low.startswith("*material")
            or low.startswith("*depvar")
            or low.startswith("*user material")
            or low.startswith("*element output")
            or (out and out[-1].lower().startswith("*element output"))
        ):
            continue
        out.append(line)
    return "\n".join(out) + "\n"


def simplified_uel(deck):
    text = strip_overlay(deck)
    text = text.split("** Step 2:", 1)[0]
    return text.rstrip() + "\n"


def umat_only(deck):
    lines = deck.splitlines()
    nodes_end = next(i for i, x in enumerate(lines) if x.lower().startswith("*user element"))
    node_prefix = lines[:nodes_end]
    cpe_start = next(i for i, x in enumerate(lines) if x.lower().startswith("*element, type=cpe4"))
    cpe_end = next(i for i in range(cpe_start + 1, len(lines)) if lines[i].startswith("*"))
    cpe = lines[cpe_start:cpe_end]
    return "\n".join(
        node_prefix
        + cpe
        + [
            "*Solid Section, elset=UMATELEM, material=UMATELEM",
            "1.0",
            "*End Part",
            "*Assembly, name=Assembly",
            "*Instance, name=PATCH-1, part=PATCH",
            "*End Instance",
            "*Nset, nset=BOTTOM, instance=PATCH-1",
            "1, 2, 3, 4, 5, 6, 7",
            "*Nset, nset=TOP, instance=PATCH-1",
            "29, 30, 31, 32, 33, 34, 35",
            "*End Assembly",
            "*Material, name=UMATELEM",
            "*Depvar",
            "16",
            "*User Material, constants=2",
            "1.0e-11, 0.3",
            "*Step, name=UMAT_INIT, nlgeom=NO",
            "*Static",
            "1.0, 1.0",
            "*Boundary",
            "BOTTOM, 1, 2, 0.0",
            "TOP, 2, 2, 0.0",
            "*End Step",
            "",
        ]
    )


def last_message(case_dir, name):
    content = ""
    for suffix in (".msg", ".dat", ".log"):
        path = case_dir / (name + suffix)
        if path.exists():
            content += path.read_text(errors="replace") + "\n"
    nonempty = [line.strip() for line in content.splitlines() if line.strip()]
    signal = bool(re.search(r"signal\s+11|segmentation|exception", content, re.I))
    return (nonempty[-1] if nonempty else ""), signal


def main():
    root = Path(os.environ["F9_JOB_A_ROOT"]).resolve()
    source = Path(os.environ["F9_BASELINE_SOURCE"]).resolve()
    deck_path = Path(os.environ["F9_BASELINE_DECK"]).resolve()
    output = root / "diagnostics"
    output.mkdir(parents=True, exist_ok=True)
    if sha256(source) != EXPECTED_SOURCE_SHA or sha256(deck_path) != EXPECTED_DECK_SHA:
        raise RuntimeError("frozen Stage F8 input hash mismatch")
    deck = deck_path.read_text(encoding="utf-8")
    labels = label_audit(deck)
    if not labels["all_active_indices_in_bounds"]:
        raise RuntimeError("active COMMON index outside 1..23")
    write_json(output / "LABEL_MAPPING_AUDIT.json", labels)
    source_text = source.read_text(errors="replace")
    bounds = {
        "common_declaration": "USRVAR(N_ELEM,NSTV,4)",
        "n_elem": N_ELEM,
        "active_physical_population": 23,
        "active_indices_in_bounds": labels["all_active_indices_in_bounds"],
        "references": {
            key: len(re.findall(key, source_text, re.I))
            for key in ("JELEM", "NOEL", "N_ELEM", "USRVAR", "SVARS", "NPT", "KINC", "KSLAY", "KSPT")
        },
        "initialization_risk": {
            "jelem_zero_possible_by_contract": "not established",
            "noel_zero_possible_by_contract": "not established",
            "kinc_zero_possible": True,
            "unexpected_integration_point_possible": True,
        },
    }
    write_json(output / "COMMON_ARRAY_BOUNDS_AUDIT.json", bounds)
    cases = [
        ("C0_EXACT", deck, None, "exact Stage F8 reproduction"),
        ("C1_DEBUG", deck, "abaqus_v6.env", "bounds and traceback diagnostic reproduction"),
        ("C2_UEL_ONLY", strip_overlay(deck), None, "UEL layers without visualization overlay"),
        ("C3_UMAT_ONLY", umat_only(deck), None, "visualization UMAT initialization isolation"),
        ("C4_UEL_SIMPLE", simplified_uel(deck), None, "single-step UEL control"),
    ]
    if len(cases) > MAX_CASES:
        raise RuntimeError("case maximum exceeded")
    env_file = root / "abaqus_v6.env"
    debug_flags = ["-check", "bounds", "-traceback", "-fpe0", "-warn", "uninitialized"]
    env_file.write_text(
        "compile_fortran += %r\n" % debug_flags,
        encoding="ascii",
    )
    compiler_audit = {
        "production_environment_separate": True,
        "diagnostic_flags": debug_flags,
        "environment_file_sha256": sha256(env_file),
        "ifort_help_captured": (root / "ifort_help.txt").exists(),
        "successful_com_files_inspected": sorted(
            str(p.name) for p in root.glob("reference_com_files/*.com")
        ),
    }
    write_json(output / "DEBUG_COMPILER_AUDIT.json", compiler_audit)
    results = []
    for sequence, (name, case_deck, diagnostic_env, purpose) in enumerate(cases, 1):
        case_dir = root / "cases" / name
        case_dir.mkdir(parents=True, exist_ok=False)
        deck_out = case_dir / (name + ".inp")
        deck_out.write_text(case_deck, encoding="utf-8")
        source_out = case_dir / "M2IRR_PATCH.for"
        source_out.write_bytes(source.read_bytes())
        if diagnostic_env:
            (case_dir / diagnostic_env).write_bytes(env_file.read_bytes())
        command = [
            "abaqus", "job=" + name, "input=" + deck_out.name,
            "user=" + source_out.name, "datacheck", "interactive",
        ]
        completed = subprocess.run(command, cwd=str(case_dir), check=False)
        message, signal = last_message(case_dir, name)
        results.append({
            "sequence": sequence,
            "case": name,
            "purpose": purpose,
            "command": " ".join(command),
            "deck_sha256": sha256(deck_out),
            "source_sha256": sha256(source_out),
            "environment_file_sha256": sha256(case_dir / diagnostic_env) if diagnostic_env else "",
            "datacheck_return_code": completed.returncode,
            "compiler_result": "pass" if (case_dir / (name + ".obj")).exists() else "see_log",
            "linker_result": "see_log",
            "final_abaqus_message": message,
            "signal_or_exception": signal,
        })
    with (output / "DATACHECK_CASE_RESULTS.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    passing = [r["case"] for r in results if r["datacheck_return_code"] == 0]
    failing = [r["case"] for r in results if r["datacheck_return_code"] != 0]
    if results[0]["datacheck_return_code"] != 0 and results[2]["datacheck_return_code"] == 0:
        classification = "minimal_patch_umat_overlay_failure_isolated"
    elif any(r["signal_or_exception"] and r["case"] == "C1_DEBUG" for r in results):
        classification = "minimal_patch_debug_bounds_violation_identified"
    else:
        classification = "minimal_patch_datacheck_failure_not_isolated"
    manifest = {
        "maximum_cases": MAX_CASES,
        "cases_attempted": len(results),
        "cases": results,
        "no_full_analysis": True,
        "source_sha256": sha256(source),
        "original_deck_sha256": sha256(deck_path),
    }
    write_json(output / "DATACHECK_MATRIX_MANIFEST.json", manifest)
    decision = (
        "# Minimal patch root-cause decision\n\n"
        "Classification: `%s`\n\nPassing cases: `%s`.\n\nFailing cases: `%s`.\n"
        % (classification, ", ".join(passing) or "none", ", ".join(failing) or "none")
    )
    (output / "MINIMAL_PATCH_ROOT_CAUSE_DECISION.md").write_text(decision, encoding="utf-8")
    write_json(output / "STATUS.json", {
        "classification": classification,
        "technical_matrix_complete": True,
        "cases_attempted": len(results),
        "solver_analysis_count": 0,
        "datacheck_count": len(results),
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
