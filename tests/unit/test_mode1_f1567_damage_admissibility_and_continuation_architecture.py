#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Task F1567:
- Physical damage admissibility resolution (d <= 1.000000 strictly enforced).
- Local donor overshoot infeasibility audit (1.0 >= d_R >= d_D > 1.0 resolved via min(1.0, d_D)).
- Candidate 2A conservation pass (all 4 scalar criteria pass, 0 physical nodal deficits).
- Geometry-consistent projection formulation (intersection constraints).
- Kinematic-offset continuation architecture and commercial Abaqus static step barriers.
- Binding governance invariants.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DAMAGE_AUDIT_PATH = (
    REPO_ROOT
    / "runs"
    / "hpc"
    / "mode1_stage_c1_2_cycle5_continuation"
    / "F1567_DAMAGE_BOUND_AUDIT.json"
)

CANDIDATE2A_PATH = (
    REPO_ROOT
    / "runs"
    / "hpc"
    / "mode1_stage_c1_2_cycle5_continuation"
    / "F1567_CANDIDATE2A_ADMISSIBLE_REVALIDATION.json"
)

GEOM_PROJ_PATH = (
    REPO_ROOT
    / "runs"
    / "hpc"
    / "mode1_stage_c1_2_cycle5_continuation"
    / "F1567_GEOMETRY_CONSISTENT_PROJECTION_AUDIT.json"
)

DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
)


def test_f1567_donor_overshoot_audit():
    """Verify quantitative forensic audit of donor overshoot points."""
    assert DAMAGE_AUDIT_PATH.exists(), f"Missing audit at {DAMAGE_AUDIT_PATH}"
    with open(DAMAGE_AUDIT_PATH, "r", encoding="utf-8") as f:
        audit = json.load(f)

    # 1. Authentic donor integration points (SDV14)
    assert audit["donor_gp_overshoot_count"] == 9
    assert audit["donor_gp_overshoot_max"] > 1.0008
    assert audit["donor_gp_overshoot_max"] < 1.0010

    # 2. Reconstructed donor nodal values (LSQR)
    assert audit["donor_nodal_overshoot_count"] == 47
    assert audit["donor_nodal_overshoot_max"] > 1.0080
    assert audit["donor_nodal_overshoot_max"] < 1.0090

    # 3. Recipient interpolated nodes
    assert audit["recipient_interp_overshoot_count"] == 14
    assert audit["recipient_interp_overshoot_max"] > 1.0030
    assert audit["recipient_interp_overshoot_max"] < 1.0040


def test_f1567_candidate2a_admissibility_and_conservation():
    """Verify Candidate 2A strictly enforces d <= 1.0 and passes all 4 scalar conservation criteria."""
    assert CANDIDATE2A_PATH.exists(), f"Missing Candidate 2A summary at {CANDIDATE2A_PATH}"
    with open(CANDIDATE2A_PATH, "r", encoding="utf-8") as f:
        c2a = json.load(f)

    # Physical damage admissibility
    assert c2a["d_max_recip"] <= 1.00000001, f"Damage bound violated: d_max = {c2a['d_max_recip']}"
    assert c2a["admissibility_status"] == "PASS_PHYSICAL_BOUNDS_STRICTLY_ENFORCED"

    # All 4 scalar conservation criteria PASS
    assert abs(c2a["delta_RF2_N"]) <= 5.0, f"RF2 failed: {c2a['delta_RF2_N']}"
    assert abs(c2a["delta_elas_pct"]) <= 0.50, f"Elastic energy failed: {c2a['delta_elas_pct']}%"
    assert abs(c2a["delta_frac_pct"]) <= 0.50, f"Fracture energy failed: {c2a['delta_frac_pct']}%"
    assert abs(c2a["delta_tot_pct"]) <= 0.10, f"Total energy failed: {c2a['delta_tot_pct']}%"
    assert c2a["scalar_conservation_status"]["all_conservation_pass"] is True

    # Nodal irreversibility vs physical bound min(1.0, d_D) has ZERO violations
    assert c2a["nodal_violations_phys_count"] == 0
    assert c2a["max_nodal_deficit_phys"] < 1e-6

    # Retained local donor overshoot infeasibility exactly matches 14 points
    assert c2a["nodal_violations_raw_overshoot_count"] == 14
    assert c2a["max_nodal_deficit_raw"] < 0.0035


def test_f1567_geometry_consistent_projection():
    """Verify geometry-consistent projection study evaluating trade-offs."""
    if not GEOM_PROJ_PATH.exists():
        pytest.skip(f"Awaiting geometry-consistent projection audit at {GEOM_PROJ_PATH}")
    with open(GEOM_PROJ_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "penalty_study" in data
    assert len(data["penalty_study"]) > 0


def test_f1567_continuation_architecture_and_governance():
    """Verify continuation architecture documentation and strict governance invariants."""
    assert DOC_PATH.exists(), f"Missing doc at {DOC_PATH}"
    with open(DOC_PATH, "r", encoding="utf-8") as f:
        doc = f.read()

    # Continuation architecture concepts documented
    assert "Kinematic-Offset" in doc or "kinematic-offset" in doc
    assert "Error 144" in doc or "DISPLACEMENT" in doc
    assert "W_{\\text{ext}}" in doc or "1.69" in doc

    # Governance checks
    session_path = REPO_ROOT / "project_coordination" / "ACTIVE_SESSION.json"
    assert session_path.exists()
    with open(session_path, "r", encoding="utf-8") as f:
        sess = json.load(f)
    assert sess["task_id"].startswith("F156")
