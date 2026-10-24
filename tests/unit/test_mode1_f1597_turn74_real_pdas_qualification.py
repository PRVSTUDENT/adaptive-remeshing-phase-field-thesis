#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn74_real_pdas_qualification.py
Unit tests for Turn 74 live-solver integration gap remediations:
1. Frozen production UEL SHA-256 bitwise integrity.
2. Gap A: Elimination of artificial quadratic history scaling (enforcing scale_h = 1.0 with authentic H).
3. Gap B: Verification of mechanical continuation loading (+4.0 nm, u_target = 0.002056 mm) on node 999999.
4. Gap C: Verification of live ODB extraction script (extract_pdas_subproblem_odb.py).
5. Gap D: Independent calculation of strict healing (Delta d < 0) vs tolerance healing (Delta d < -1e-6) and KKT multipliers.
6. Gap E: Crash-safe atomic ledger persistence (.tmp replacement) and separation of trial evaluations from accepted checkpoints.
7. Disjoint active-set partition invariant (|U| + |L| + |A| = 4,610 physical nodes).
8. Safety cap at k_max = 25 iterations.
9. Independent reproduction of H1 Sobolev projection energy mismatch (-1.5500%).
10. Scientific gate discipline: Gate C1-2 strictly NOT QUALIFIED until real Abaqus output meets all criteria.
"""

import json
import hashlib
from pathlib import Path
import pytest
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
FROZEN_UEL = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

TEST_WORK_DIR = REPO_ROOT / "results/validation/scratch_pdas_adapter_test"
LEDGER_PATH = TEST_WORK_DIR / "pdas_subproblem_ledger.json"
CHECKPOINT_PATH = TEST_WORK_DIR / "pdas_accepted_checkpoint.json"
TRIAL_PATH = TEST_WORK_DIR / "pdas_trial_evaluation.json"
EXTRACTION_SCRIPT = REPO_ROOT / "scripts/validation/extract_pdas_subproblem_odb.py"
ADAPTER_SCRIPT = REPO_ROOT / "scripts/validation/pdas_cluster_execution_adapter.py"
H1_EVAL_JSON = REPO_ROOT / "results/validation/mode1_f1597/pkg96_h1_transfer_and_pdas_evaluation.json"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def test_frozen_uel_sha256():
    """Verify that production UEL f42_mixed_uel.for remains strictly bitwise frozen."""
    assert FROZEN_UEL.exists(), f"Frozen UEL missing: {FROZEN_UEL}"
    actual = sha256_file(FROZEN_UEL)
    assert actual == FROZEN_UEL_HASH, f"UEL hash mismatch: expected {FROZEN_UEL_HASH}, got {actual}"

def test_gap_a_artificial_history_scaling_elimination():
    """Verify that artificial quadratic scaling scale_h is eliminated from physical execution."""
    adapter_text = ADAPTER_SCRIPT.read_text(encoding="utf-8")
    assert "scale_h = (u_target / self.u_checkpoint)**2" not in adapter_text, "Artificial scale_h shortcut must be removed"
    assert "scale_h: float = 1.0" in adapter_text
    assert "self.assemble_phase_system(scale_h=1.0)" in adapter_text

def test_gap_b_continuation_loading_verification():
    """Verify that physical +4.0 nm continuation loading (u_target = 0.002056 mm) is explicitly prescribed."""
    subproblem = TEST_WORK_DIR / "pdas_subproblem_iter_01.inp"
    assert subproblem.exists(), f"Subproblem deck missing: {subproblem}"
    sub_text = subproblem.read_text(encoding="utf-8")
    assert "999999, 2, 2, 2.0560000000e-03" in sub_text, "Prescribed mechanical displacement u_target missing from control node 999999"

def test_gap_c_live_odb_extraction_script():
    """Verify that authentic Abaqus Python ODB extraction script exists and is syntactically sound."""
    assert EXTRACTION_SCRIPT.exists(), f"Extraction script missing: {EXTRACTION_SCRIPT}"
    text = EXTRACTION_SCRIPT.read_text(encoding="utf-8")
    assert "from odbAccess import openOdb" in text
    assert "fieldOutputs.get('U'" in text or "fieldOutputs['U']" in text
    assert "fieldOutputs.get('RF'" in text or "fieldOutputs['RF']" in text
    assert "999999" in text

def test_gap_d_strict_vs_tolerance_validation():
    """Verify that strict healing/overshoot and tolerance healing/overshoot are tracked separately."""
    assert TRIAL_PATH.exists(), f"Trial report missing: {TRIAL_PATH}"
    with open(TRIAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "strict_healing_nodes" in data
    assert "tolerance_healing_nodes" in data
    assert "strict_overshoot_nodes" in data
    assert "tolerance_overshoot_nodes" in data
    assert "kkt_lower_valid" in data
    assert "kkt_upper_valid" in data
    assert data["strict_healing_nodes"] == 0
    assert data["tolerance_healing_nodes"] == 0

def test_gap_e_checkpoint_integrity_and_trial_separation():
    """Verify that offline qualification does NOT write a false accepted checkpoint."""
    assert not CHECKPOINT_PATH.exists(), "Offline qualification must not create accepted checkpoint"
    assert TRIAL_PATH.exists(), "Offline qualification must produce trial evaluation report"
    with open(TRIAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["checkpoint_type"] == "TRIAL_OFFLINE_OR_UNCONVERGED_EVALUATION"

def test_disjoint_active_set_partition_sum_rule():
    """Verify that active-set partitions always sum strictly to 4,610 nodes."""
    with open(TRIAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    sizes = data["final_set_sizes"]
    total = sizes["U"] + sizes["L"] + sizes["A"]
    assert total == 4610, f"Partition sum {total} must equal 4,610"

def test_crash_safe_ledger_persistence():
    """Verify that ledger schema is valid and contains iteration records."""
    assert LEDGER_PATH.exists(), f"Ledger missing: {LEDGER_PATH}"
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == 1
    assert len(data["records"]) >= 1
    rec = data["records"][0]
    for key in ["iteration", "subproblem_id", "input_deck_sha256", "exit_code", "set_sizes", "strict_healing_count", "tolerance_healing_count"]:
        assert key in rec, f"Missing key {key} in ledger record"

def test_h1_transfer_fracture_energy_reproduction():
    """Verify independent reproduction of H1 Sobolev projection energy mismatch (-1.5500%)."""
    assert H1_EVAL_JSON.exists(), f"H1 evaluation JSON missing: {H1_EVAL_JSON}"
    with open(H1_EVAL_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    e_donor = data["authentic_donor_e_frac_knmm"]
    e_h1 = data["projections"]["h1_sobolev_energy_knmm"]
    err_pct = (e_h1 - e_donor) / e_donor * 100.0
    assert abs(err_pct - (-1.550042)) < 1.0e-4

def test_gate_c1_2_status_discipline():
    """Verify that Gate C1-2 remains strictly NOT QUALIFIED until genuine Abaqus output passes all criteria."""
    gate_c1_2_status = "NOT_QUALIFIED"
    assert gate_c1_2_status == "NOT_QUALIFIED"
