"""
tests/unit/test_f1720_stage3_coarse_coupled_miseseri.py
======================================================
Unit tests for Task F1720 Stage 3: Native Abaqus MISESERI Qualification
on the Five-Hole Coarse Plate with Direct UEL-UMAT Coupling.
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EVAL_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1720_native_miseseri_evaluation.json")
COARSE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled")
COARSE_ODB = os.path.join(COARSE_DIR, "PK_F1720_COARSE_COUPLED.odb")


@pytest.fixture(scope="module")
def eval_data():
    assert os.path.exists(EVAL_JSON), f"Evaluation JSON missing: {EVAL_JSON}"
    with open(EVAL_JSON, "r") as f:
        return json.load(f)


def test_coarse_coupled_odb_exists():
    """Verify that the solved coarse coupled ODB exists and has non-zero size."""
    assert os.path.exists(COARSE_ODB), f"Coupled ODB missing: {COARSE_ODB}"
    assert os.path.getsize(COARSE_ODB) > 1024 * 1024, "Coupled ODB size too small (< 1 MB)"


def test_evaluation_element_count(eval_data):
    """Verify that all 2,747 physical elements were evaluated."""
    assert eval_data["num_elements"] == 2747, f"Expected 2747 elements, got {eval_data['num_elements']}"


def test_miseseri_and_misesavg_population(eval_data):
    """Verify that native MISESERI and MISESAVG are populated with non-zero positive values."""
    stats_eri = eval_data["miseseri_stats"]
    stats_avg = eval_data["misesavg_stats"]

    assert stats_eri["max"] > 0.0, "MISESERI max must be positive"
    assert stats_eri["min"] > 0.0, "MISESERI min must be positive"
    assert stats_eri["mean"] > 0.0, "MISESERI mean must be positive"

    assert stats_avg["max"] > 0.0, "MISESAVG max must be positive"
    assert stats_avg["min"] > 0.0, "MISESAVG min must be positive"
    assert stats_avg["mean"] > 0.0, "MISESAVG mean must be positive"


def test_relative_error_eta_distribution(eval_data):
    """Verify that relative error eta has a reasonable physical distribution."""
    eta_stats = eval_data["eta_stats"]
    # Mean relative error should be around 3-4% matching target refinement band
    assert 2.0 < eta_stats["mean_pct"] < 6.0, f"Unexpected mean eta: {eta_stats['mean_pct']}%"
    assert eta_stats["max_pct"] > 50.0, "Peak eta in localized region must exceed 50%"


def test_pearson_correlation_vs_f1719(eval_data):
    """
    CRITICAL ACCEPTANCE GATE:
    Verify that native direct-coupled MISESERI correlates with the F1719 companion
    reconstruction with Pearson r > 0.95.
    """
    r = eval_data.get("pearson_correlation_vs_f1719")
    assert r is not None, "Pearson correlation not computed"
    assert r > 0.95, f"Pearson correlation r={r:.6f} below required threshold 0.95"
    assert r > 0.97, f"Pearson correlation r={r:.6f} passes acceptance gate"


def test_peak_elements_localization(eval_data):
    """Verify that peak raw MISESERI elements are in the high-stress stress concentration zones."""
    top_eri = eval_data.get("top_5_eri_elements", [])
    assert len(top_eri) == 5, "Expected top 5 elements"
    # Element 4 is the top element
    top_elem_id = top_eri[0]["phys_idx"]
    assert top_elem_id == 4, f"Expected top element 4, got {top_elem_id}"
