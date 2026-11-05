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

    assert rec["task_id"] in [
        "F1623-METHOD-C-SAME-MESH-CHECKPOINT03-PROVENANCE-CORRECTION",
        "F1627-METHOD-C-SAME-MESH-EXTRACTOR-CONTRACT-QUALIFICATION"
    ]
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


def test_driver_extractor_nodes_unpacking():
    """Verify that SameMeshControlPDASDriver correctly unpacks 'nodes' list from extractor."""
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.state_transfer.driver_same_mesh_control_pdas import SameMeshControlPDASDriver
    from scripts.state_transfer.driver_package146_147_pdas_continuation import driving_history

    endpoint_p = PKG172_DIR / "evidence" / "1420344.mmaster02" / "endpoint.json"
    assert endpoint_p.is_file(), f"Evidence endpoint.json missing: {endpoint_p}"
    endpoint_data = json.loads(endpoint_p.read_text(encoding="utf-8"))

    driver = SameMeshControlPDASDriver(
        package=PKG172_DIR,
        output=PKG172_DIR / "test_out",
        extractor=PKG172_DIR / "smoke_import.py"
    )
    driver.load()

    # Mock runner that returns authentic endpoint_data
    driver.runner = lambda directory, job, role, step_idx: dict(endpoint_data)

    # 1. Test mechanical unpacking
    new_d, new_u, res = driver.solve_subproblem(
        step_idx=1, outer=1, sub_idx=0, role="mechanical",
        damage=driver.d0, active=set(driver.d0), displacement=None,
        history=driver.h0, target_u=driver.target_uy
    )
    assert len(new_u) == 13278, f"Expected 13,278 displacements, got {len(new_u)}"
    assert set(new_u.keys()) == set(driver.mesh.nodes.keys()), "Displacement node keys mismatch"
    assert all(len(v) == 2 and math.isfinite(v[0]) and math.isfinite(v[1]) for v in new_u.values())

    # 2. Test driving_history with unpacked new_u
    zero_baseline = {(e, g): 0.0 for e in driver.mesh.elements for g in range(1, 5)}
    psi_k = driving_history(driver.mesh, new_u, zero_baseline)
    assert len(psi_k) == 51984, f"Expected 51,984 GP histories, got {len(psi_k)}"
    assert all(math.isfinite(v) and v >= 0.0 for v in psi_k.values())

    # 3. Test phase unpacking
    new_d2, new_u2, res2 = driver.solve_subproblem(
        step_idx=1, outer=1, sub_idx=0, role="phase",
        damage=driver.d0, active=set(driver.d0), displacement=new_u,
        history=driver.h0, target_u=driver.target_uy
    )
    assert len(new_d2) == 13278, f"Expected 13,278 damage values, got {len(new_d2)}"
    assert all(math.isfinite(v) and 0.0 <= v <= 1.0 for v in new_d2.values())
    assert all(new_d2[n] >= driver.d0[n] for n in new_d2), "Damage irreversibility violated"


def test_deck_node_print_output_restored():
    """Verify that _deck() writes *Node Print, frequency=1\\nU\\n for companion .dat table."""
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.state_transfer.driver_same_mesh_control_pdas import SameMeshControlPDASDriver

    for pkg_dir in [PKG172_DIR, PKG173_DIR]:
        driver = SameMeshControlPDASDriver(
            package=pkg_dir,
            output=pkg_dir / "test_out",
            extractor=REPO_ROOT / "scripts/validation/extract_package148_iteration.py"
        )
        driver.load()

        mech_deck = driver._deck(
            step_idx=1, role="mechanical", damage=driver.d0, active=set(driver.d0),
            displacement=None, history=driver.h0, target_u=driver.target_uy
        )
        assert "*Node Print, frequency=1\nU\n" in mech_deck, "Mechanical deck missing *Node Print"

        disp = {n: (0.0, 0.0) for n in driver.mesh.nodes}
        phase_deck = driver._deck(
            step_idx=1, role="phase", damage=driver.d0, active=set(driver.d0),
            displacement=disp, history=driver.h0, target_u=driver.target_uy
        )
        assert "*Node Print, frequency=1\nU\n" in phase_deck, "Phase deck missing *Node Print"

        # Verify on-disk dynamic iteration decks
        prefix = "P172" if "172" in str(pkg_dir) else "P173"
        for deck_name in [f"{prefix}_ITER1_MECH.inp", f"{prefix}_ITER1_PHASE.inp"]:
            deck_path = pkg_dir / deck_name
            assert deck_path.is_file(), f"Deck missing: {deck_path}"
            assert "*Node Print" in deck_path.read_text(encoding="utf-8"), f"*Node Print missing in {deck_name}"


def test_phase_raw_healing_diagnostics_and_bounds_validation():
    """Verify raw phase-field preservation, healing telemetry, and bounds fail-closed checks."""
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.state_transfer.driver_same_mesh_control_pdas import SameMeshControlPDASDriver

    driver = SameMeshControlPDASDriver(
        package=PKG172_DIR,
        output=PKG172_DIR / "test_out",
        extractor=REPO_ROOT / "scripts/validation/extract_package148_iteration.py"
    )
    driver.load()

    endpoint_p = PKG172_DIR / "evidence" / "1420344.mmaster02" / "endpoint.json"
    base_endpoint = json.loads(endpoint_p.read_text(encoding="utf-8"))

    # Case A: Slight raw healing on node 10 before projection
    modified_endpoint = dict(base_endpoint)
    mod_nodes = []
    target_node = 10
    d0_val = driver.d0[target_node]
    healed_raw_d = max(0.0, d0_val - 0.005)
    for row in base_endpoint["nodes"]:
        nid = row[0]
        if nid == target_node:
            mod_nodes.append([nid, row[1], row[2], healed_raw_d])
        else:
            mod_nodes.append(list(row))
    modified_endpoint["nodes"] = mod_nodes

    driver.runner = lambda directory, job, role, step_idx: dict(modified_endpoint)
    disp = {n: (0.0, 0.0) for n in driver.mesh.nodes}

    new_d, new_u, res = driver.solve_subproblem(
        step_idx=1, outer=1, sub_idx=0, role="phase",
        damage=driver.d0, active=set(driver.d0), displacement=disp,
        history=driver.h0, target_u=driver.target_uy
    )

    # Assert raw healing was preserved and diagnosed
    assert "raw_damage" in res, "raw_damage missing from subproblem results"
    assert res["raw_damage"][target_node] == healed_raw_d, "Raw healing damage was not preserved"
    assert res["raw_healing_violations"] >= 1, "Expected raw healing violation count >= 1"
    assert res["raw_healing_min"] < 0.0, f"Expected negative raw_healing_min, got {res['raw_healing_min']}"

    # Assert documented projection enforced irreversibility
    assert new_d[target_node] == d0_val, f"Projected damage should equal d0: {new_d[target_node]} vs {d0_val}"
    assert all(new_d[n] >= driver.d0[n] for n in new_d), "Projected damage violated irreversibility"

    # Case B: Two-component phase output rejected fail-closed
    two_comp_endpoint = dict(base_endpoint)
    two_comp_endpoint["nodes"] = [[r[0], r[1], r[2]] for r in base_endpoint["nodes"]]
    driver.runner = lambda directory, job, role, step_idx: dict(two_comp_endpoint)

    with pytest.raises(ValueError, match="rejected two-component phase output"):
        driver.solve_subproblem(
            step_idx=1, outer=1, sub_idx=0, role="phase",
            damage=driver.d0, active=set(driver.d0), displacement=disp,
            history=driver.h0, target_u=driver.target_uy
        )

    # Case C: Unphysical raw damage out of bounds rejected fail-closed
    unphysical_endpoint = dict(base_endpoint)
    unphysical_endpoint["nodes"] = [
        [r[0], r[1], r[2], 1.5 if r[0] == 1 else r[3]] for r in base_endpoint["nodes"]
    ]
    driver.runner = lambda directory, job, role, step_idx: dict(unphysical_endpoint)

    with pytest.raises(ValueError, match="unphysical raw damage out of bounds"):
        driver.solve_subproblem(
            step_idx=1, outer=1, sub_idx=0, role="phase",
            damage=driver.d0, active=set(driver.d0), displacement=disp,
            history=driver.h0, target_u=driver.target_uy
        )


def test_finalize_coupled_acceptance_authentic_schema():
    """Verify finalize_coupled_acceptance() reads authentic rf2_kN/total_energy_kNmm and fails closed."""
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.state_transfer.driver_same_mesh_control_pdas import (
        SameMeshControlPDASDriver,
        PDASReEquilibrationSolver,
        DONOR_REFERENCE_FORCE_KN,
        DONOR_REFERENCE_TOTAL_ENERGY_KNMM
    )

    driver = SameMeshControlPDASDriver(
        package=PKG172_DIR,
        output=PKG172_DIR / "test_out",
        extractor=REPO_ROOT / "scripts/validation/extract_package148_iteration.py"
    )
    driver.load()

    endpoint_p = PKG172_DIR / "evidence" / "1420344.mmaster02" / "endpoint.json"
    authentic_endpoint = json.loads(endpoint_p.read_text(encoding="utf-8"))

    # Initial consistent displacement
    disp_csv = PKG172_DIR / "nodal_displacements_initial.csv"
    disp = {}
    with open(disp_csv, "r") as f:
        reader = csv.reader(f)
        next(reader)
        for r in reader:
            if r:
                disp[int(r[0])] = (float(r[1]), float(r[2]))

    solver = PDASReEquilibrationSolver(driver.mesh, driver.d0, driver.h0)

    # 1. Authentic endpoint: verify successful parsing and drift <= 2%
    summary, passed = driver.finalize_coupled_acceptance(
        u_trial=disp,
        u_abaqus=disp,
        history_trial=driver.h0,
        damage_relaxed=driver.d0,
        consistent_u=disp,
        consistent_endpoint=authentic_endpoint,
        solver=solver,
        step_idx=1,
        outer=1,
        target_uy=driver.target_uy,
        delta_d=1e-6,
        delta_u_relaxed=1e-10,
        delta_u_raw=1e-10,
        delta_h=1e-5,
        pdas_active_count=0,
        pdas_free_count=13278
    )

    assert math.isclose(summary["reaction_force_kN"], 0.17992419004440308, rel_tol=1e-6)
    assert math.isclose(summary["rf2_kN"], 0.17992419004440308, rel_tol=1e-6)
    assert math.isclose(summary["total_energy_kNmm"], 0.00022639903, rel_tol=1e-6)
    assert summary["force_drift_pct"] <= 2.0, f"Force drift {summary['force_drift_pct']}% exceeds 2%"
    assert summary["energy_drift_pct"] <= 2.0, f"Energy drift {summary['energy_drift_pct']}% exceeds 2%"
    assert summary["force_gate_pass"] is True
    assert summary["energy_gate_pass"] is True

    # 2. Fail closed on missing reaction force
    missing_rf = dict(authentic_endpoint)
    missing_rf.pop("rf2_kN", None)
    missing_rf.pop("reaction_force_kn", None)
    missing_rf.pop("reaction_force_kN", None)
    with pytest.raises(KeyError, match="missing reaction force"):
        driver.finalize_coupled_acceptance(
            u_trial=disp, u_abaqus=disp, history_trial=driver.h0, damage_relaxed=driver.d0,
            consistent_u=disp, consistent_endpoint=missing_rf, solver=solver,
            step_idx=1, outer=1, target_uy=driver.target_uy,
            delta_d=1e-6, delta_u_relaxed=1e-10, delta_u_raw=1e-10, delta_h=1e-5,
            pdas_active_count=0, pdas_free_count=13278
        )

    # 3. Fail closed on missing total energy
    missing_energy = dict(authentic_endpoint)
    missing_energy.pop("total_energy_kNmm", None)
    missing_energy.pop("total_energy_knmm", None)
    with pytest.raises(KeyError, match="missing total energy"):
        driver.finalize_coupled_acceptance(
            u_trial=disp, u_abaqus=disp, history_trial=driver.h0, damage_relaxed=driver.d0,
            consistent_u=disp, consistent_endpoint=missing_energy, solver=solver,
            step_idx=1, outer=1, target_uy=driver.target_uy,
            delta_d=1e-6, delta_u_relaxed=1e-10, delta_u_raw=1e-10, delta_h=1e-5,
            pdas_active_count=0, pdas_free_count=13278
        )

    # 4. Fail closed on non-finite force or energy
    nan_rf = dict(authentic_endpoint, rf2_kN=float("nan"))
    with pytest.raises(ValueError, match="non-finite reaction force"):
        driver.finalize_coupled_acceptance(
            u_trial=disp, u_abaqus=disp, history_trial=driver.h0, damage_relaxed=driver.d0,
            consistent_u=disp, consistent_endpoint=nan_rf, solver=solver,
            step_idx=1, outer=1, target_uy=driver.target_uy,
            delta_d=1e-6, delta_u_relaxed=1e-10, delta_u_raw=1e-10, delta_h=1e-5,
            pdas_active_count=0, pdas_free_count=13278
        )


def test_end_to_end_coupled_pipeline_qualification(tmp_path):
    """Verify complete end-to-end execution pipeline from solve to final checkpoint serialization."""
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.state_transfer.driver_same_mesh_control_pdas import (
        SameMeshControlPDASDriver,
        driving_history
    )

    driver = SameMeshControlPDASDriver(
        package=PKG172_DIR,
        output=tmp_path / "run_out",
        extractor=REPO_ROOT / "scripts/validation/extract_package148_iteration.py"
    )
    driver.load()

    endpoint_p = PKG172_DIR / "evidence" / "1420344.mmaster02" / "endpoint.json"
    authentic_endpoint = json.loads(endpoint_p.read_text(encoding="utf-8"))

    # Mock runner simulating both mechanical and phase subproblems
    def mock_runner(directory, job, role, step_idx):
        if role == "mechanical":
            return dict(authentic_endpoint)
        else:
            # Phase subproblem returns authentic nodes with valid damage component
            phase_endpoint = dict(authentic_endpoint)
            phase_endpoint["nodes"] = [
                [r[0], r[1], r[2], driver.d0[r[0]]] for r in authentic_endpoint["nodes"]
            ]
            return phase_endpoint

    driver.runner = mock_runner

    # 1. Step 1 Mechanical: unpacks displacements
    _, u1, res_mech = driver.solve_subproblem(
        step_idx=1, outer=1, sub_idx=0, role="mechanical",
        damage=driver.d0, active=set(driver.d0), displacement=None,
        history=driver.h0, target_u=driver.target_uy
    )
    assert len(u1) == 13278

    # 2. Driving history: 51,984 GP histories
    zero_baseline = {(e, g): 0.0 for e in driver.mesh.elements for g in range(1, 5)}
    psi_1 = driving_history(driver.mesh, u1, zero_baseline)
    assert len(psi_1) == 51984
    h_updated = {k: max(driver.h0[k], psi_1[k]) for k in driver.h0}

    # 3. Step 1 Phase: unpacks damage with raw healing telemetry
    d1, _, res_phase = driver.solve_subproblem(
        step_idx=1, outer=1, sub_idx=0, role="phase",
        damage=driver.d0, active=set(driver.d0), displacement=u1,
        history=h_updated, target_u=driver.target_uy
    )
    assert len(d1) == 13278
    assert "raw_healing_min" in res_phase

    # 4. Final acceptance with authentic consistent endpoint
    from scripts.state_transfer.driver_same_mesh_control_pdas import PDASReEquilibrationSolver
    solver = PDASReEquilibrationSolver(driver.mesh, d1, h_updated)

    summary, passed = driver.finalize_coupled_acceptance(
        u_trial=u1,
        u_abaqus=u1,
        history_trial=h_updated,
        damage_relaxed=d1,
        consistent_u=u1,
        consistent_endpoint=authentic_endpoint,
        solver=solver,
        step_idx=1,
        outer=1,
        target_uy=driver.target_uy,
        delta_d=1e-6,
        delta_u_relaxed=1e-10,
        delta_u_raw=1e-10,
        delta_h=1e-5,
        pdas_active_count=0,
        pdas_free_count=13278
    )

    # 5. Assert checkpoint and summary serialization
    summary_file = tmp_path / "run_out" / "same_mesh_control_equilibration_summary.json"
    ckpt_file = tmp_path / "run_out" / "converged_same_mesh_control_checkpoint.json"

    assert summary_file.is_file(), "Summary file was not created"
    assert ckpt_file.is_file(), "Checkpoint file was not created"

    saved_ckpt = json.loads(ckpt_file.read_text(encoding="utf-8"))
    assert saved_ckpt["reaction_force_kN"] == summary["reaction_force_kN"]
    assert saved_ckpt["total_energy_kNmm"] == summary["total_energy_kNmm"]
    assert len(saved_ckpt["displacement"]) == 13278
    assert len(saved_ckpt["damage"]) == 13278
    assert len(saved_ckpt["history"]) == 51984


def test_evaluate_same_mesh_controls_contract(tmp_path):
    from scripts.validation.evaluate_same_mesh_controls import build_evaluation_summary

    arm1_dir = tmp_path / "arm1"
    arm2_dir = tmp_path / "arm2"
    arm1_dir.mkdir()
    arm2_dir.mkdir()

    # Synthetic telemetry matching realistic observed behavior:
    # Arm 1 has high delta_H (~100 MPa) due to averaging
    t1 = [
        {"outer": 1, "pdas_active_count": 12558, "delta_d": 7.2e-3, "delta_u": 0.0, "delta_h": 0.0, "kkt_post_passed": True, "complementarity": 1e-9},
        {"outer": 2, "pdas_active_count": 1000, "delta_d": 1.2e-2, "delta_u": 5.0e-5, "delta_h": 100.0, "kkt_post_passed": True, "complementarity": 1e-9}
    ]
    # Arm 2 has low delta_H (~0.1 MPa) due to isoparametric bilinear transfer
    t2 = [
        {"outer": 1, "pdas_active_count": 13083, "delta_d": 2.6e-4, "delta_u": 0.0, "delta_h": 0.0, "kkt_post_passed": True, "complementarity": 1e-11},
        {"outer": 2, "pdas_active_count": 3000, "delta_d": 1.3e-3, "delta_u": 1.0e-6, "delta_h": 0.1, "kkt_post_passed": True, "complementarity": 1e-11}
    ]

    (arm1_dir / "live_iteration_telemetry.json").write_text(json.dumps(t1), encoding="utf-8")
    (arm2_dir / "live_iteration_telemetry.json").write_text(json.dumps(t2), encoding="utf-8")

    summary = build_evaluation_summary(arm1_dir, arm2_dir)

    assert summary["schema"] == 1
    assert summary["task_id"] == "F1626-METHOD-C-SAME-MESH-REPAIRED-CONTROL-EXECUTION"
    verdict = summary["scientific_verdict"]
    assert verdict["history_gradient_defect_confirmed"] is True
    assert verdict["delta_H_reduction_factor"] == 1000.0
    assert verdict["isoparametric_superiority_established"] is True


