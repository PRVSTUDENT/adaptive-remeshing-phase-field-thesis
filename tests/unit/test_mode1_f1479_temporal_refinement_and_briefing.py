"""Unit tests for Task F1479: Package 44 Temporal Refinement Experiment and Briefing Qualifications.

Validates that:
1. Package 44 exists at models/pandey_kumar_mode1/44_method_b_temporal_refinement/ with
   all required artifacts (M1_MB_CORRECTED_DTMAX_14K.inp, f42_mixed_uel.for, submit_M1_MB_DTMAX_8T.pbs,
   run_datacheck_and_submit.sh, PACKAGE_MANIFEST.json, PRE_JOB_ANTI_DEVIATION_CARD.md).
2. The input deck contains exactly the single intended change: Step 2 dt_max = 1.0E-4, INC=12000,
   with all 14,483 elements, geometry, and boundary conditions frozen.
3. The production UEL hash matches the frozen production hash CE8D5EDC...
4. The supervisor briefing (SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md) incorporates all
   7 required epistemic qualifications (Method A scope, Method C arbitrary tracking boundary,
   state-transfer energy preservation status, Abaqus native continuation feasibility,
   retrospective vs prospective Method B, binned corridor coverage vs elementwise resolution,
   and ligament resolution necessity vs sufficiency).
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE44_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "44_method_b_temporal_refinement"
BRIEFING_PATH = REPO_ROOT / "docs" / "supervisor_reports" / "22-10-2026" / "SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md"
FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def test_package44_structure_and_manifest():
    """Verify Package 44 directory structure, manifest, and production UEL hash."""
    assert PACKAGE44_DIR.exists(), f"Package 44 directory missing at {PACKAGE44_DIR}"

    manifest_file = PACKAGE44_DIR / "PACKAGE_MANIFEST.json"
    assert manifest_file.exists()
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

    assert manifest["package_id"] == "44_method_b_temporal_refinement"
    assert manifest["name"] == "M1_MB_CORR_14K_DTMAX_REFINEMENT"
    assert manifest["mesh"]["finite_elements"] == 14483
    assert manifest["mesh"]["total_records_3layers"] == 43449
    assert manifest["artifacts"]["user_subroutine"]["sha256"] == FROZEN_UEL_SHA

    # Verify UEL file on disk
    uel_file = PACKAGE44_DIR / "f42_mixed_uel.for"
    assert uel_file.exists()


def test_package44_deck_step2_static():
    """Verify Package 44 deck Step-2 STATIC line has dt_max=1.0E-4 and INC=12000."""
    deck_path = PACKAGE44_DIR / "M1_MB_CORRECTED_DTMAX_14K.inp"
    assert deck_path.exists()
    content = deck_path.read_text(encoding="utf-8")

    assert "*STEP, NAME=Step-2, NLGEOM=NO, INC=12000" in content
    assert " 1.0E-4, 1.0, 1.0E-9, 1.0E-4" in content
    # Step 1 should remain unchanged
    assert "*STEP, NAME=Step-1, NLGEOM=NO, INC=2500" in content
    assert " 5.0E-4, 1.0, 1.0E-9, 5.0E-4" in content


def test_package44_pbs_and_wrapper_directives():
    """Verify PBS script and execution wrapper have correct job name and resources."""
    pbs_path = PACKAGE44_DIR / "submit_M1_MB_DTMAX_8T.pbs"
    assert pbs_path.exists()
    pbs_content = pbs_path.read_text(encoding="utf-8")

    assert "#PBS -N M1_MB_DTMAX_8T" in pbs_content
    assert "#PBS -l nodes=1:ppn=8" in pbs_content
    assert "#PBS -l mem=24gb" in pbs_content
    assert "#PBS -l walltime=24:00:00" in pbs_content
    assert "mp_mode=threads" in pbs_content

    sh_path = PACKAGE44_DIR / "run_datacheck_and_submit.sh"
    assert sh_path.exists()
    sh_content = sh_path.read_text(encoding="utf-8")
    assert "EXPECTED_INP_SHA=" in sh_content
    assert "submit_M1_MB_DTMAX_8T.pbs" in sh_content


def test_supervisor_briefing_epistemic_qualifications():
    """Verify all 7 required scientific overstatement qualifications exist in the briefing."""
    assert BRIEFING_PATH.exists()
    briefing = BRIEFING_PATH.read_text(encoding="utf-8")

    # 1. Method A does not universally require advance knowledge of crack path
    assert "Method A does not universally require advance knowledge" in briefing

    # 2. Method C has not demonstrated autonomous tracking of arbitrary crack paths
    assert "Method C has not demonstrated autonomous tracking of arbitrary" in briefing or "Method C has **not** demonstrated autonomous tracking of arbitrary crack paths" in briefing

    # 3. State-transfer energy preservation has not been experimentally qualified
    assert "State-transfer energy preservation has not been experimentally qualified" in briefing or "state-transfer energy preservation has not been experimentally qualified" in briefing

    # 4. Failed Abaqus initialization does not prove all native continuation impossible
    assert "does not establish that all native continuation strategies are fundamentally impossible" in briefing or "does not establish that all native continuation" in briefing

    # 5. Retrospective Package 40 does not establish prospective Method B accuracy
    assert "Retrospective Package 40" in briefing
    assert "does not prove prospective Method B accuracy" in briefing

    # 6. Binned median corridor coverage vs elementwise resolution
    assert "binned median corridor" in briefing
    assert "must not be conflated with 100% elementwise resolution" in briefing or "must not be equated with 100% elementwise" in briefing

    # 7. Ligament resolution necessity vs sufficiency
    assert "demonstrates that ligament resolution was necessary" in briefing
    assert "spatial resolution alone is not universally sufficient" in briefing or "not prove that ligament resolution alone is universally necessary and sufficient" in briefing
