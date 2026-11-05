#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_same_mesh_control_staging.py
=================================
Unit and regression test suite verifying the paired same-mesh control experiment
Checkpoint 03 provenance correction, dynamic first-iteration deck generation,
and authentic cluster datacheck qualification under Task F1623.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG172_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "172_c5_same_mesh_old_control"
PKG173_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "173_c5_same_mesh_corrected_control"
CP03_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "167_c5_package167_r3_c2_2_continuation" / "evidence" / "1419566.mmaster02" / "converged_checkpoint_03.json"
PKG167_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "167_c5_package167_r3_c2_2_continuation"
RECEIPT_PATH = REPO_ROOT / "results" / "validation" / "same_mesh_control_datacheck_receipt.json"
REPORT_PATH = REPO_ROOT / "results" / "validation" / "same_mesh_control_staging_report.md"
TASK_DEF_PATH = REPO_ROOT / "project_coordination" / "task_definitions" / "F1623-METHOD-C-SAME-MESH-CHECKPOINT03-PROVENANCE-CORRECTION.json"

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_frozen_uel_integrity():
    for pkg_dir in [PKG172_DIR, PKG173_DIR]:
        uel_p = pkg_dir / "f42_mixed_uel.for"
        assert uel_p.is_file(), f"f42_mixed_uel.for missing in {pkg_dir.name}"
        assert sha256_file(uel_p) == FROZEN_UEL_HASH, f"UEL hash mismatch in {pkg_dir.name}"


def test_package_structure_and_files():
    required_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "driver_same_mesh_control_pdas.py",
        "f42_mixed_uel.for",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "PACKAGE_MANIFEST.json",
        "run_datacheck.sh",
        "smoke_import.py",
        "P172_ITER1_MECH.inp" if "172" in str(PKG172_DIR) else "P173_ITER1_MECH.inp",
        "P172_ITER1_PHASE.inp" if "172" in str(PKG172_DIR) else "P173_ITER1_PHASE.inp"
    ]
    for fn in [
        "active_set_boundary_cards.inc", "d_lower_bounds.csv", "driver_same_mesh_control_pdas.py",
        "f42_mixed_uel.for", "initial_conditions_solution.inc", "job_notifications.sh",
        "nodal_displacements_initial.csv", "nodal_phase_field_initial.csv", "PACKAGE_MANIFEST.json",
        "run_datacheck.sh", "smoke_import.py", "P172_ITER1_MECH.inp", "P172_ITER1_PHASE.inp"
    ]:
        assert (PKG172_DIR / fn).is_file(), f"Missing {fn} in Package 172"

    for fn in [
        "active_set_boundary_cards.inc", "d_lower_bounds.csv", "driver_same_mesh_control_pdas.py",
        "f42_mixed_uel.for", "initial_conditions_solution.inc", "job_notifications.sh",
        "nodal_displacements_initial.csv", "nodal_phase_field_initial.csv", "PACKAGE_MANIFEST.json",
        "run_datacheck.sh", "smoke_import.py", "P173_ITER1_MECH.inp", "P173_ITER1_PHASE.inp"
    ]:
        assert (PKG173_DIR / fn).is_file(), f"Missing {fn} in Package 173"


def test_checkpoint03_provenance_and_cp02_rejection():
    """
    Fail-closed test: asserts 100% agreement with Checkpoint 03 across all 13,278 nodes,
    and explicitly rejects Checkpoint 02 initial conditions.
    """
    assert CP03_PATH.is_file(), f"Checkpoint 03 missing at {CP03_PATH}"
    with open(CP03_PATH, "r", encoding="utf-8") as f:
        cp03 = json.load(f)

    cp03_u = {int(item[0]): (float(item[1]), float(item[2])) for item in cp03["displacement"]}
    cp03_d = {int(item[0]): float(item[1]) for item in cp03["damage"]}
    assert len(cp03_u) == 13278
    assert len(cp03_d) == 13278

    # Load CP02 (Package 167) initial conditions to prove separation
    pkg167_u_csv = PKG167_DIR / "nodal_displacements_initial.csv"
    pkg167_u = {}
    with open(pkg167_u_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for r in reader:
            if r:
                pkg167_u[int(r[0])] = (float(r[1]), float(r[2]))

    # Test both Package 172 and 173
    for pkg_dir, label in [(PKG172_DIR, "Package 172"), (PKG173_DIR, "Package 173")]:
        # 1. Displacement verification
        u_csv = pkg_dir / "nodal_displacements_initial.csv"
        pkg_u = {}
        with open(u_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for r in reader:
                if r:
                    pkg_u[int(r[0])] = (float(r[1]), float(r[2]))
        assert len(pkg_u) == 13278

        # Max error against CP03 must be <= 1e-12 mm
        max_err_cp03 = max(math.hypot(pkg_u[n][0] - cp03_u[n][0], pkg_u[n][1] - cp03_u[n][1]) for n in cp03_u)
        assert max_err_cp03 <= 1.0e-12, f"{label} displacement differs from Checkpoint 03: {max_err_cp03:.4e} mm"

        # Fail-closed check: verify displacement is NOT Checkpoint 02 (must differ by ~5.22e-6 mm)
        max_diff_cp02 = max(math.hypot(pkg_u[n][0] - pkg167_u[n][0], pkg_u[n][1] - pkg167_u[n][1]) for n in cp03_u)
        assert max_diff_cp02 > 5.0e-6, f"{label} improperly matches Checkpoint 02: diff = {max_diff_cp02:.4e} mm"

        # 2. Damage verification
        d_csv = pkg_dir / "nodal_phase_field_initial.csv"
        pkg_d = {}
        with open(d_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for r in reader:
                if r:
                    pkg_d[int(r[0])] = float(r[1])
        assert len(pkg_d) == 13278
        max_err_d = max(abs(pkg_d[n] - cp03_d[n]) for n in cp03_d)
        assert max_err_d <= 1.0e-12, f"{label} damage differs from Checkpoint 03: {max_err_d:.4e}"

        # 3. Active set boundary cards
        inc_file = pkg_dir / "active_set_boundary_cards.inc"
        with open(inc_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("**")]
        assert len(lines) == 13278
        for line in lines:
            parts = [p.strip() for p in line.split(",")]
            nid = int(parts[0])
            d_val = float(parts[3])
            assert abs(d_val - cp03_d[nid]) <= 1.0e-12, f"Active set card mismatch at node {nid}"


def test_identical_nodal_and_boundary_assets():
    shared_files = [
        "active_set_boundary_cards.inc",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "job_notifications.sh"
    ]
    for fn in shared_files:
        hash_172 = sha256_file(PKG172_DIR / fn)
        hash_173 = sha256_file(PKG173_DIR / fn)
        assert hash_172 == hash_173, f"Shared asset {fn} differs between Package 172 and 173"


def test_dynamic_first_iteration_decks_conformance():
    """
    Verifies that authentic dynamic first-iteration decks exist, have complete quadrature cards,
    and incorporate the verified Checkpoint 03 boundary conditions.
    """
    for pkg_dir, pfx in [(PKG172_DIR, "P172"), (PKG173_DIR, "P173")]:
        mech_inp = pkg_dir / f"{pfx}_ITER1_MECH.inp"
        phase_inp = pkg_dir / f"{pfx}_ITER1_PHASE.inp"
        assert mech_inp.is_file(), f"Missing {mech_inp.name}"
        assert phase_inp.is_file(), f"Missing {phase_inp.name}"

        mech_text = mech_inp.read_text(encoding="utf-8")
        phase_text = phase_inp.read_text(encoding="utf-8")

        # Must have Initial Conditions SOLUTION cards
        assert "*Initial Conditions, type=SOLUTION" in mech_text
        assert "*Initial Conditions, type=SOLUTION" in phase_text

        # Target displacement uy = 0.0018703125442191958 mm
        assert "0.0018703125442191958" in mech_text

        # Step names
        assert f"*Step, name=C5_Control_Step1_mechanical" in mech_text
        assert f"*Step, name=C5_Control_Step1_phase" in phase_text


def test_manifest_verification_and_anderson_disabled():
    with open(PKG172_DIR / "PACKAGE_MANIFEST.json", "r", encoding="utf-8") as f:
        m172 = json.load(f)
    with open(PKG173_DIR / "PACKAGE_MANIFEST.json", "r", encoding="utf-8") as f:
        m173 = json.load(f)

    # Anderson disabled in both arms
    assert m172["numerical_parameters"]["anderson_enabled"] is False
    assert m173["numerical_parameters"]["anderson_enabled"] is False

    # Checkpoint 03 provenance recorded
    assert "Checkpoint 03" in m172["donor_source"]["checkpoint"]
    assert "Checkpoint 03" in m173["donor_source"]["checkpoint"]
    assert m172["donor_source"]["target_uy_mm"] == 0.0018703125442191958

    # Identical numerical solver settings
    for key in ["damping_omega_d_stage1", "damping_omega_d_stage2", "damping_omega_u_stage1", "damping_omega_u_stage2",
                "max_active_cardinality", "max_symmetric_diff", "max_added_nodes", "stabilization_window",
                "rollback_factor", "divergence_factor", "catastrophic_delta_d_cap", "max_outer_iterations",
                "delta_d_tol", "delta_u_tol_mm", "delta_h_tol_MPa", "kkt_tol"]:
        assert m172["numerical_parameters"][key] == m173["numerical_parameters"][key], f"Mismatch in {key}"

    # Receiver mesh identical
    assert m172["receiver_mesh"]["elements_quad"] == 12996
    assert m173["receiver_mesh"]["elements_quad"] == 12996
    assert m172["receiver_mesh"]["physical_nodes"] == 13278
    assert m173["receiver_mesh"]["physical_nodes"] == 13278


def test_arm1_history_perturbation():
    with open(PKG172_DIR / "PACKAGE_MANIFEST.json", "r", encoding="utf-8") as f:
        m172 = json.load(f)
    peak_err = m172["transfer_operator"]["history_perturbation_peak_MPa"]
    rms_err = m172["transfer_operator"]["history_perturbation_rms_MPa"]
    assert abs(peak_err - 6.3491) < 0.01, f"Expected ~6.3491 MPa peak perturbation, got {peak_err}"
    assert abs(rms_err - 0.0681) < 0.01, f"Expected ~0.0681 MPa RMS perturbation, got {rms_err}"


def test_arm2_history_identity():
    with open(PKG173_DIR / "PACKAGE_MANIFEST.json", "r", encoding="utf-8") as f:
        m173 = json.load(f)
    peak_err = m173["transfer_operator"]["history_perturbation_peak_MPa"]
    rms_err = m173["transfer_operator"]["history_perturbation_rms_MPa"]
    assert peak_err <= 1.0e-12, f"Expected machine identity (<= 1e-12 MPa), got {peak_err}"
    assert rms_err <= 1.0e-14, f"Expected machine identity RMS (<= 1e-14 MPa), got {rms_err}"


def test_datacheck_receipt_validity():
    assert RECEIPT_PATH.is_file(), "same_mesh_control_datacheck_receipt.json missing"
    with open(RECEIPT_PATH, "r", encoding="utf-8") as f:
        rec = json.load(f)

    assert rec["task_id"] == "F1623-METHOD-C-SAME-MESH-CHECKPOINT03-PROVENANCE-CORRECTION"
    assert rec["status"] == "DATACHECKS_PASSED_ALL_8_SUBPROBLEMS_EXIT_0"
    assert rec["production_pbs_submissions"] == 0
    assert rec["zero_pbs_enforced"] is True
    assert rec["frozen_uel_sha256"] == FROZEN_UEL_HASH

    # Check Arm 1 all 4 datachecks
    arm1 = rec["experimental_matrix"]["arm_1_control_old"]
    assert arm1["anderson_enabled"] is False
    for sub in ["preliminary_mechanical_datacheck", "preliminary_phase_datacheck",
                "dynamic_iter1_mechanical_datacheck", "dynamic_iter1_phase_datacheck"]:
        assert arm1[sub]["exit_code"] == 0, f"Arm 1 {sub} exit code non-zero"
        assert arm1[sub]["errors"] == 0, f"Arm 1 {sub} had errors"
        assert arm1[sub]["status"] == "PASS", f"Arm 1 {sub} status not PASS"

    # Check Arm 2 all 4 datachecks
    arm2 = rec["experimental_matrix"]["arm_2_control_corrected"]
    assert arm2["anderson_enabled"] is False
    for sub in ["preliminary_mechanical_datacheck", "preliminary_phase_datacheck",
                "dynamic_iter1_mechanical_datacheck", "dynamic_iter1_phase_datacheck"]:
        assert arm2[sub]["exit_code"] == 0, f"Arm 2 {sub} exit code non-zero"
        assert arm2[sub]["errors"] == 0, f"Arm 2 {sub} had errors"
        assert arm2[sub]["status"] == "PASS", f"Arm 2 {sub} status not PASS"


def test_dat_files_zero_errors_and_completion_banners():
    dat_files = [
        PKG172_DIR / "P172_MECHANICAL_DC.dat",
        PKG172_DIR / "P172_PHASE_DC.dat",
        PKG172_DIR / "P172_ITER1_MECH.dat",
        PKG172_DIR / "P172_ITER1_PHASE.dat",
        PKG173_DIR / "P173_MECHANICAL_DC.dat",
        PKG173_DIR / "P173_PHASE_DC.dat",
        PKG173_DIR / "P173_ITER1_MECH.dat",
        PKG173_DIR / "P173_ITER1_PHASE.dat"
    ]
    for df in dat_files:
        assert df.is_file(), f"Missing {df.name}"
        text = df.read_text(encoding="utf-8", errors="replace")
        assert "***ERROR" not in text, f"Error found in {df.name}"
        assert ("THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in text or "ANALYSIS DATACHECK COMPLETE" in text), \
            f"Missing completion banner in {df.name}"


def test_task_definition_conformance():
    assert TASK_DEF_PATH.is_file(), "Task definition missing"
    with open(TASK_DEF_PATH, "r", encoding="utf-8") as f:
        tdef = json.load(f)
    assert tdef["task_id"] == "F1623-METHOD-C-SAME-MESH-CHECKPOINT03-PROVENANCE-CORRECTION"
    assert tdef["governance"]["max_new_pbs_submissions"] == 0
    assert tdef["governance"]["zero_pbs_enforced"] is True


def test_deterministic_master_deck_selection_with_shuffled_inps():
    import tempfile
    import shutil
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "state_transfer"))
    from driver_same_mesh_control_pdas import SameMeshControlPDASDriver

    # Create dummy package with multiple .inp files in inverted/arbitrary order using tempfile
    temp_dir = Path(tempfile.mkdtemp(prefix="test_pkg_"))
    try:
        pkg_test = temp_dir / "pkg"
        pkg_test.mkdir()
        (pkg_test / "PACKAGE_MANIFEST.json").write_text('{"schema": 1}', encoding="utf-8")
        (pkg_test / "nodal_displacements_initial.csv").write_text("node_id,u1_mm,u2_mm\n", encoding="utf-8")
        (pkg_test / "nodal_phase_field_initial.csv").write_text("node_id,damage\n", encoding="utf-8")
        (pkg_test / "d_lower_bounds.csv").write_text("element_id,d1,d2,d3,d4,h1,h2,h3,h4\n", encoding="utf-8")

        # Inverted order: iter and DC decks before master deck
        master_inp = pkg_test / "M1_C5_PACKAGE172_OLD_CONTROL_REEQUILIBRATION.inp"
        # Copy actual master inp from PKG172_DIR
        master_inp.write_text((PKG172_DIR / "M1_C5_PACKAGE172_OLD_CONTROL_REEQUILIBRATION.inp").read_text(encoding="utf-8"), encoding="utf-8")

        (pkg_test / "P172_ITER1_MECH.inp").write_text("** ITER1 MECH", encoding="utf-8")
        (pkg_test / "P172_ITER1_PHASE.inp").write_text("** ITER1 PHASE", encoding="utf-8")
        (pkg_test / "P172_MECHANICAL_DC.inp").write_text("** MECH DC", encoding="utf-8")
        (pkg_test / "P172_PHASE_DC.inp").write_text("** PHASE DC", encoding="utf-8")

        # Test deterministic resolution
        driver = SameMeshControlPDASDriver(package=pkg_test, output=temp_dir / "out", extractor=temp_dir / "ex.py")
        (pkg_test / "nodal_displacements_initial.csv").write_text(
            (PKG172_DIR / "nodal_displacements_initial.csv").read_text(encoding="utf-8"), encoding="utf-8"
        )
        (pkg_test / "nodal_phase_field_initial.csv").write_text(
            (PKG172_DIR / "nodal_phase_field_initial.csv").read_text(encoding="utf-8"), encoding="utf-8"
        )
        (pkg_test / "d_lower_bounds.csv").write_text(
            (PKG172_DIR / "d_lower_bounds.csv").read_text(encoding="utf-8"), encoding="utf-8"
        )

        driver.load()
        assert driver.deck_path.name == "M1_C5_PACKAGE172_OLD_CONTROL_REEQUILIBRATION.inp"

        # Test explicit master deck specification
        driver_explicit = SameMeshControlPDASDriver(
            package=pkg_test, output=temp_dir / "out", extractor=temp_dir / "ex.py",
            master_deck_name="M1_C5_PACKAGE172_OLD_CONTROL_REEQUILIBRATION.inp"
        )
        driver_explicit.load()
        assert driver_explicit.deck_path.name == "M1_C5_PACKAGE172_OLD_CONTROL_REEQUILIBRATION.inp"

        # Test fail-closed on missing master deck
        master_inp.unlink()
        driver_missing = SameMeshControlPDASDriver(package=pkg_test, output=temp_dir / "out", extractor=temp_dir / "ex.py")
        with pytest.raises(FileNotFoundError, match="Deterministic master deck selection failed"):
            driver_missing.load()

        # Test fail-closed on ambiguous master decks
        (pkg_test / "M1_C5_PACKAGE172_OLD_CONTROL_REEQUILIBRATION.inp").write_text("** M1", encoding="utf-8")
        (pkg_test / "M1_C5_PACKAGE172_EXTRA_RESTART.inp").write_text("** M2", encoding="utf-8")
        driver_ambiguous = SameMeshControlPDASDriver(package=pkg_test, output=temp_dir / "out", extractor=temp_dir / "ex.py")
        with pytest.raises(ValueError, match="Ambiguous master input deck"):
            driver_ambiguous.load()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_actual_staged_driver_load_on_both_packages():
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "state_transfer"))
    from driver_same_mesh_control_pdas import SameMeshControlPDASDriver

    # Arm 1: Package 172
    d172 = SameMeshControlPDASDriver(
        package=PKG172_DIR,
        output=PKG172_DIR / "test_out",
        extractor=PKG172_DIR / "smoke_import.py"
    )
    d172.load()
    assert d172.deck_path.name == "M1_C5_PACKAGE172_OLD_CONTROL_REEQUILIBRATION.inp"
    assert len(d172.mesh.elements) == 12996
    assert len(d172.mesh.nodes) == 13278
    assert len(d172.u0) == 13278
    assert len(d172.d0) == 13278
    assert len(d172.h0) == 51984

    # Arm 2: Package 173
    d173 = SameMeshControlPDASDriver(
        package=PKG173_DIR,
        output=PKG173_DIR / "test_out",
        extractor=PKG173_DIR / "smoke_import.py"
    )
    d173.load()
    assert d173.deck_path.name == "M1_C5_PACKAGE173_CORRECTED_CONTROL_REEQUILIBRATION.inp"
    assert len(d173.mesh.elements) == 12996
    assert len(d173.mesh.nodes) == 13278
    assert len(d173.u0) == 13278
    assert len(d173.d0) == 13278
    assert len(d173.h0) == 51984


def test_discrepancy_analysis_consistency_and_active_set_characterization():
    disc_p = REPO_ROOT / "results" / "validation" / "checkpoint_02_vs_03_discrepancy_analysis.json"
    assert disc_p.is_file(), "checkpoint_02_vs_03_discrepancy_analysis.json missing"
    with open(disc_p, "r", encoding="utf-8") as f:
        d = json.load(f)

    # Reconciled physical evolution values across continuation load increment
    disp = d["discrepancies"]["displacement"]
    assert 5.0e-6 <= disp["max_abs_delta_u_mm"] <= 5.5e-6
    assert 3.0e-6 <= disp["rms_delta_u_mm"] <= 3.5e-6

    dam = d["discrepancies"]["damage"]
    assert 2.0e-8 <= dam["max_abs_delta_d"] <= 4.0e-8
    assert 4.0e-9 <= dam["rms_delta_d"] <= 6.0e-9

    hist = d["discrepancies"]["history"]
    assert 0.07 <= hist["max_abs_delta_h_MPa"] <= 0.08
    assert 0.0010 <= hist["rms_delta_h_MPa"] <= 0.0015

    # Reconciled active-set and localized damage characterization
    char = d["active_set_and_damage_characterization"]
    assert char["nodes_localized_d_ge_095"] == 0, "Expected 0 nodes with d >= 0.95 at CP03"
    assert char["nodes_localized_d_ge_065"] == 23, "Expected 23 nodes with d >= 0.65"
    assert char["nodes_localized_d_ge_060"] == 66, "Expected 66 nodes with d >= 0.60"
    assert char["written_boundary_cards_in_inc"] == 13278, "Expected 13,278 written boundary cards"
    assert "dynamically at runtime" in char["pdas_active_set_mechanism"]

    # Reconciled conclusion
    conclusion = d["conclusion"]
    assert "4.29e-4" not in conclusion, "Stale damage figure found in conclusion"
    assert "tolerance violation" not in conclusion.lower(), "Incorrect tolerance-violation phrasing found"
    assert "physical state evolution" in conclusion.lower()
