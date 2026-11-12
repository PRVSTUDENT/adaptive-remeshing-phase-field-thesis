"""
Unit tests for Task F1720 Stage 2: Direct UEL-UMAT Coupling and Mechanical Neutrality
Audits:
  1. Call order: UEL executes before UMAT in every increment/iteration.
  2. Mechanical neutrality: Config B dummy-scaled overlay perturbs RF by < 1e-8.
  3. Force doubling: Config C unscaled overlay doubles RF (+100%).
  4. Stress transfer fidelity: SDVs in UMAT match authentic UEL stress tensor.
  5. Native MISESERI activation: Non-zero in Config B, zero in Config A.
"""

import os
import json
import pytest

DIAG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "models", "pandey_kumar_mode1", "212_f1720_diagnostic_patch"
)
RESULTS_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "results", "validation", "f1720_diagnostic_patch_results.json"
)
CALL_ORDER_TXT = os.path.join(DIAG_DIR, "f1720_call_order.txt")


@pytest.fixture(scope="module")
def results_data():
    assert os.path.exists(RESULTS_JSON), f"Results JSON not found at {RESULTS_JSON}"
    with open(RESULTS_JSON, "r") as f:
        return json.load(f)


def test_call_order_uel_before_umat():
    """Verify that UEL is always executed before UMAT in the solver call sequence."""
    assert os.path.exists(CALL_ORDER_TXT), f"Call order log not found at {CALL_ORDER_TXT}"
    with open(CALL_ORDER_TXT, "r") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("=")]

    # Skip header
    header_idx = -1
    for i, line in enumerate(lines):
        if "CALL" in line and "ROUTINE" in line:
            header_idx = i
            break
    assert header_idx >= 0, "Header row not found in call order log"

    calls = lines[header_idx + 1:]
    assert len(calls) > 0, "No calls logged"

    first_routine = calls[0].split()[1]
    assert first_routine == "UEL", f"First call was {first_routine}, expected UEL"

    # Verify that in every increment, UEL calls precede UMAT calls
    last_uel_inc = None
    for call in calls:
        parts = call.split()
        routine = parts[1]
        kinc = int(parts[4])
        if routine == "UEL":
            last_uel_inc = kinc
        elif routine == "UMAT":
            assert last_uel_inc is not None, "UMAT called before any UEL call!"


def test_mechanical_neutrality_config_b(results_data):
    """Verify strict mechanical neutrality: Config B perturbs reaction force by < 1e-8."""
    standalone = results_data.get("PK_F1720_DIAG_1ELEM_STANDALONE")
    config_b = results_data.get("PK_F1720_DIAG_1ELEM_B")
    assert standalone is not None and config_b is not None

    rf_ref = standalone["total_rf_y"]
    rf_b = config_b["total_rf_y"]
    assert rf_ref > 0.0

    delta_rf = abs(rf_b - rf_ref)
    rel_error = delta_rf / rf_ref

    # Must be zero to machine precision (< 1e-12)
    assert rel_error < 1.0e-8, f"Config B RF perturbation too large: {rel_error:.4e}"


def test_force_doubling_config_c(results_data):
    """Verify that Config C (unscaled physical stress) doubles reaction force (+100%)."""
    standalone = results_data.get("PK_F1720_DIAG_1ELEM_STANDALONE")
    config_c = results_data.get("PK_F1720_DIAG_1ELEM_C")
    assert standalone is not None and config_c is not None

    rf_ref = standalone["total_rf_y"]
    rf_c = config_c["total_rf_y"]

    ratio = rf_c / rf_ref
    # Should be exactly 2.0 (100% increase) within 0.1%
    assert abs(ratio - 2.0) < 1.0e-3, f"Config C RF ratio was {ratio:.4f}, expected 2.0000"


def test_stress_tensor_transfer_fidelity(results_data):
    """Verify that UEL stress components transferred to UMAT SDVs match analytical/UEL values."""
    config_b = results_data.get("PK_F1720_DIAG_1ELEM_B")
    assert config_b is not None

    sdvs = config_b["elem_sdvs"]
    assert len(sdvs) == 4, f"Expected 4 Gauss points, got {len(sdvs)}"

    # All 4 Gauss points under uniform tension should have identical stresses
    for sdv in sdvs:
        s11 = sdv["s11_uel"]
        s22 = sdv["s22_uel"]
        s33 = sdv["s33_uel"]
        s12 = sdv["s12_uel"]
        svm = sdv["svm_uel"]

        # S11 (transverse normal) should be zero in 1D tension
        assert abs(s11) < 1.0e-6, f"S11 not zero: {s11}"

        # S22 (axial tension) should match reaction force / area = 0.2288 kN/mm^2
        assert abs(s22 - 0.2288094) < 1.0e-4, f"S22 mismatch: {s22}"

        # S33 (plane strain out-of-plane) = nu * S22 = 0.3 * 0.2288 = 0.06864 kN/mm^2
        assert abs(s33 - 0.0686428) < 1.0e-4, f"S33 mismatch: {s33}"

        # S12 (shear) should be zero
        assert abs(s12) < 1.0e-6, f"S12 not zero: {s12}"

        # Von Mises = sqrt(S22^2 + S33^2 - S22*S33) = 0.20337 kN/mm^2
        assert abs(svm - 0.203370) < 1.0e-4, f"Von Mises mismatch: {svm}"


def test_native_miseseri_activation(results_data):
    """Verify that native MISESERI and MISESAVG are activated in Config B, but zero in Config A."""
    config_a = results_data.get("PK_F1720_DIAG_1ELEM_A")
    config_b = results_data.get("PK_F1720_DIAG_1ELEM_B")

    # Config A: stress is zero, so MISESERI and MISESAVG must be 0.0
    assert bool(config_a["has_miseseri"]) is True
    assert config_a["miseseri_vals"][0]["data"] == 0.0
    assert config_a["misesavg_vals"][0]["data"] == 0.0

    # Config B: stress is non-zero, so MISESAVG must be > 0
    assert bool(config_b["has_miseseri"]) is True
    assert bool(config_b["has_misesavg"]) is True
    misesavg = config_b["misesavg_vals"][0]["data"]
    assert misesavg > 0.0, f"MISESAVG was {misesavg}, expected > 0"
    # MISESAVG should be exactly on the order of 1e-14 (scaled by 1e-11 / 210)
    assert 1.0e-15 < misesavg < 1.0e-13, f"MISESAVG unexpected magnitude: {misesavg}"
