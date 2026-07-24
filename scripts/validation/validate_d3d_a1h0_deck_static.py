#!/usr/bin/env python3
"""Validate the frozen D3D-A1H0 two-step fixed-phase datacheck deck."""

import argparse
import json
import math
import re
from pathlib import Path

EXPECTED_STEPS = [
    "INGEST_D3D_A1_CANDIDATE",
    "D3D_A1_MECHANICAL_CHECKPOINT_EQUILIBRATION",
]
EXPECTED_FIXED_PHASE_NODES = 6601
EXPECTED_CHECKPOINT_U2 = 0.003000000026077032
EXPECTED_PACKAGE = "package_d3d_a1_checkpoint_r1"


def validate(deck_path):
    text = deck_path.read_text(encoding="utf-8")
    step_matches = list(
        re.finditer(r"(?im)^\*Step,\s*name=([^,\r\n]+).*$", text)
    )
    step_names = [match.group(1).strip() for match in step_matches]
    sections = []
    for index, match in enumerate(step_matches):
        end = step_matches[index + 1].start() if index + 1 < len(step_matches) else len(text)
        sections.append(text[match.start():end])

    fixed_counts = []
    for section in sections:
        nodes = set()
        for raw in section.splitlines():
            parts = [part.strip() for part in raw.split(",")]
            if (
                len(parts) >= 4
                and parts[0].isdigit()
                and parts[1:3] == ["3", "3"]
            ):
                nodes.add(int(parts[0]))
        fixed_counts.append(len(nodes))

    top_u2_values = []
    for raw in text.splitlines():
        parts = [part.strip() for part in raw.split(",")]
        if len(parts) >= 4 and parts[0].upper() == "TOP" and parts[1:3] == ["2", "2"]:
            top_u2_values.append(float(parts[3]))

    upper = text.upper()
    package_present = EXPECTED_PACKAGE in text
    release_absent = "RELEASE" not in upper
    continuation_absent = "CONTINUATION" not in upper
    checkpoint_unchanged = (
        len(top_u2_values) == 1
        and math.isclose(top_u2_values[0], EXPECTED_CHECKPOINT_U2, rel_tol=0.0, abs_tol=1.0e-15)
    )
    failures = []
    if step_names != EXPECTED_STEPS:
        failures.append("step_names")
    if fixed_counts != [EXPECTED_FIXED_PHASE_NODES, EXPECTED_FIXED_PHASE_NODES]:
        failures.append("fixed_phase_node_counts")
    if not release_absent:
        failures.append("phase_release_step_present")
    if not continuation_absent:
        failures.append("continuation_step_present")
    if not checkpoint_unchanged:
        failures.append("checkpoint_u2_changed")
    if not package_present:
        failures.append("candidate_package_mismatch")

    return {
        "classification": (
            "stage_d3d_a1h0_r2_deck_static_pass"
            if not failures
            else "stage_d3d_a1h0_r2_deck_static_fail"
        ),
        "deck_static_ok": not failures,
        "input": str(deck_path),
        "step_count": len(step_names),
        "step_names": step_names,
        "step1_fixed_phase_nodes": fixed_counts[0] if fixed_counts else 0,
        "step2_fixed_phase_nodes": fixed_counts[1] if len(fixed_counts) > 1 else 0,
        "phase_release_step_present": not release_absent,
        "continuation_step_present": not continuation_absent,
        "checkpoint_u2_values": top_u2_values,
        "checkpoint_u2_expected": EXPECTED_CHECKPOINT_U2,
        "checkpoint_u2_unchanged": checkpoint_unchanged,
        "candidate_package": EXPECTED_PACKAGE if package_present else None,
        "candidate_package_expected": EXPECTED_PACKAGE,
        "failures": failures,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    status = validate(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["deck_static_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
