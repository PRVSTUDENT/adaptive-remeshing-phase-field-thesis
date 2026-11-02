# -*- coding: utf-8 -*-
"""
test_turn19_preparation.py
Unit tests for Turn 19 research preparation artifact:
C4 same-load reference validation and preservation.
"""

import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PREPARATION_ARTIFACT = REPO_ROOT / "results/validation/preparation-a7f33358-1694-4ddb-9c8c-18dcea562643.json"


def test_turn19_preparation_artifact_exists():
    assert PREPARATION_ARTIFACT.exists(), "Preparation artifact does not exist on disk"


def test_turn19_preparation_artifact_schema():
    data = json.loads(PREPARATION_ARTIFACT.read_text(encoding="utf-8"))
    assert data.get("schema") == 1
    assert data.get("status") == "PREPARATION_COMPLETE"
    assert data.get("verification_passed") is True
    assert len(data.get("finding", "").strip()) >= 20
    assert data.get("operation") == "research_preparation"


def test_turn19_reference_parity_benchmarks():
    data = json.loads(PREPARATION_ARTIFACT.read_text(encoding="utf-8"))
    ref = data["reference_validation"]
    assert ref["source_experiment"] == "Package 157 Revision 6"
    assert ref["pbs_job_id"] == "1419359.mmaster02"
    assert ref["target_displacement_mm"] == pytest.approx(0.0018653125442191958, abs=1e-12)
    assert ref["reaction_force_kN"] == pytest.approx(0.18346779247291461, abs=1e-9)
    assert ref["total_raw_energy_kNmm"] == pytest.approx(0.00022511363524288855, abs=1e-12)
    assert ref["healing_violations"] == 0
    assert ref["history_monotonicity_violations"] == 0


def test_turn19_evidence_sources_hashes():
    data = json.loads(PREPARATION_ARTIFACT.read_text(encoding="utf-8"))
    sources = data.get("evidence_sources", {})
    assert len(sources) >= 5
    for rel_path, expected_hash in sources.items():
        full_path = REPO_ROOT / rel_path
        assert full_path.exists(), "Evidence file does not exist: %s" % rel_path
        computed = hashlib.sha256(full_path.read_bytes()).hexdigest().upper()
        assert computed == expected_hash, "Hash mismatch for %s: %s vs %s" % (rel_path, computed, expected_hash)
