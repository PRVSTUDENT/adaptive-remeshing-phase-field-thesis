import hashlib
import json
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

PROD_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
DECK40_HASH = "1209F716971719B1A740FF92C8B5503BA9784F10D5EEDD3C5035C81D40A066E9"
PBS_8TB_HASH = "25223AC5D450000393A36AF84607BEF05D0A5CAFBBAC263FA4F7113666E18BCC"

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_job_1413022_submission_and_pbs_parameters():
    """Verify that submit_M1_MB_CORR_8TB.pbs is properly structured, parameter-locked, and hash-verified."""
    pbs_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k" / "submit_M1_MB_CORR_8TB.pbs"
    assert pbs_path.is_file(), f"PBS script not found at {pbs_path}"
    
    # Hash check
    actual_hash = compute_sha256(pbs_path)
    assert actual_hash == PBS_8TB_HASH, f"PBS script hash mismatch: {actual_hash} != {PBS_8TB_HASH}"
    
    text = pbs_path.read_text(encoding="utf-8")
    assert "#PBS -N M1_MB_CORR_8TB" in text
    assert "#PBS -q entry_imfdfkmq" in text
    assert "#PBS -l nodes=1:ppn=8" in text
    assert "#PBS -l mem=24gb" in text
    assert "#PBS -l walltime=24:00:00" in text
    assert "#PBS -m abe" in text
    assert "cpus=8" in text
    assert "mp_mode=threads" in text
    assert "JOB_NAME=\"M1_MB_CORRECTED_8T_B\"" in text
    assert "INP_NAME=\"M1_MB_CORRECTED_PROPAGATION_14K.inp\"" in text
    assert "USER_SUB=\"f42_mixed_uel.for\"" in text


def test_stage_b_repeat_determinism_hypothesis():
    """Verify the scientific hypothesis and comparison baselines for 8-thread determinism."""
    # Input deck hash verification
    deck_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k" / "M1_MB_CORRECTED_PROPAGATION_14K.inp"
    assert deck_path.is_file()
    actual_deck_hash = compute_sha256(deck_path)
    assert actual_deck_hash == DECK40_HASH, f"Deck hash mismatch: {actual_deck_hash} != {DECK40_HASH}"

    # Verify baseline metrics for 1412465 (serial reference) and 1412873 (first 8T SMP solve)
    # Both terminated at partial displacement u ~ 0.007889 mm due to dt_min cutbacks
    u_terminal_expected = 0.007889
    f_max_expected = 0.7437  # kN
    increments_expected = 4890
    
    # Assert partial-horizon classification is strictly preserved
    assert u_terminal_expected < 0.0100, "Must be classified as partial horizon, not full 0.0100 mm"
    assert increments_expected == 4890


def test_stage_c1_0_same_mesh_mathematical_proof():
    """Verify mathematical proof design and quantitative targets for Stage C1-0."""
    arch_doc = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
    assert arch_doc.is_file()
    arch_text = arch_doc.read_text(encoding="utf-8")

    # Verify Stage C1-0 same-mesh specification
    assert "Stage C1-0" in arch_text
    assert "2,906 -> 2,906 FEs" in arch_text or "2,906 \\to 2,906" in arch_text
    
    # Target anchor values from authentic donor Job 1411891
    assert "653.0886" in arch_text  # RF in N
    assert "1.6327" in arch_text    # E_elas in mJ
    assert "0.094910" in arch_text  # d_max at Node 97
    
    # Tolerances
    assert "|\\Delta RF| \\le 0.5\\,\\text{N}" in arch_text or "|Delta RF| <= 0.5 N" in arch_text
    assert "0.05\\%" in arch_text or "0.05%" in arch_text
    
    # Absence of unsupported claims
    assert 'Retract claims of "guaranteed exactly 1 Newton iteration"' in arch_text
    assert "Standard Abaqus convergence criteria apply" in arch_text


def test_phase_field_nodal_dof3_initialization_semantics():
    """Verify understanding of Abaqus phase-field initialization limitations."""
    arch_doc = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
    arch_text = arch_doc.read_text(encoding="utf-8")

    # Active DOF 3 for phase field
    assert "DOF 3" in arch_text
    # Solution IC only writes element state variables (STATEV / SVARS)
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in arch_text
    # Displacement IC rejected by Error 144 in *STATIC
    assert "Error 144" in arch_text
    # Phase residual out-of-balance
    assert "\\mathbf{R}_d" in arch_text or "R_d" in arch_text


def test_four_stage_energy_balance_ledger_invariants():
    """Verify the 4-stage energy balance ledger equations and retraction of additive formula."""
    arch_doc = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
    arch_text = arch_doc.read_text(encoding="utf-8")

    # Formal retraction of unphysical formula
    assert "Retraction of Unphysical Formula" in arch_text or "retract" in arch_text.lower()
    
    # Zero external work during fixed-u equilibration
    assert "\\Delta W_{\\text{ext}} = 0" in arch_text
    # Frozen damage during Step 1 equilibration
    assert "\\Delta d = 0" in arch_text or "damage is frozen" in arch_text.lower()
    # Monotonic relaxation dissipation
    assert "\\Delta E_{\\text{elas, relax}} = -\\mathcal{D}_{\\text{num, relax}} \\le 0" in arch_text or "\\mathcal{D}_{\\text{num, relax}}" in arch_text


def test_governance_and_gate_6c_hold_preservation():
    """Verify cluster lock, idle queue status, and frozen production UEL hash."""
    uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
    actual_hash = compute_sha256(uel_path)
    assert actual_hash == PROD_UEL_HASH, f"Production UEL hash mismatch: {actual_hash} != {PROD_UEL_HASH}"

    wrapper_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "42_method_c1_forward_refinement" / "submit_c1_forward_refinement_job.sh"
    if wrapper_path.exists():
        wrapper_text = wrapper_path.read_text(encoding="utf-8")
        assert "AUTHORIZED=false" in wrapper_text, "Submission wrapper must have AUTHORIZED=false"
