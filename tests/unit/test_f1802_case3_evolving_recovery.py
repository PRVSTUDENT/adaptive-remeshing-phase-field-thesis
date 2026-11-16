# -*- coding: utf-8 -*-
"""
tests/unit/test_f1802_case3_evolving_recovery.py
Task F1802: Case 3 Method A.2 Evolving Recovery Donor Qualification and Causal Remesh.

Validates:
1. Physical mesh file existence, non-emptiness, whole-file SHA-256 and body SHA-256.
2. Finite element topology: 27,916 total elements (27,117 quads [97.14%], 799 tris).
3. Positive signed Jacobians: min det(J) > 0 (+1.018e-3 > 0, zero non-positive Jacobians).
4. Aspect ratio compliance: max AR <= 4.0 (2.436), median AR <= 2.0 (1.239), 0 violations > 4.0.
5. Spatial resolution with corrected shoelace formula:
   - Primary corridor: 6,130 elements, mean h ~ 0.2937 mm, 58.91% <= l0, 11.47% <= l0/2.
   - Secondary corridor: 1,423 elements, mean h ~ 0.5060 mm, min h ~ 0.1580 mm, 5.06% <= l0, 0.00% <= l0/2.
   - Far field: 2,660 elements, coarsening ratio 2.64x >= 2.0x (Gate 6 PASS).
6. Evolutionary impact against F1800 (pre-initiation 3.0%):
   - Secondary corridor coverage <= l0 increases from 1.24% to 5.06% (+3.82% pts, 4.08x coverage increase).
   - Secondary corridor min h drops from 0.2223 mm to 0.1580 mm.
   - Secondary corridor <= l0/2 remains strictly 0.00% (min h = 0.1580 mm > l0/2 = 0.1425 mm).
7. Machine receipts and donor qualification receipts:
   - Valid JSON, stress units in kN/mm^2 (GPa), donor SHA-256 8ED4E418..., error_target = 3.0%.
   - Documented auxiliary degraded-continuum constitutive nature distinct from UEL stress.
8. Governance & PBS constraints:
   - 0 new PBS jobs consumed, cumulative preserved at 35, frozen UEL maintained, MASTER_GOAL_STATUS = OPEN.
"""

from __future__ import print_function
import os
import sys
import json
import math
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

F1802_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "252_f1802_case3_evolving_recovery")
PHYS_INP = os.path.join(F1802_DIR, "PK_F1802_CASE_3_ADAPT_PHYS.inp")
REMESH_RECEIPT = os.path.join(F1802_DIR, "PK_F1802_CASE3_EVOLVING_REMESH_RECEIPT.json")
DONOR_RECEIPT = os.path.join(F1802_DIR, "PK_F1802_CASE3_DONOR_QUALIFICATION_RECEIPT.json")
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "f1802_case3_native_miseseri.json")
REPORT_PATH = os.path.join(REPO_ROOT, "docs", "validation", "F1802_CASE3_EVOLVING_RECOVERY_QUALIFICATION_REPORT.md")

EXPECTED_BODY_SHA256 = "34B036E40307C9A4A38F674309B9DA64EF20C4CD23A6212CAFCFC61F55F44D28"
EXPECTED_INP_SHA256 = "251ECD959A5127BC4A2003E496314FE808408B2AC5CE38E124DF10C4AF0E3C46"
EXPECTED_DONOR_SHA256 = "8ED4E4189A1B1EBA4E8D39DA6FB8C6A9CBE22C9D1227E235C52F4679B4821AD1"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def compute_mesh_body_sha256(filepath):
    with open(filepath, "r") as f:
        lines = f.readlines()
    h = hashlib.sha256()
    for line in lines:
        if not line.strip().startswith("**"):
            h.update(line.strip().encode("utf-8") + b"\n")
    return h.hexdigest().upper()


def test_f1802_physical_mesh_hashes_and_existence():
    """Verify F1802 physical mesh INP existence, size, whole-file SHA-256 and body SHA-256."""
    assert os.path.exists(PHYS_INP), "Physical INP missing: " + PHYS_INP
    size = os.path.getsize(PHYS_INP)
    assert size > 0, "Physical INP is empty"
    assert size == 2006768, "Physical INP size changed from expected 2006768 bytes"

    file_sha = compute_sha256(PHYS_INP)
    assert file_sha == EXPECTED_INP_SHA256, "Physical INP whole-file SHA-256 mismatch: " + file_sha

    body_sha = compute_mesh_body_sha256(PHYS_INP)
    assert body_sha == EXPECTED_BODY_SHA256, "Mesh body SHA-256 mismatch: " + body_sha
    assert body_sha != "0DAFAD93742A4988AF068070F7BFE72FE71CD3C353506C346584A208E71EF6AC", "F1802 body must differ from F1800 3.0% baseline"
    assert body_sha != "AF53DCD3148F065E9F881BF0D22F8DB82C3140C665672B10B45C0B31AC211A4D", "F1802 body must differ from F1801 5.0% baseline"


def test_f1802_element_topology_and_mesh_quality():
    """Verify independent finite element mesh quality: quads, signed Jacobians, aspect ratio."""
    assert os.path.exists(REMESH_RECEIPT), "Remesh receipt missing"
    with open(REMESH_RECEIPT, "r") as f:
        data = json.load(f)

    mesh = data["physical_mesh"]
    assert mesh["total_elements"] == 27916, "Total elements must be exactly 27,916"
    assert mesh["quad_count"] == 27117, "Quad count must be 27,117"
    assert mesh["tri_count"] == 799, "Tri count must be 799"
    assert mesh["quad_percent"] >= 90.0, "Quad percent must be >= 90%"
    assert abs(mesh["quad_percent"] - 97.14) < 0.1, "Quad percent should be ~97.14%"

    assert mesh["min_det_j"] > 0.0, "Signed Jacobian must be strictly positive"
    assert mesh["non_positive_jacobians"] == 0, "Zero non-positive Jacobians required"
    assert mesh["zero_negative_jacobians"] is True

    assert mesh["max_aspect_ratio"] <= 4.0, "Max aspect ratio must be <= 4.0"
    assert abs(mesh["max_aspect_ratio"] - 2.436) < 0.05, "Max aspect ratio should be ~2.436"
    assert mesh["ar_violations_gt_4"] == 0, "Zero aspect ratio violations > 4.0"
    assert mesh["median_aspect_ratio"] <= 2.0, "Median aspect ratio must be <= 2.0"
    assert mesh["min_corner_angle_deg"] >= 20.0, "Min corner angle must be >= 20 deg"
    assert mesh["max_corner_angle_deg"] <= 160.0, "Max corner angle must be <= 160 deg"


def test_f1802_spatial_resolution_and_evolving_donor_effect():
    """Verify spatial resolution in primary, secondary, and far-field zones and evolving donor effect."""
    with open(REMESH_RECEIPT, "r") as f:
        data = json.load(f)

    sp = data["spatial_resolution"]
    pri = sp["primary_corridor_notch_to_hole"]
    sec = sp["secondary_corridor_hole_to_boundary"]
    far = sp["far_field_background"]
    coarsen = sp["far_to_core_coarsening_ratio"]

    assert pri["count"] == 6130, "Primary corridor elements must be 6,130"
    assert abs(pri["mean_mm"] - 0.2937) < 0.01, "Primary corridor mean h should be ~0.2937 mm"
    assert abs(pri["pct_le_l0"] - 58.91) < 0.1, "Primary % <= l0 should be ~58.91%"
    assert abs(pri["pct_le_l0_half"] - 11.47) < 0.1, "Primary % <= l0/2 should be ~11.47%"

    assert sec["count"] == 1423, "Secondary corridor elements must be 1,423"
    assert abs(sec["mean_mm"] - 0.5060) < 0.01, "Secondary corridor mean h should be ~0.5060 mm"
    assert abs(sec["pct_le_l0"] - 5.06) < 0.1, "Secondary corridor % <= l0 should be ~5.06%"
    assert sec["pct_le_l0_half"] == 0.0, "Secondary corridor % <= l0/2 must be strictly 0.0%"
    assert abs(sec["min_mm"] - 0.1580) < 0.01, "Secondary corridor min h should be ~0.1580 mm"
    assert sec["min_mm"] > sp["l0_half_mm"], "Secondary min h must be > l0/2 (0.1425 mm)"

    assert far["count"] == 2660, "Far field elements must be 2,660"
    assert abs(far["mean_mm"] - 0.7768) < 0.01, "Far field mean h should be ~0.7768 mm"

    assert coarsen >= 2.0, "Far-to-primary coarsening ratio must be >= 2.0x"
    assert abs(coarsen - 2.64) < 0.05, "Coarsening ratio should be ~2.64x"


def test_f1802_comparative_resolution_vs_f1800_and_f1801():
    """Verify comparative resolution: secondary % <= l0 gains 3.82% pts vs F1800 while % <= l0/2 remains 0%."""
    with open(REMESH_RECEIPT, "r") as f:
        data = json.load(f)

    comp = data["comparative_resolution_vs_f1800_and_f1801"]
    sec_l0 = comp["secondary_pct_le_l0"]
    sec_l0_half = comp["secondary_pct_le_l0_half"]
    sec_min_h = comp["secondary_min_h_mm"]

    assert sec_l0["f1800_precritical_3pct"] == 1.24
    assert sec_l0["f1801_precritical_5pct"] == 0.00
    assert abs(sec_l0["f1802_evolving_state2_3pct"] - 5.06) < 0.1
    assert abs(sec_l0["evolutionary_gain_vs_f1800_pct_pts"] - 3.82) < 0.1

    assert sec_l0_half["f1800_precritical_3pct"] == 0.00
    assert sec_l0_half["f1801_precritical_5pct"] == 0.00
    assert sec_l0_half["f1802_evolving_state2_3pct"] == 0.00
    assert sec_l0_half["evolutionary_gain_vs_f1800_pct_pts"] == 0.00

    assert abs(sec_min_h["f1800_precritical_3pct"] - 0.2234) < 0.001
    assert sec_min_h["f1801_precritical_5pct"] == 0.3235
    assert abs(sec_min_h["f1802_evolving_state2_3pct"] - 0.1580) < 0.01


def test_f1802_donor_qualification_receipt_and_constitutive_nature():
    """Verify donor qualification receipt declares auxiliary degraded-elastic constitutive nature."""
    assert os.path.exists(DONOR_RECEIPT), "Donor qualification receipt missing"
    with open(DONOR_RECEIPT, "r") as f:
        donor = json.load(f)

    assert donor["donor_sha256"] == EXPECTED_DONOR_SHA256
    assert donor["donor_size_bytes"] == 1676760
    assert donor["stress_unit"] == "kN/mm^2 (GPa)"
    assert "miseseri_stats_kn_per_mm2" in donor
    assert "misesavg_stats_kn_per_mm2" in donor

    char = donor["donor_state_characterization"]
    assert char["physical_regime"] == "PRIMARY_PROPAGATION_HOLE_ARREST_STATE"
    assert char["prescribed_displacement_uy_mm"] == 0.200
    assert char["distinct_from_uel_stress"] is True
    assert "Auxiliary discrete-stiffness recovery model" in char["constitutive_nature"]

    reg = donor["regional_error_distribution_kn_per_mm2"]
    assert abs(reg["ratio_secondary_to_primary_mean"] - 1.495) < 0.05, "Ratio sec/prim should be ~1.50"


def test_f1802_governance_and_coordination_invariants():
    """Verify active task, session lock, UEL hash, and PBS submission invariants."""
    task_file = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(task_file, "r") as f:
        task = json.load(f)

    assert task["task_id"] in [
        "F1800-CASE3-PRECRITICAL-NATIVE-MISESERI-SCALE-AND-CAUSAL-REMESH-TEST",
        "F1801-CASE3-NATIVE-MISESERI-ERROR-TARGET-EFFICIENCY-TEST",
        "F1802-CASE3-METHOD-A2-EVOLVING-RECOVERY-DONOR-QUALIFICATION-AND-CAUSAL-REMESH",
        "F1803-CASE3-STATE2-DEGRADED-MODULUS-FIDELITY-NATIVE-REMESH",
        "F1804-CASE2-DISTAL-DEGRADED-MODULUS-RECOVERY-REMESH",
        "F1805-CASE2-OUTERMOST-DISTAL-NATIVE-MISESERI-TARGET-SENSITIVITY"
    ]
    assert task["master_goal_status"] == "OPEN"
    assert task["frozen_uel_sha256"] == FROZEN_UEL_SHA256
    assert task["cumulative_pbs_submissions"] == 35
    assert task["max_new_pbs_submissions"] == 0
    assert task["submissions_consumed"] == 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
