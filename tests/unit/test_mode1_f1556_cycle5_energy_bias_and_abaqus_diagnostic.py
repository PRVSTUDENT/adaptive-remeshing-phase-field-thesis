#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test suite for Task F1556:
Audit and resolution of donor energy-evaluation bias, formal 3-state decomposition,
physical Clapeyron audit, spatial error concentration, and Abaqus same-displacement
receiver re-equilibration diagnostic (Job 1414955).
"""

import sys
import os
import json
import csv
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

C5_DIR = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation"

def test_01_donor_element_discrepancy_ledger():
    ledger_csv = C5_DIR / "CYCLE5_DONOR_ELEMENT_ENERGY_DISCREPANCY_LEDGER.csv"
    assert ledger_csv.exists(), f"Discrepancy ledger missing: {ledger_csv}"

    rows = []
    with open(ledger_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    assert len(rows) == 29293, f"Expected 29,293 element rows, got {len(rows)}"

    # Sort by absolute elastic energy discrepancy
    sorted_elas = sorted(rows, key=lambda x: abs(float(x["delta_Eelas_mJ"])), reverse=True)
    top_10 = sorted_elas[:10]

    # Verify that top 10 error contributors are situated along the crack wake / process zone
    for r in top_10:
        xc = float(r["centroid_x"])
        yc = float(r["centroid_y"])
        assert 0.45 <= xc <= 0.66, f"Top contributor {r['element_id']} at x={xc} outside crack corridor"
        assert 0.48 <= yc <= 0.52, f"Top contributor {r['element_id']} at y={yc} outside crack corridor"
        # Confirm that damage is high and under-predicted by continuous L2 projection
        d_avg = float(r["d_elem_avg"])
        d_sdv14 = float(r["d_odb_sdv14"])
        assert d_avg < d_sdv14, f"Element {r['element_id']}: d_avg ({d_avg}) >= d_sdv14 ({d_sdv14})"

    # Verify that top 10 elements contribute a substantial portion of the total discrepancy
    top10_sum = sum(float(r["delta_Eelas_mJ"]) for r in top_10)
    assert top10_sum > 0.015, f"Expected top 10 sum > 0.015 mJ, got {top10_sum:.6f} mJ"

def test_02_three_state_energy_decomposition():
    summary_json = C5_DIR / "CYCLE5_RECON_EQUIL_SUMMARY.json"
    assert summary_json.exists(), f"Summary JSON missing: {summary_json}"

    with open(summary_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    decomp = data.get("three_state_energy_decomposition", {})
    stA = decomp.get("state_A_authentic_solved_donor", {})
    stB = decomp.get("state_B_reconstructed_donor_mesh", {})
    stC = decomp.get("state_C_mapped_recipient_mesh", {})

    # State A (Package 65 ODB volume integration)
    assert abs(stA["E_elas_mJ"] - 1.678941) < 1e-4
    assert abs(stA["E_frac_uJ"] - 697.1766) < 1e-2
    assert abs(stA["E_total_mJ"] - 2.376118) < 1e-4

    # State B (Reconstructed on unchanged donor mesh)
    assert abs(stB["E_elas_mJ"] - 1.720474) < 1e-4
    assert abs(stB["E_frac_uJ"] - 683.0884) < 1e-2
    assert abs(stB["E_total_mJ"] - 2.403562) < 1e-4

    # State C (Mapped on 34,094 recipient mesh)
    assert abs(stC["E_elas_mJ"] - 1.725088) < 1e-4
    assert abs(stC["E_frac_uJ"] - 683.7366) < 1e-2
    assert abs(stC["E_total_mJ"] - 2.408824) < 1e-4

    # Deltas
    d_recon = decomp["delta_reconstruction_B_minus_A"]
    assert abs(d_recon["delta_E_elas_pct"] - 2.4738) < 1e-2
    assert abs(d_recon["delta_E_total_pct"] - 1.1550) < 1e-2

    d_remap = decomp["delta_remapping_C_minus_B"]
    assert abs(d_remap["delta_E_elas_pct"] - 0.2682) < 1e-2
    assert abs(d_remap["delta_E_total_pct"] - 0.2189) < 1e-2

def test_03_physical_interpretation_and_clapeyron_audit():
    # Clapeyron formula 0.5 * F * u for instantaneous elastic energy at u = 0.0060 mm
    u_disp = 0.0060
    # Donor Package 65
    F_donor = 0.55964726  # kN
    E_elas_clapeyron_donor = 0.5 * F_donor * u_disp * 1e3  # mJ
    assert abs(E_elas_clapeyron_donor - 1.678941) < 1e-4, "Clapeyron identity failed for donor elastic energy"

    # Total energy is NOT 0.5 * F * u
    E_total_donor = 2.376118  # mJ
    assert abs(E_total_donor - E_elas_clapeyron_donor) > 0.60, "Total energy must differ by E_frac from 0.5*F*u"

    # Solved Recipient Job 1414955
    F_solved = 0.56573995  # kN
    E_elas_clapeyron_solved = 0.5 * F_solved * u_disp * 1e3  # mJ
    assert abs(E_elas_clapeyron_solved - 1.697220) < 1e-4, "Clapeyron identity failed for recipient elastic energy"

def test_04_job_1414955_reequilibration_diagnostic():
    summary_json = C5_DIR / "CYCLE5_RECON_EQUIL_SUMMARY.json"
    with open(summary_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["job_id"] == "1414955.mmaster02"
    assert data["exit_status"] == 0
    assert data["increments"] == 1
    assert data["cutbacks"] == 0
    assert data["iterations"] == 2
    assert data["mesh_elements"] == 34094

    solv = data["solver_energies"]
    assert abs(solv["E_elas_mJ"] - 1.697220) < 1e-3
    assert abs(solv["E_frac_uJ"] - 683.6044) < 1e-2
    assert abs(solv["E_total_mJ"] - 2.380824) < 1e-3

    deltas = data["solver_to_donor_deltas"]
    assert abs(deltas["delta_E_total_pct"] - 0.1981) < 1e-2
    assert abs(deltas["delta_RF_pct"] - 1.089) < 1e-2

    # Verification of strict governance hold on loaded continuation
    gov = data["governance"]
    assert "LOADED_CONTINUATION_STRICTLY_ON_HOLD" in gov["status"]
    assert gov["method_c_verdict"] == "NOT_YET_QUALIFIED"
