"""Unit tests for Package 157 Revision 8 Candidate Qualification & Reference Gate Separation.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import hashlib
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
R6_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "157_c4_package157_c1_2_continuation_r6"
R8_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "157_c4_package157_c1_2_continuation_r8"
FROZEN_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_r8_package_directory_and_manifest_specifications():
    assert R8_DIR.is_dir(), f"Missing R8 directory: {R8_DIR}"
    manifest_path = R8_DIR / "PACKAGE_MANIFEST.json"
    assert manifest_path.is_file(), "Missing R8 PACKAGE_MANIFEST.json"

    with open(manifest_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    assert pkg["schema"] == 1
    assert pkg["package"] == 157
    assert pkg["revision"] == "R8"
    assert pkg["baseline_uy_mm"] == pytest.approx(0.0018653125442191958, rel=1e-12)
    assert pkg["targets_mm"] == [pytest.approx(0.0018703125442191958, rel=1e-12)]
    assert pkg["max_outer"] == 200
    assert pkg["max_phase"] == 20
    assert pkg["substep_size_mm"] == pytest.approx(5.0e-06, rel=1e-9)


def test_r8_checkpoint_lineage_from_authentic_r6():
    r6_cp = R6_DIR / "converged_checkpoint_01.json"
    r8_cp = R8_DIR / "initial_checkpoint_01.json"

    assert r6_cp.is_file(), f"Missing R6 checkpoint: {r6_cp}"
    assert r8_cp.is_file(), f"Missing R8 initial checkpoint: {r8_cp}"

    with open(r6_cp, "r", encoding="utf-8") as f:
        c6 = json.load(f)
    with open(r8_cp, "r", encoding="utf-8") as f:
        c8 = json.load(f)

    assert c6["target_uy_mm"] == pytest.approx(0.0018653125442191958, rel=1e-12)
    assert c6["target_uy_mm"] == c8["target_uy_mm"]
    assert c6["coupled_convergence"] is True

    # Exact field counts
    assert len(c8["displacement"]) == 7265
    assert len(c8["damage"]) == 7265
    assert len(c8["history"]) == 28224

    # Bitwise match on initial checkpoint file
    assert sha256_file(r8_cp) == sha256_file(r6_cp)


def test_r8_frozen_uel_integrity():
    uel_file = R8_DIR / "f42_mixed_uel.for"
    assert uel_file.is_file(), "Missing UEL source in R8"
    assert sha256_file(uel_file) == FROZEN_UEL_SHA


def test_r8_deck_and_initial_condition_completeness():
    assert (R8_DIR / "initial_conditions_solution.inc").is_file()
    assert (R8_DIR / "nodal_displacements_initial.csv").is_file()
    assert (R8_DIR / "nodal_phase_field_initial.csv").is_file()
    assert (R8_DIR / "d_lower_bounds.csv").is_file()
    assert (R8_DIR / "active_set_boundary_cards.inc").is_file()
    assert (R8_DIR / "P157_MECHANICAL_DC.inp").is_file()
    assert (R8_DIR / "P157_PHASE_DC.inp").is_file()
    assert (R8_DIR / "submit_M1_C4_P157_C1_2_R8.pbs").is_file()
    assert (R8_DIR / "submit_M1_C4_P157_R8_DC.pbs").is_file()
    assert (R8_DIR / "EXECUTION_MANIFEST.json").is_file()
    assert (R8_DIR / "QUALIFICATION_EXECUTION_MANIFEST.json").is_file()


def test_r8_gate_separation_discovery_vs_submission():
    """Verify decoupling: discovery of C4 reference gap vs submission gate."""
    # Discovery: R8 is needed to provide exact uy = 0.001870312544 mm reference
    target_uy = 0.0018703125442191958

    # Check that neither R6 nor R7 produced this exact reference
    r6_cp = R6_DIR / "converged_checkpoint_01.json"
    with open(r6_cp, "r", encoding="utf-8") as f:
        c6 = json.load(f)
    assert c6["target_uy_mm"] < target_uy  # R6 stopped at 0.00186531 mm

    # Execution gate check: R8 execution requires compute-node datacheck before live run
    qual_manifest_path = R8_DIR / "QUALIFICATION_EXECUTION_MANIFEST.json"
    with open(qual_manifest_path, "r", encoding="utf-8") as f:
        qual = json.load(f)
    assert qual["jobs"][0]["id"] == "M1_C4_P157_R8_DC"
    assert qual["jobs"][0]["walltime_hours"] == 1
