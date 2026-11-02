# -*- coding: utf-8 -*-
"""
test_c2_2_integration_readiness.py
Unit tests for Mode-I Method C Stage C2-2 Bounded Integration-Readiness Audit.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.check_c2_2_integration_readiness import perform_integration_readiness_audit

AUDIT_PATH = REPO_ROOT / "results/validation/c2_2_integration_readiness_audit.json"


def test_integration_readiness_audit_artifact_exists():
    assert AUDIT_PATH.exists(), "Audit artifact must exist on disk"
    data = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    assert data["audit_name"] == "STAGE_C2_2_INTEGRATION_READINESS_AUDIT"
    assert data["task"] == "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE"


def test_independent_components_all_pass():
    data = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    assert data["independent_components_verified_all_pass"] is True
    comps = data["audit_components"]

    # Mesh integrity
    assert comps["c5_mesh_integrity"]["status"] == "PASS"
    assert comps["c5_mesh_integrity"]["elements"] == 12996
    assert comps["c5_mesh_integrity"]["nodes"] == 13278

    # Frozen UEL
    assert comps["frozen_production_uel"]["status"] == "PASS"
    assert comps["frozen_production_uel"]["bitwise_identical"] is True
    assert comps["frozen_production_uel"]["canonical_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

    # Notification script
    assert comps["notification_script"]["status"] == "PASS"

    # Builder and predecessor guard
    assert comps["builder_and_predecessor_guard"]["status"] == "PASS"
    assert comps["builder_and_predecessor_guard"]["guard_enforces_no_submission"] is True

    # Driver specification
    assert comps["driver_specification"]["status"] == "PASS"
    assert comps["driver_specification"]["tolerances_match_method_c"] is True

    # Submission adapter gates
    assert comps["submission_adapter_gates"]["status"] == "PASS"
    assert comps["submission_adapter_gates"]["submission_prevented"] is True
    assert "GATE_1_PREDECESSOR_CHECKPOINT_02" in comps["submission_adapter_gates"]["blocking_gates"]
    assert "GATE_8_INDEPENDENT_C4_REFERENCE" in comps["submission_adapter_gates"]["blocking_gates"]


def test_dual_unresolved_dependencies_isolated():
    data = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    assert data["submission_allowed"] is False
    deps = data["unresolved_dependencies"]
    assert len(deps) == 2
    dep_r3 = deps[0]
    assert dep_r3["dependency"] == "PREDECESSOR_CHECKPOINT_02"
    assert dep_r3["source_job"] == "1419499.mmaster02"
    assert dep_r3["status"] == "PENDING_RUNNING_SOLVER"
    assert dep_r3["physical_acceptance_required"] is True

    dep_r8 = deps[1]
    assert dep_r8["dependency"] == "INDEPENDENT_C4_REFERENCE"
    assert dep_r8["source_job"] == "1419490.mmaster02"
    assert dep_r8["status"] == "PENDING_RUNNING_SOLVER"
    assert dep_r8["physical_acceptance_required"] is True

