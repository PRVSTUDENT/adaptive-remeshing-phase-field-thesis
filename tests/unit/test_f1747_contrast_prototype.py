# -*- coding: utf-8 -*-
"""
tests/unit/test_f1747_contrast_prototype.py

Validates Task F1747 Case 3 Geometry-Independent Nonlinear Contrast Transformation:
  1. Statistical parameter selection derivation (tau = median + IQR).
  2. Background noise suppression (>= 75% elements mapped to zero error).
  3. Preservation of dual-corridor active fracture process zones.
  4. Bounded element count prediction (10k - 25k elements).
  5. Bitwise preservation of frozen UEL f42_mixed_uel.for (CE8D5EDC...).
  6. Zero-PBS governance adherence (0 new jobs consumed, cumulative preserved at 25).
"""

import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def test_f1747_frozen_uel_integrity():
    """Verify bitwise preservation of f42_mixed_uel.for."""
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.exists(uel_path), "Frozen UEL source missing: %s" % uel_path
    with open(uel_path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest().upper()
    assert digest == FROZEN_UEL_SHA256, "UEL hash mismatch: got %s" % digest

def test_f1747_parameter_derivation_provenance():
    """Verify objective statistical derivation of tau, gamma, and scale."""
    summary_path = os.path.join(REPO_ROOT, "results", "validation", "f1747_contrast_prototype_summary.json")
    assert os.path.exists(summary_path), "Summary JSON missing: %s" % summary_path
    with open(summary_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    base = data["global_envelope_baseline"]
    proto = data["selected_prototype"]
    
    # Check baseline stats
    expected_tau = base["median"] + base["iqr"]
    assert abs(proto["tau"] - expected_tau) < 1e-5, (
        "tau derivation mismatch: got %.6f, expected %.6f" % (proto["tau"], expected_tau)
    )
    assert proto["gamma"] == 1.5, "gamma mismatch: expected 1.5, got %s" % proto["gamma"]
    assert proto["scale"] > 0.0, "scale must be positive"

def test_f1747_background_suppression():
    """Verify that Candidate B suppresses >= 75% of elements to strictly zero error."""
    map_path = os.path.join(REPO_ROOT, "results", "validation", "f1747_transformed_envelope_map.json")
    assert os.path.exists(map_path), "Transformed envelope map missing"
    with open(map_path, "r", encoding="utf-8-sig") as f:
        map_data = json.load(f)
    
    stats = map_data["global_statistics"]
    assert stats["total_elements"] == 3923, "Total elements mismatch"
    assert stats["suppression_percentage"] >= 75.0, (
        "Suppression percentage < 75%%: %.2f%%" % stats["suppression_percentage"]
    )
    assert stats["suppressed_to_zero_count"] == 3101, (
        "Suppressed count mismatch: got %d, expected 3101" % stats["suppressed_to_zero_count"]
    )
    assert stats["active_count"] == 822, "Active count mismatch"

def test_f1747_corridor_activation_and_sizing_prediction():
    """Verify active coverage in both corridors and bounded element count prediction."""
    summary_path = os.path.join(REPO_ROOT, "results", "validation", "f1747_contrast_prototype_summary.json")
    with open(summary_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    proto = data["selected_prototype"]
    assert proto["primary_corridor_active_pct"] >= 60.0, "Primary corridor active % < 60%"
    assert proto["secondary_corridor_active_pct"] >= 60.0, "Secondary corridor active % < 60%"
    
    # Predicted element count bounded between 10k and 25k (down from 120k!)
    n_pred = proto["predicted_total_elements"]
    assert 10000 <= n_pred <= 25000, "Predicted total elements %d outside [10k, 25k]" % n_pred

def test_f1747_zero_pbs_governance():
    """Verify 0 new PBS jobs consumed and cumulative historical accounting preserved."""
    active_task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(active_task_path, "r", encoding="utf-8-sig") as f:
        task = json.load(f)
    
    assert task["task_id"] == "F1747-CASE3-CONTRAST-TRANSFORMATION-PROTOTYPE"
    assert task["max_new_pbs_submissions"] == 0, "max_new_pbs_submissions > 0"
    assert task["submissions_consumed"] == 0, "Non-zero submissions consumed"
    assert task["cumulative_pbs_submissions"] == 25, "Cumulative PBS submissions != 25"
