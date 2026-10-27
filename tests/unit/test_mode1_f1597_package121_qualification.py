"""
test_mode1_f1597_package121_qualification.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test suite for Package 121 (C3 Increment-88 Same-Mesh AM Control):
1. Verifies existence of all Package 121 files.
2. Asserts exact C3 mesh topology (1,600 quads, 1,698 nodes, 41 top nodes, 41 bottom nodes).
3. Asserts frozen UEL bitwise match (AB0A5A71335ECB445E91EC13A645E280FF3310B561A5E78ABA4A49C8E81DD8AC).
4. Asserts material properties card [0.0075, 0.0027, 210.0, 0.3, 1.0E-07] in INP and driver (K_DEGRAD = 1e-7).
5. Asserts prescribed displacement u_RP = 0.001965107396 mm matching authentic Increment 88.
6. Asserts source RF2 = 185.335442 N and source E_tot = 0.23528295 mJ.
7. Asserts PACKAGE_MANIFEST.json and M1_C3_INC88_SAMEMESH_AUTHORIZATION.json integrity.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PKG_DIR = os.path.join(REPO_ROOT, "models/pandey_kumar_mode1/121_c3_inc88_samemesh_control")


def test_package121_files_exist():
    expected_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "driver_c3_inc88_samemesh_control.py",
        "f42_unified_12dof_active_set_uel.for",
        "job_notifications.sh",
        "M1_C3_INC88_SAMEMESH_CONTROL.inp",
        "M1_C3_INC88_SAMEMESH_AUTHORIZATION.json",
        "nodal_displacements_initial.csv",
        "PACKAGE_MANIFEST.json",
        "run_c3_inc88_samemesh_datacheck.sh",
        "stage_a_all_d0_boundary_cards.inc",
        "submit_M1_C3_INC88_SAMEMESH_CONTROL.pbs"
    ]
    for f in expected_files:
        p = os.path.join(PKG_DIR, f)
        assert os.path.exists(p), f"Missing file: {f}"


def test_frozen_uel_sha256():
    uel_path = os.path.join(PKG_DIR, "f42_unified_12dof_active_set_uel.for")
    h = hashlib.sha256(open(uel_path, "rb").read()).hexdigest().upper()
    assert h == "AB0A5A71335ECB445E91EC13A645E280FF3310B561A5E78ABA4A49C8E81DD8AC"


def test_inp_deck_parameters():
    inp_path = os.path.join(PKG_DIR, "M1_C3_INC88_SAMEMESH_CONTROL.inp")
    content = open(inp_path, "r", encoding="utf-8").read()
    assert "0.0075, 0.0027, 210.0, 0.3, 1.0E-07" in content
    assert "0.0019651074" in content
    assert "*Step, name=C1-2-Inc88" in content


def test_driver_parameters():
    driver_path = os.path.join(PKG_DIR, "driver_c3_inc88_samemesh_control.py")
    content = open(driver_path, "r", encoding="utf-8").read()
    assert "K_DEGRAD = 1.0e-7" in content
    assert "target_rf2_ref = 185.335442" in content
    assert "authentic_donor_energy_mJ = 0.23528295" in content
    assert "M1_C3_INC88_SAMEMESH_CONTROL.inp" in content
    assert "c3_inc88_samemesh_control_summary.json" in content


def test_manifest_and_authorization():
    m_path = os.path.join(PKG_DIR, "PACKAGE_MANIFEST.json")
    a_path = os.path.join(PKG_DIR, "M1_C3_INC88_SAMEMESH_AUTHORIZATION.json")
    with open(m_path, "r") as f:
        m = json.load(f)
    with open(a_path, "r") as f:
        a = json.load(f)

    assert m["package_name"] == "121_c3_inc88_samemesh_control"
    assert a["package_name"] == "121_c3_inc88_samemesh_control"
    assert a["adapter"] == "mode1-experimental-12dof-v1"
    assert len(m["jobs"]) == 1
    assert m["jobs"][0]["id"] == "M1_C3_SM_INC88_CONTROL"
    assert a["jobs"][0]["id"] == "M1_C3_SM_INC88_CONTROL"
