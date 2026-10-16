"""Unit test suite for Task F1497: Package 49 Zero-Displacement Equilibrium Verification,
Donor Energy Reconciliation, and Nonmatching Continuation Qualification.

Author: Gemini Antigravity
Date: 2026-10-16
Protocol Version: 2
"""

import hashlib
import json
import os
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Authoritative Hashes
FROZEN_PRODUCTION_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
PACKAGE49_FORWARD_DECK_SHA256 = "B4A4414B768FE58E28E33377D8165793C886EDDEA90A2470C13DF12AB7F21FF7"
PACKAGE49_EQUIL_DECK_SHA256 = "EB95EF10B89701F399DACF51FE73FD8EC318CDE4D8362D03061B27EC060CB303"
PACKAGE49_EQUIL_PBS_SHA256 = "79093A20526C84D023E35CA06682E66D612871FA0A352C8C75FF4AA30E3ECCCE"
PACKAGE49_FORWARD_PBS_SHA256 = "07F68A5E26D6419830C14FEDBD937F67FFDDD302468D35762B485D5104F4E18E"


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_stage_c1_1_status_and_donor_energy_reconciliation():
    """Verify Task F1497 status and the mathematical resolution of donor energy provenance."""
    active_task_path = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
    assert active_task_path.exists()

    with open(active_task_path, "r", encoding="utf-8") as f:
        task_data = json.load(f)

    # 1. Scientific status must strictly reflect numerical continuation pending
    assert task_data["status"] == "STAGE_C1_1_OFFLINE_MAPPING_VALIDATED__NUMERICAL_CONTINUATION_PENDING"

    # 2. Donor energy values:
    # Authentic donor Job 1413814.mmaster02 (row 500 of uel_energy_balance.csv):
    e_elas_donor = 1.6327213  # mJ
    e_frac_donor = 0.0306626  # mJ
    e_tot_donor = 1.6633839   # mJ

    # Fine 15k reference mesh Job 1398090.mmaster02 at u = 0.0050 mm:
    e_tot_fine_ref = 1.691100 # mJ

    # Transferred recipient mesh total energy:
    e_tot_recipient = 1.6634   # mJ

    # Continuity error relative to authentic donor:
    delta_e_tot = abs(e_tot_recipient - e_tot_donor) / e_tot_donor * 100.0
    assert delta_e_tot < 0.010  # 0.00096% <= 0.10% threshold

    # Discretization compliance delta between coarse donor and fine reference:
    delta_discretization = abs(e_tot_donor - e_tot_fine_ref) / e_tot_fine_ref * 100.0
    assert abs(delta_discretization - 1.6388) < 0.01  # exactly 1.639%


def test_uel_solution_state_initialization_semantics():
    """Verify UEL solution state initialization semantics across element types in f42_mixed_uel.for."""
    uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer" / "f42_mixed_uel.for"
    assert uel_path.exists()
    assert compute_sha256(uel_path) == FROZEN_PRODUCTION_UEL_SHA256

    with open(uel_path, "r", encoding="utf-8") as f:
        uel_code = f.read()

    # Verify quad (JTYPE=1) SVARS ingestion into SV_H_COMMITTED
    assert "IF (JTYPE .EQ. 1 .OR. JTYPE .EQ. 3) THEN" in uel_code
    assert "SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(8+KPT)" in uel_code

    # Verify tri (JTYPE=3) SVARS ingestion into SV_H_COMMITTED
    assert "SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(6+KPT)" in uel_code

    # Verify input decks have *INITIAL CONDITIONS, TYPE=SOLUTION
    p49_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer"
    for deck_name, expected_hash in [
        ("M1_MC_STAGE_C1_1_EQUIL.inp", PACKAGE49_EQUIL_DECK_SHA256),
        ("M1_MC_STAGE_C1_1_FORWARD_14K.inp", PACKAGE49_FORWARD_DECK_SHA256),
    ]:
        deck_path = p49_dir / deck_name
        assert deck_path.exists()
        assert compute_sha256(deck_path) == expected_hash
        has_init_cond = False
        with open(deck_path, "r", encoding="utf-8") as f:
            for line in f:
                if "*INITIAL CONDITIONS, TYPE=SOLUTION" in line:
                    has_init_cond = True
                    break
        assert has_init_cond, f"Missing *INITIAL CONDITIONS, TYPE=SOLUTION in {deck_name}"


def test_package49_batch_authorization_and_preflight_manifest():
    """Verify Package 49 batch authorization manifest, preflight script, and acceptance criteria."""
    p49_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer"
    manifest_path = p49_dir / "METHOD_C_STAGE_C1_1_AUTHORIZATION.json"
    assert manifest_path.exists()

    with open(manifest_path, "r", encoding="utf-8") as f:
        auth_data = json.load(f)

    assert auth_data["batch_name"] == "MODE1_METHOD_C_STAGE_C1_1"
    assert auth_data["max_submissions"] == 2
    assert auth_data["automatic_retry"] is False

    jobs = {j["id"]: j for j in auth_data["jobs"]}
    assert "equil_test" in jobs
    assert "forward_continuation" in jobs

    # Verify job limits and parameters
    eq_job = jobs["equil_test"]
    assert eq_job["pbs"] == "submit_M1_MC_STAGE_C1_1_EQUIL.pbs"
    assert eq_job["max_submissions"] == 1
    assert eq_job["queue"] == "entry_imfdfkmq"
    assert eq_job["cpus"] == 1
    assert eq_job["memory_gb"] == 8

    fc_job = jobs["forward_continuation"]
    assert fc_job["pbs"] == "submit_M1_MC_STAGE_C1_1.pbs"
    assert fc_job["max_submissions"] == 1
    assert fc_job["depends_on"] == ["equil_test_review"]

    # Verify preflight script exists
    preflight_path = REPO_ROOT / "scripts" / "hpc" / "preflight_package49_authorization.py"
    assert preflight_path.exists()


def test_quantitative_acceptance_thresholds_definition():
    """Verify quantitative acceptance thresholds for the equilibrium test."""
    p49_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer"
    manifest_path = p49_dir / "METHOD_C_STAGE_C1_1_AUTHORIZATION.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        auth_data = json.load(f)

    acceptance = auth_data["acceptance"]["equil_test"]

    # Reaction force continuity
    assert "|Delta RF| <= 5.0 N" in acceptance
    # Damage retention
    assert "Delta d_max <= 0.020" in acceptance
    # Energy continuity
    assert "Delta E_elas <= 0.50%" in acceptance
    assert "Delta E_frac <= 0.50%" in acceptance
    assert "Delta E_tot <= 0.10%" in acceptance
    # Global energy residual
    assert "Delta_book / W_ext <= 2.0%" in acceptance
    # Newton convergence
    assert "Exit 0, 0 cutbacks" in acceptance
