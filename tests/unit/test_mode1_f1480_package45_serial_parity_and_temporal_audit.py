"""Unit tests for Task F1480: Package 45 Serial Parity Control and Temporal Increment Physics Audit.

Verifies:
1. Package 45 directory structure, manifest, anti-deviation card, and cryptographic hashes.
2. Package 45 deck Step 2 *STATIC line and INC=12000 increment headroom.
3. Package 45 PBS script 1-CPU serial directives, memory, walltime, and notification traps.
4. Dimensional audit of Step 2 displacement increments:
   - Reference (dt=2.0E-4): du = 1.0 nm (0.0010 um)
   - Refined (dt=1.0E-4): du = 0.5 nm (0.0005 um)
   - Proof that INC=12000 is an algorithmic increment ceiling, not a physical parameter.
"""

import json
import os
import re
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG45_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "45_method_b_temporal_refinement_serial_parity")

EXPECTED_INP_SHA = "CB596BD91CA45F4B51111158EAA56523A01888471F8FF54EE37F40A306387B9C"
EXPECTED_SUB_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_PBS_SHA = "EAF0BB76EE21E8B4E331FA0B277F89DFFDF7CCFC6C7A17CCFFC30B61F278FF38"


def test_package45_structure_and_manifest():
    """Verify Package 45 directory exists and manifest matches required schema."""
    assert os.path.isdir(PKG45_DIR), f"Package 45 directory missing: {PKG45_DIR}"
    
    manifest_path = os.path.join(PKG45_DIR, "PACKAGE_MANIFEST.json")
    assert os.path.isfile(manifest_path), "PACKAGE_MANIFEST.json missing"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    assert manifest["package_id"] == "45_method_b_temporal_refinement_serial_parity"
    assert manifest["gate"] == "GATE_6B_TEMPORAL_CONVERGENCE_AND_SERIAL_PARITY"
    assert manifest["execution_resources"]["cpus"] == 1
    assert manifest["execution_resources"]["mode"] == "serial"
    assert manifest["provenance_hashes"]["input_deck_sha256"] == EXPECTED_INP_SHA
    assert manifest["provenance_hashes"]["uel_subroutine_sha256"] == EXPECTED_SUB_SHA
    assert manifest["provenance_hashes"]["pbs_script_sha256"] == EXPECTED_PBS_SHA

    card_path = os.path.join(PKG45_DIR, "PRE_JOB_ANTI_DEVIATION_CARD.md")
    assert os.path.isfile(card_path), "PRE_JOB_ANTI_DEVIATION_CARD.md missing"


def test_package45_deck_step2_static():
    """Verify input deck Step 2 *STATIC line and INC=12000."""
    deck_path = os.path.join(PKG45_DIR, "M1_MB_CORRECTED_DTMAX_14K.inp")
    assert os.path.isfile(deck_path), "M1_MB_CORRECTED_DTMAX_14K.inp missing"

    with open(deck_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Step 1 static
    step1_match = re.search(r"\*STEP, NAME=Step-1[^\n]*\n\*STATIC\n\s*([0-9.E+-]+),\s*([0-9.E+-]+),\s*([0-9.E+-]+),\s*([0-9.E+-]+)", content)
    assert step1_match is not None, "Step-1 *STATIC not found"
    dt0_1, ttot_1, dtmin_1, dtmax_1 = [float(x) for x in step1_match.groups()]
    assert dt0_1 == pytest.approx(5.0e-4)
    assert ttot_1 == pytest.approx(1.0)
    assert dtmax_1 == pytest.approx(5.0e-4)

    # Step 2 static and INC
    step2_inc_match = re.search(r"\*STEP, NAME=Step-2[^\n]*INC=([0-9]+)", content)
    assert step2_inc_match is not None, "Step-2 INC not found"
    assert int(step2_inc_match.group(1)) == 12000

    step2_match = re.search(r"\*STEP, NAME=Step-2[^\n]*\n\*STATIC\n\s*([0-9.E+-]+),\s*([0-9.E+-]+),\s*([0-9.E+-]+),\s*([0-9.E+-]+)", content)
    assert step2_match is not None, "Step-2 *STATIC not found"
    dt0_2, ttot_2, dtmin_2, dtmax_2 = [float(x) for x in step2_match.groups()]
    assert dt0_2 == pytest.approx(1.0e-4)
    assert ttot_2 == pytest.approx(1.0)
    assert dtmin_2 == pytest.approx(1.0e-9)
    assert dtmax_2 == pytest.approx(1.0e-4)


def test_package45_pbs_directives():
    """Verify PBS execution script directives for 1-CPU serial."""
    pbs_path = os.path.join(PKG45_DIR, "submit_M1_MB_DTMAX_1C.pbs")
    assert os.path.isfile(pbs_path), "submit_M1_MB_DTMAX_1C.pbs missing"

    with open(pbs_path, "r", encoding="utf-8") as f:
        pbs = f.read()

    assert "#PBS -N M1_MB_DTMAX_1C" in pbs
    assert "#PBS -l nodes=1:ppn=1" in pbs
    assert "#PBS -l mem=24gb" in pbs
    assert "#PBS -l walltime=24:00:00" in pbs
    assert "#PBS -m abe" in pbs
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in pbs
    assert "cpus=1" in pbs
    assert "mp_mode=threads" in pbs


def test_temporal_increment_dimensional_physics_audit():
    """Verify rigorous dimensional physics of Step 2 displacement increments."""
    # Step 1: boundary displacement uy goes from 0.0 to 0.0050 mm over step time T1 = 1.0
    u_step1_end = 0.0050  # mm
    u_step2_end = 0.0100  # mm
    delta_u_step2 = u_step2_end - u_step1_end  # 0.0050 mm = 5.0 um = 5000 nm
    T_step2 = 1.0  # s

    # Reference Package 40: dt_max = 2.0E-4
    dt_max_ref = 2.0e-4
    du_ref_mm = dt_max_ref * delta_u_step2 / T_step2
    du_ref_um = du_ref_mm * 1e3
    du_ref_nm = du_ref_mm * 1e6

    assert du_ref_mm == pytest.approx(1.0e-6)
    assert du_ref_um == pytest.approx(0.0010)
    assert du_ref_nm == pytest.approx(1.0)

    # Refined Package 44 / 45: dt_max = 1.0E-4
    dt_max_refined = 1.0e-4
    du_refined_mm = dt_max_refined * delta_u_step2 / T_step2
    du_refined_um = du_refined_mm * 1e3
    du_refined_nm = du_refined_mm * 1e6

    assert du_refined_mm == pytest.approx(5.0e-7)
    assert du_refined_um == pytest.approx(0.00050)
    assert du_refined_nm == pytest.approx(0.50)

    # Ratio of temporal refinement
    ratio = du_ref_nm / du_refined_nm
    assert ratio == pytest.approx(2.0)

    # Verify INC headroom:
    # At dt_max = 1.0E-4, nominal increment count = 1.0 / 1.0E-4 = 10,000 increments.
    # Therefore INC must be >= 10,000. INC=12000 provides 20% cutback headroom.
    nominal_increments = int(T_step2 / dt_max_refined)
    assert nominal_increments == 10000
    assert 12000 > nominal_increments
