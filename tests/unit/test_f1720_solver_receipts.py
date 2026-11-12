#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_f1720_solver_receipts.py
Unit and regression test suite for primary solver receipts of Task F1720.
Validates file sizes, SHA-256 hashes, terminal lines, cutback counts,
increment totals, and ODB final frame reconciliation.
"""

import hashlib
import json
import os
import pytest

STA_PATH = "models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.sta"
MSG_PATH = "models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.msg"
DAT_PATH = "models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.dat"
INVENTORY_PATH = "results/validation/f1720_solver_receipts/RECEIPT_INVENTORY.json"
FORENSICS_PATH = "results/validation/f1720_solver_forensics.json"

EXPECTED_HASHES = {
    STA_PATH: "A219FA1B5D585A4730A62D16B4EE97985C86180642230944A4DA1942123F504F",
    MSG_PATH: "8748784CDDB7F4288B33F23B518D95A9EB4E8E9E2B92A0BF638781F087B1E15A",
    DAT_PATH: "03CC6A4F18EC44EA33208E424FBB1F4DF12871F6FB757A3957D6CC559E18712B",
}

EXPECTED_SIZES = {
    STA_PATH: 13971,
    MSG_PATH: 572480,
    DAT_PATH: 17808,
}

def sha256_of_file(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest().upper()

def test_01_primary_receipt_files_exist_and_match_manifest_hashes():
    for path, expected_hash in EXPECTED_HASHES.items():
        assert os.path.isfile(path), f"Primary receipt {path} must exist on disk."
        actual_size = os.path.getsize(path)
        assert actual_size == EXPECTED_SIZES[path], (
            f"Size mismatch for {path}: expected {EXPECTED_SIZES[path]}, got {actual_size}"
        )
        actual_hash = sha256_of_file(path)
        assert actual_hash == expected_hash, (
            f"SHA-256 mismatch for {path}: expected {expected_hash}, got {actual_hash}"
        )

def test_02_status_file_increments_cutbacks_and_time_fraction():
    with open(STA_PATH, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Check terminal message
    assert any("THE ANALYSIS HAS NOT BEEN COMPLETED" in line for line in lines)

    # Parse rows: step, inc, severe_discon_or_cutbacks, etc.
    step1_incs = 0
    step2_incs = 0
    step2_cutbacks = 0
    last_step2_time = 0.0

    for line in lines:
        parts = line.split()
        if len(parts) >= 6 and parts[0] in ("1", "2") and parts[1].isdigit():
            step_num = int(parts[0])
            inc_token = parts[1]
            flag_token = parts[2]
            if step_num == 1:
                step1_incs = max(step1_incs, int(inc_token))
            elif step_num == 2:
                step2_incs = max(step2_incs, int(inc_token))
                if "U" in flag_token:
                    step2_cutbacks += 1
                try:
                    step_time = float(parts[7]) if len(parts) > 7 else float(parts[-2])
                    last_step2_time = max(last_step2_time, step_time)
                except ValueError:
                    pass

    assert step1_incs == 50, f"Step 1 must complete 50 increments, got {step1_incs}"
    assert step2_incs == 127, f"Step 2 must reach increment 127, got {step2_incs}"
    assert step2_cutbacks == 24, f"Step 2 must have 24 cutbacks, got {step2_cutbacks}"
    assert step1_incs + step2_incs == 177, "Total completed increments must be 177"
    assert abs(last_step2_time - 0.221) < 0.005, f"Final step 2 time fraction must be ~0.221, got {last_step2_time}"

def test_03_message_file_terminal_error_and_analysis_summary():
    with open(MSG_PATH, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    assert "TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED" in content
    assert "THE ANALYSIS HAS BEEN TERMINATED DUE TO PREVIOUS ERRORS" in content
    assert "TOTAL OF        177  INCREMENTS" in content
    assert "24  CUTBACKS IN AUTOMATIC INCREMENTATION" in content
    assert "639  ITERATIONS" in content
    assert "2  ERROR MESSAGES" in content

def test_04_data_file_completion_message():
    with open(DAT_PATH, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    assert "ANALYSIS COMPLETE" in content
    assert "2 ERROR MESSAGES ON THE MSG FILE" in content
    assert "14 WARNING MESSAGES ON THE DAT FILE" in content

def test_05_reconciliation_with_final_odb_frame():
    assert os.path.isfile(FORENSICS_PATH), f"{FORENSICS_PATH} must exist"
    with open(FORENSICS_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    final = data["final_frame_summary"]
    assert final["step"] == "Step-2"
    assert final["frame_index"] == 127
    assert abs(final["frame_value"] - 0.22149844467639923) < 1e-8
    assert abs(final["u2_rp"] - 0.005664495285600424) < 1e-8
    assert abs(final["rf2_rp"] - 0.9127940535545349) < 1e-6

    # Verify frame and increment structure
    step1_frames = data["steps"]["Step-1"]["total_frames"]
    step2_frames = data["steps"]["Step-2"]["total_frames"]
    assert step1_frames == 51  # frame 0 + 50 completed increments
    assert step2_frames == 128 # frame 0 + 127 completed increments
    completed_incs = (step1_frames - 1) + (step2_frames - 1)
    assert completed_incs == 177

    # Verify physical integration point count in ODB
    assert data["sdv1_values_count"] == 51716

def test_06_text_receipt_copies_and_inventory_consistency():
    assert os.path.isfile(INVENTORY_PATH), f"{INVENTORY_PATH} must exist"
    with open(INVENTORY_PATH, "r", encoding="utf-8-sig") as f:
        inv = json.load(f)

    sta_copy = "results/validation/f1720_solver_receipts/PK_F1720_ADAPTED_PFM_sta.txt"
    dat_copy = "results/validation/f1720_solver_receipts/PK_F1720_ADAPTED_PFM_dat.txt"
    msg_term = "results/validation/f1720_solver_receipts/PK_F1720_ADAPTED_PFM_msg_terminal.txt"

    assert os.path.isfile(sta_copy)
    assert os.path.isfile(dat_copy)
    assert os.path.isfile(msg_term)

    assert sha256_of_file(sta_copy) == EXPECTED_HASHES[STA_PATH]
    assert sha256_of_file(dat_copy) == EXPECTED_HASHES[DAT_PATH]
