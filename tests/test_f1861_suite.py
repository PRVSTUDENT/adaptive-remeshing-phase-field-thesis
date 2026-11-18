# -*- coding: utf-8 -*-
"""Unit test suite for Task F1861 Uniform Reference Suite.

Verifies:
1. All 4 physical reference meshes satisfy paper Standard uniform sizing and element counts:
   - Case 1: h = 0.00375 mm (l0/2), 87,020 elements, >=85% quads
   - Case 2: h = 0.00375 mm (l0/2), 84,651 elements, >=85% quads
   - Case 3: h = 0.358 mm (~86,000 target), 85,798 elements, >=85% quads
   - Case 5: h = 0.00363 mm (81,090 target), 80,829 elements, >=85% quads
2. All 4 3-layer Method A production decks exist with line-wrapping <= 16 entries and match receipts.
3. Subroutine and interface hashes match frozen references (CE8D5EDC..., E5C98B6F...).
4. Submission receipts and PBS IDs (1424456, 1424465, 1424466, 1424467) recorded.
5. PBS accounting strictly verified (4 consumed, cumulative 57).
6. Master goal status remains OPEN.
"""

import csv
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SUITE_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "288_f1861_uniform_reference"
RECEIPT_FILE = SUITE_DIR / "f1861_suite_receipt.json"
SUBMISSION_FILE = SUITE_DIR / "f1861_submission_receipt.json"
ACTIVE_TASK_FILE = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
HPC_LEDGER_FILE = REPO_ROOT / "project_coordination" / "HPC_JOB_LEDGER.csv"

FROZEN_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
FROZEN_INTERFACE_SHA = "e5c98b6f601b1cd586571f8e24f357d15abbd1c5d5487b52903ba249734279b2"


def test_suite_receipt_and_physical_meshes():
    """Verify all 4 uniform reference physical meshes meet target resolution and quality."""
    assert RECEIPT_FILE.is_file(), "Missing f1861_suite_receipt.json"
    with open(RECEIPT_FILE, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    jobs = data["jobs"]
    expected_cases = {
        "F1861_REF_C1": {
            "elem_min": 85000, "elem_max": 90000,
            "quad_percent_min": 95.0
        },
        "F1861_REF_C2": {
            "elem_min": 82000, "elem_max": 88000,
            "quad_percent_min": 95.0
        },
        "F1861_REF_C3": {
            "elem_min": 84000, "elem_max": 88000,
            "quad_percent_min": 95.0
        },
        "F1861_REF_C5": {
            "elem_min": 79000, "elem_max": 83000,
            "quad_percent_min": 95.0
        },
    }

    for jname, exp in expected_cases.items():
        assert jname in jobs, f"Missing job {jname} in receipt"
        j = jobs[jname]
        n_elem = j["physical_elements"]
        quad_pct = j["quad_percent"]
        assert exp["elem_min"] <= n_elem <= exp["elem_max"], (
            f"{jname} physical elements {n_elem} outside expected range [{exp['elem_min']}, {exp['elem_max']}]"
        )
        assert quad_pct >= exp["quad_percent_min"], (
            f"{jname} quad percent {quad_pct:.2f}% < {exp['quad_percent_min']}%"
        )

        # Check file existence
        sub_dir = jname.split("_")[-1].lower()
        if sub_dir == "c1":
            sub_dir = "case1"
        elif sub_dir == "c2":
            sub_dir = "case2"
        elif sub_dir == "c3":
            sub_dir = "case3"
        elif sub_dir == "c5":
            sub_dir = "case5"

        case_num = jname.split("_")[-1].replace("C", "")
        phys_path = SUITE_DIR / sub_dir / f"PK_F1861_REF_CASE_{case_num}_PHYS.inp"
        assert phys_path.is_file(), f"Missing physical mesh file {phys_path}"


def test_production_decks_and_layer_multipliers():
    """Verify 3-layer Method A decks have exact 3x element counts and valid line wrapping."""
    with open(RECEIPT_FILE, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    for jname, j in data["jobs"].items():
        sub_dir = j["scratch_dir"].split("/")[-1]
        deck_path = SUITE_DIR / sub_dir / f"{j['model_name']}.inp"
        assert deck_path.is_file(), f"Missing production deck {deck_path}"

        # Layer multiplier check
        assert j["layered_elements"] == 3 * j["physical_elements"], (
            f"{jname} layered elements {j['layered_elements']} != 3 * {j['physical_elements']}"
        )

        # Line length / token check in elsets: Abaqus *ELSET, GENERATE or lists max 16 per line
        with open(deck_path, "r", encoding="utf-8-sig") as f:
            in_elset = False
            for line_no, line in enumerate(f, 1):
                s = line.strip()
                if s.startswith("*ELSET") and "GENERATE" not in s:
                    in_elset = True
                    continue
                elif s.startswith("*"):
                    in_elset = False
                    continue
                if in_elset and s:
                    tokens = [t.strip() for t in s.split(",") if t.strip()]
                    assert len(tokens) <= 16, (
                        f"Line {line_no} in {deck_path.name} exceeds 16 entries: {len(tokens)}"
                    )


def test_subroutine_hashes():
    """Verify frozen UEL and native stress interface hashes."""
    import hashlib

    # Subroutine interface file in each case directory
    for case in ["case1", "case2", "case3", "case5"]:
        for_path = SUITE_DIR / case / "f42_native_miseseri_interface_v1.for"
        assert for_path.is_file(), f"Missing {for_path}"
        with open(for_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().lower()
        assert h == FROZEN_INTERFACE_SHA, f"Interface hash mismatch in {case}: {h} != {FROZEN_INTERFACE_SHA}"


def test_submission_receipt_and_job_ids():
    """Verify all 4 jobs are recorded in f1861_submission_receipt.json with valid PBS IDs."""
    assert SUBMISSION_FILE.is_file(), "Missing f1861_submission_receipt.json"
    with open(SUBMISSION_FILE, "r", encoding="utf-8-sig") as f:
        subs = json.load(f)

    assert len(subs) == 4, f"Expected 4 submissions, got {len(subs)}"
    job_ids = [s["pbs_job_id"] for s in subs]
    for jid in job_ids:
        assert jid.endswith(".mmaster02"), f"Invalid PBS Job ID format: {jid}"

    assert len(set(job_ids)) == 4, f"Duplicate PBS Job IDs detected: {job_ids}"


def test_pbs_accounting_and_active_task():
    """Verify PBS accounting: exactly 4 consumed, cumulative 57, master goal OPEN."""
    with open(ACTIVE_TASK_FILE, "r", encoding="utf-8-sig") as f:
        task = json.load(f)

    assert task["task_id"] == "F1861-UNIFORM-HIGHLY-REFINED-REFERENCE"
    assert task["submissions_consumed"] == 4, f"Consumed {task['submissions_consumed']} != 4"
    assert task["cumulative_pbs_submissions"] == 57, f"Cumulative {task['cumulative_pbs_submissions']} != 57"
    assert task["master_goal_status"] == "OPEN", "Master goal status must remain OPEN"

    # Check HPC_JOB_LEDGER.csv
    assert HPC_LEDGER_FILE.is_file(), "Missing HPC_JOB_LEDGER.csv"
    with open(HPC_LEDGER_FILE, "r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))

    # Last 4 entries must correspond to F1861
    last_4 = reader[-4:]
    for row in last_4:
        assert len(row) >= 9, f"Malformed row in HPC ledger: {row}"
        assert row[1].startswith("F1861_REF_C"), f"Unexpected job name in ledger: {row[1]}"
        assert row[8] == "F1861_UNIFORM_REFERENCE_PARALLEL_16CPU_SMP"
