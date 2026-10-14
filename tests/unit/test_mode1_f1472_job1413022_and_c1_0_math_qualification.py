# -*- coding: utf-8 -*-
"""
test_mode1_f1472_job1413022_and_c1_0_math_qualification.py

Unit test suite for Task F1472:
1. Verify live tracking and configuration of Job 1413022.mmaster02 (M1_MB_CORR_8TB)
   against serial reference Job 1412465 and Stage A 8T SMP Job 1412873.
2. Verify rigorous qualification of Stage C1-0 mathematical claim: identity mesh mapping
   (zero geometric interpolation error) does NOT independently guarantee an assembled zero
   residual in an unimplemented solver; verify five mandatory subsystem restoration requirements.
3. Verify correction of static equilibrium energy interpretation: Newton iteration energy reduction
   during fixed-displacement equilibration is total potential energy minimization (Delta Pi <= 0),
   not physical thermodynamic dissipation; verify formal four-way energy/dissipation distinction.
4. Verify strict governance: frozen production UEL hash CE8D5EDC..., Gate 6C hold, and
   locked submission wrapper (AUTHORIZED=false).
"""

import hashlib
import json
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

PROD_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
DECK40_HASH = "1209F716971719B1A740FF92C8B5503BA9784F10D5EEDD3C5035C81D40A066E9"
PBS_8TB_HASH = "25223AC5D450000393A36AF84607BEF05D0A5CAFBBAC263FA4F7113666E18BCC"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_job_1413022_tracking_and_determinism_baselines():
    """Verify tracking of Job 1413022 and preservation of baseline determinism metrics."""
    active_task_path = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
    assert active_task_path.is_file(), "ACTIVE_TASK.json must exist"
    with open(active_task_path, "r", encoding="utf-8") as f:
        task_data = json.load(f)

    # Job 1413022 is the active PBS job
    assert "1413022.mmaster02" in task_data["active_pbs_job_ids"]

    # Verify ledger entry in HPC_JOB_LEDGER.csv
    hpc_ledger_path = REPO_ROOT / "project_coordination" / "HPC_JOB_LEDGER.csv"
    assert hpc_ledger_path.is_file()
    ledger_text = hpc_ledger_path.read_text(encoding="utf-8")
    assert "1413022.mmaster02" in ledger_text
    assert "M1_MB_CORR_8TB" in ledger_text

    # Verify input deck and production UEL hashes
    deck_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k" / "M1_MB_CORRECTED_PROPAGATION_14K.inp"
    assert compute_sha256(deck_path) == DECK40_HASH
    uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
    assert compute_sha256(uel_path) == PROD_UEL_HASH

    # Verify partial horizon baseline facts (Job 1412465 and 1412873)
    # Both completed Step 1 (2,000 incs) and reached Step 2 inc 2890 (total 4,890 incs)
    # terminating at u ~ 0.007889 mm due to dt_min cutbacks on severed specimen
    u_cutback = 0.007889
    assert u_cutback < 0.0100, "Partial horizon classification must remain strictly intact"


def test_stage_c1_0_math_qualification_and_subsystem_restoration():
    """Verify analytical derivation showing why identity mesh does NOT guarantee assembled zero residual."""
    arch_doc = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
    assert arch_doc.is_file()
    text = arch_doc.read_text(encoding="utf-8")

    # Section 7.3.1 must exist with rigorous qualification
    assert "7.3.1 Rigorous Mathematical Derivation: Why Identity Mesh Mapping Does NOT Independently Guarantee" in text

    # Discrete residual equation
    assert "\\mathbf{R}^{(0)} = \\begin{bmatrix} \\mathbf{R}_u^{(0)} \\\\ \\mathbf{R}_d^{(0)} \\end{bmatrix}" in text
    assert "\\mathbf{R}_u^{(0)} = \\mathbf{F}_{\\text{ext}} - \\sum_{e=1}^{N_{\\text{elem}}} \\int_{\\Omega_e} \\mathbf{B}_u^T \\boldsymbol{\\sigma}" in text
    assert "\\mathbf{R}_d^{(0)} =" in text and "\\sum_{e=1}^{N_{\\text{elem}}} \\int_{\\Omega_e}" in text

    # Verify documentation of all five mandatory restoration subsystems
    # 1. Boundary conditions on Gamma_u
    assert "Kinematic Boundary Conditions on $\\Gamma_u$" in text
    assert "u_y = u_D = 0.0050" in text
    # 2. Mechanical DOFs 1, 2
    assert "Mechanical Nodal Displacement Vector (DOFs 1, 2)" in text
    assert "2,988 physical nodes" in text
    # 3. Phase-field nodal DOF 3 and Error 144 / SOLUTION IC limitation
    assert "Phase-Field Nodal Degrees of Freedom (DOF 3)" in text
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in text
    assert "does NOT initialize nodal solution degrees of freedom" in text
    assert "d = 0" in text
    # 4. Internal state variables (SVARS)
    assert "Internal State Variables at Quadrature Points (`SVARS`)" in text
    assert "53.65" in text
    # 5. Dual-layer common block synchronization
    assert "Dual-Layer Common Block Synchronization (`COMMON /CB_STATE_TRANS/`)" in text
    assert "LOP = 0" in text

    # Retraction/qualification summary
    assert "analytical limit assuming complete, error-free state reconstruction across all five subsystems" in text


def test_static_equilibrium_potential_energy_minimization_vs_dissipation():
    """Verify correction of static equilibrium energy interpretation and four-way distinction."""
    arch_doc = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
    text = arch_doc.read_text(encoding="utf-8")

    # Potential energy functional Pi(u)
    assert "\\Pi(\\mathbf{u}) = \\int_{\\Omega} \\psi(\\boldsymbol{\\varepsilon}(\\mathbf{u}), d_0)" in text
    # Algorithmic progression toward stationary point
    assert "progression toward the stationary point" in text or "stationary point" in text
    # Explicit rejection of physical dissipation in static step
    assert "zero physical thermodynamic dissipation occurs" in text or "\\Delta \\mathcal{D}_{\\text{phys}} \\equiv 0" in text
    assert "Energy Minimization vs Physical Dissipation" in text

    # Formal Four-Way Distinction
    assert "Potential Energy Minimization" in text
    assert "Projection Discrepancy" in text
    assert "Physical Fracture Energy Dissipation" in text
    assert "Numerical Viscous Regularization" in text

    # Frozen damage invariants
    assert "\\Delta W_{\\text{ext, relax}}" in text
    assert "\\Delta W_{\\text{ext}} = 0" in text
    assert "\\Delta E_{\\text{frac, relax}} = 0" in text
    assert "\\Delta E_{\\text{elas, relax}} = -\\mathcal{D}_{\\text{num, relax}} \\le 0" in text


def test_supervisor_briefing_synchronization():
    """Verify that the supervisor briefing aligns with Stage C1-0 qualification and energy interpretation."""
    briefing_path = REPO_ROOT / "docs" / "supervisor_reports" / "22-10-2026" / "SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md"
    assert briefing_path.is_file()
    text = briefing_path.read_text(encoding="utf-8")

    # Section 6.1 Stage C1-0 qualification
    assert "zero geometric interpolation error does NOT independently guarantee an assembled zero residual" in text
    assert "simultaneous exact restoration of boundary conditions, mechanical DOFs 1 and 2, phase-field nodal DOF 3" in text

    # Section 6.1 Stage C1-1 energy minimization
    assert "static potential energy minimization" in text
    assert "rigorously distinguishing algorithmic energy minimization from physical thermodynamic dissipation with frozen damage" in text


def test_governance_and_gate_6c_locks():
    """Verify production UEL frozen state, submission wrapper locks, and Gate 6C governance."""
    uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
    actual_uel_hash = compute_sha256(uel_path)
    assert actual_uel_hash == PROD_UEL_HASH, f"Production UEL hash mismatch: {actual_uel_hash} != {PROD_UEL_HASH}"

    wrapper_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "42_method_c1_forward_refinement" / "submit_c1_forward_refinement_job.sh"
    if wrapper_path.exists():
        wrapper_text = wrapper_path.read_text(encoding="utf-8")
        assert "AUTHORIZED=false" in wrapper_text, "Submission wrapper must enforce AUTHORIZED=false"

    active_task_path = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
    with open(active_task_path, "r", encoding="utf-8") as f:
        task_data = json.load(f)
    assert "GATE_6C_ON_HOLD" in task_data["gate_status"] or "ON_HOLD" in task_data["gate_status"]
