#!/usr/bin/env python3
"""Validate the living project phase checklist."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKLIST = ROOT / "docs" / "project" / "PROJECT_PHASE_CHECKLIST.md"
REPORTS = [
    "docs/reports/STAGE_A_BASELINE_REPORT.tex",
    "docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex",
]
STATUS_MARKERS = ("[x]", "[ ]", "[-]", "[!]", "[?]", "[~]")
EVIDENCE_TOKENS = ("Evidence:", "Commit:", "Run:", "Job:", "Classification:", "Result:", "Note:")


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def checklist_duplicates() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("PROJECT_PHASE_CHECKLIST.md")
        if "agent_handoff" not in path.parts
    ]


def dashboard_rows(text: str) -> list[str]:
    rows: list[str] = []
    in_dashboard = False
    for line in text.splitlines():
        if line.startswith("## Overall Phase Dashboard"):
            in_dashboard = True
            continue
        if in_dashboard and line.startswith("## "):
            break
        if in_dashboard and line.startswith("|") and "---" not in line and "Phase" not in line:
            rows.append(line)
    return rows


def completed_items_without_evidence(lines: list[str]) -> list[tuple[int, str]]:
    missing: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        if re.match(r"\s*[-*]\s+\[x\]", line):
            window = "\n".join(lines[index : index + 4])
            if not any(token in window for token in EVIDENCE_TOKENS):
                missing.append((index + 1, line.strip()))
    return missing


def section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^## ", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end]


def main() -> int:
    errors: list[str] = []
    if not CHECKLIST.exists():
        fail(f"missing checklist: {CHECKLIST}", errors)
        print("\n".join(errors))
        return 2

    text = CHECKLIST.read_text(encoding="utf-8")
    lines = text.splitlines()

    duplicates = checklist_duplicates()
    if len(duplicates) != 1:
        fail("duplicate checklist files outside agent_handoff: " + ", ".join(str(p) for p in duplicates), errors)

    rows = dashboard_rows(text)
    if not rows:
        fail("overall phase dashboard has no phase rows", errors)
    for row in rows:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        if len(cells) < 5 or not any(marker in cells[2] for marker in STATUS_MARKERS):
            fail(f"dashboard row lacks a status marker: {row}", errors)

    for line_number, item in completed_items_without_evidence(lines):
        fail(f"completed item lacks evidence near line {line_number}: {item}", errors)

    config = ROOT / "configs" / "molnar_paper_matched_single_notch.yaml"
    config_text = config.read_text(encoding="utf-8") if config.exists() else ""
    if "runnable: false" in config_text:
        gate_table = section(text, "Gate Checklist")
        if re.search(r"\|\s*Gate A3\s*\|[^\n]*\|\s*passed\s*\|", gate_table, re.IGNORECASE):
            fail("Gate A3 is marked passed while configuration is non-runnable", errors)

    wp3 = section(text, "WP3 - MISESERI Pre-Analysis And Remeshing Reproduction")
    if "Gate A3: reference_data_insufficient" in text:
        wp3_lines = [line for line in wp3.splitlines() if re.match(r"\s*[-*]\s+\[-\]", line)]
        if wp3_lines:
            fail("WP3 has in-progress items while Gate A3 is blocked: " + "; ".join(wp3_lines), errors)

    if re.search(r"\|\s*(WP3|WP4|WP5|WP6)\s*\|[^\n]*\|\s*`\[x\]`", text):
        fail("downstream stage marked complete while its gate is open", errors)

    for report in REPORTS:
        if report not in text:
            fail(f"required living report not referenced: {report}", errors)

    counts = {marker: len(re.findall(re.escape(marker), text)) for marker in STATUS_MARKERS}
    if errors:
        print("check_project_phase_checklist: FAIL")
        for error in errors:
            print(f"- {error}")
        print("counts:", counts)
        return 2

    print("check_project_phase_checklist: PASS")
    print("counts:", counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
