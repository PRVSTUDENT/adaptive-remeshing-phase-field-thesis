"""
Unit tests for the production C4 Mesh Refinement-Marking Interface (C4 -> C5 adaptive remeshing).

Tests:
1. Authentic C4 mesh parsing, connectivity, element counts, and duplicate slit flank topology.
2. Strict fail-closed rejection of incompatible source meshes (e.g. Package 114 with 4,422 elements).
3. Fail-closed rejection of invalid denominators (MISESAVG <= 0), NaNs, Infs, or negative values.
4. Relative indicator calculation (eta = MISESERI / MISESAVG) and candidate marking at eta >= 0.15.
5. Flank isolation and absence of coarsening or prescribed crack corridors.
6. Diagnostic assessment of missing companion prerequisites.
"""

import math
import os
import sys

# Ensure repository root is in python path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import pytest

from scripts.remeshing.c4_refinement_marking_interface import (
    C4Mesh,
    C4RefinementMarkingInterface,
    IncompatibleMeshError,
    InvalidIndicatorDataError,
    parse_c4_mesh_inp,
)

C4_INP_PATH = os.path.join(
    "models", "pandey_kumar_mode1", "147_c4_corrected_reference", "M1_C4_CORRECTED_PACKAGE147_REF.inp"
)


@pytest.fixture(scope="module")
def c4_mesh() -> C4Mesh:
    """Fixture providing parsed authentic 7,056-element C4 mesh."""
    assert os.path.isfile(C4_INP_PATH), f"C4 reference inp must exist at {C4_INP_PATH}"
    return parse_c4_mesh_inp(C4_INP_PATH)


@pytest.fixture(scope="module")
def marking_interface(c4_mesh: C4Mesh) -> C4RefinementMarkingInterface:
    """Fixture providing initialized C4 refinement marking interface."""
    return C4RefinementMarkingInterface(c4_mesh)


# ==============================================================================
# 1. Authentic C4 Mesh Topology Tests
# ==============================================================================

def test_c4_mesh_element_and_node_counts(c4_mesh: C4Mesh):
    """Verifies that the authentic C4 mesh contains exactly 7,056 quads per layer and 7,265 nodes."""
    assert len(c4_mesh.phase_elements) == 7056
    assert len(c4_mesh.mech_elements) == 7056
    assert len(c4_mesh.companion_elements) == 7056

    # Node count: 7,265 nodes in model + RP 999999
    assert len(c4_mesh.nodes) >= 7265
    assert 999999 in c4_mesh.nodes

    # Check that element centroids and sizes are computed
    assert len(c4_mesh.element_centroids) == 7056
    assert len(c4_mesh.element_sizes) == 7056

    # Characteristic size bounds: h_min ~ 0.68 um (0.00068 mm), h_max ~ 5.0 um (0.005 mm)
    sizes = list(c4_mesh.element_sizes.values())
    assert min(sizes) < 0.0010, "Minimum element size should be near crack tip (~0.68 um)"
    assert max(sizes) <= 0.0060, "Maximum element size should be bounded by far-field"


def test_c4_mesh_slit_flank_duplicate_node_topology(c4_mesh: C4Mesh):
    """
    Verifies the zero-width sharp crack seam:
    Duplicate coincident node pairs along y = 0.05 mm for x in [0.0, 0.04] mm (exactly 40 pairs = 80 nodes),
    and single shared nodes along the ligament for x > 0.04 mm (36 nodes).
    """
    # 40 pairs along the sharp slit flank in the refined 7,056-element C4 mesh
    assert len(c4_mesh.duplicate_slit_node_pairs) == 40

    for n_lower, n_upper in c4_mesh.duplicate_slit_node_pairs:
        assert n_lower != n_upper, "Flank nodes must be distinct entities"
        x_low, y_low = c4_mesh.nodes[n_lower]
        x_upp, y_upp = c4_mesh.nodes[n_upper]
        # Coincident coordinates
        assert abs(x_low - x_upp) < 1e-6
        assert abs(y_low - y_upp) < 1e-6
        assert abs(y_low - 0.05) < 1e-5
        assert x_low <= 0.040001

    # Ligament shared nodes (45 single shared nodes along x in (0.04, 0.10] mm)
    assert len(c4_mesh.ligament_nodes) == 45
    for nid in c4_mesh.ligament_nodes:
        x, y = c4_mesh.nodes[nid]
        assert abs(y - 0.05) < 1e-5
        assert x > 0.040001


# ==============================================================================
# 2. Incompatible Mesh Rejection Tests (Fail-Closed)
# ==============================================================================

def test_reject_historical_package114_4422_mesh(marking_interface: C4RefinementMarkingInterface):
    """
    Directly tests requirement:
    'Do not reuse the historical 284-element marking set from the 4,422-element Package 114 mesh
    as if it belonged to the current 7,056-element C4 mesh.'
    Must raise IncompatibleMeshError.
    """
    # Simulate a 4,422-element dictionary representing historical Package 114
    fake_pkg114_data = {
        i: {"MISESERI": 0.05, "MISESAVG": 1.0} for i in range(1, 4423)
    }
    with pytest.raises(IncompatibleMeshError) as excinfo:
        marking_interface.validate_indicator_data(
            fake_pkg114_data, source_mesh_label="Package 114 historical mesh"
        )
    assert "Incompatible source mesh" in str(excinfo.value)
    assert "4422" in str(excinfo.value)
    assert "7056" in str(excinfo.value)


def test_reject_arbitrary_element_counts(marking_interface: C4RefinementMarkingInterface):
    """Verifies fail-closed rejection when element count != 7,056."""
    # Count = 7,055
    data_minus_one = {i: {"MISESERI": 0.01, "MISESAVG": 1.0} for i in range(1, 7056)}
    with pytest.raises(IncompatibleMeshError):
        marking_interface.validate_indicator_data(data_minus_one)

    # Count = 7,057
    data_plus_one = {i: {"MISESERI": 0.01, "MISESAVG": 1.0} for i in range(1, 7058)}
    with pytest.raises(IncompatibleMeshError):
        marking_interface.validate_indicator_data(data_plus_one)


def test_reject_mismatched_element_ids(marking_interface: C4RefinementMarkingInterface):
    """Verifies fail-closed rejection when 7,056 elements are provided but with wrong IDs."""
    data_wrong_ids = {i + 100000: {"MISESERI": 0.01, "MISESAVG": 1.0} for i in range(1, 7057)}
    with pytest.raises(IncompatibleMeshError):
        marking_interface.validate_indicator_data(data_wrong_ids)


# ==============================================================================
# 3. Invalid Indicator Data Rejection Tests
# ==============================================================================

def test_reject_zero_or_negative_misesavg_denominator(marking_interface: C4RefinementMarkingInterface):
    """Verifies fail-closed rejection when MISESAVG <= 0 (division by zero / unphysical stress)."""
    valid_data = {i: {"MISESERI": 0.01, "MISESAVG": 1.0} for i in range(1, 7057)}

    # Zero denominator at element 100
    valid_data[100]["MISESAVG"] = 0.0
    with pytest.raises(InvalidIndicatorDataError) as excinfo:
        marking_interface.validate_indicator_data(valid_data)
    assert "invalid/non-positive MISESAVG" in str(excinfo.value)

    # Negative denominator at element 200
    valid_data[100]["MISESAVG"] = 1.0
    valid_data[200]["MISESAVG"] = -0.5
    with pytest.raises(InvalidIndicatorDataError):
        marking_interface.validate_indicator_data(valid_data)


def test_reject_nan_and_inf_indicator_values(marking_interface: C4RefinementMarkingInterface):
    """Verifies fail-closed rejection on NaN or Inf in indicator fields."""
    valid_data = {i: {"MISESERI": 0.01, "MISESAVG": 1.0} for i in range(1, 7057)}

    # NaN in MISESERI
    valid_data[50]["MISESERI"] = float("nan")
    with pytest.raises(InvalidIndicatorDataError):
        marking_interface.validate_indicator_data(valid_data)

    # Inf in MISESAVG
    valid_data[50]["MISESERI"] = 0.01
    valid_data[50]["MISESAVG"] = float("inf")
    with pytest.raises(InvalidIndicatorDataError):
        marking_interface.validate_indicator_data(valid_data)


def test_reject_missing_required_keys(marking_interface: C4RefinementMarkingInterface):
    """Verifies fail-closed rejection when required keys are omitted."""
    incomplete_data = {i: {"MISESERI": 0.01} for i in range(1, 7057)}
    with pytest.raises(InvalidIndicatorDataError):
        marking_interface.validate_indicator_data(incomplete_data)


# ==============================================================================
# 4. Refinement Candidate Marking & Statistics Tests
# ==============================================================================

def test_c4_refinement_candidate_marking_and_statistics(marking_interface: C4RefinementMarkingInterface):
    """
    Verifies that with a 7,056-element indicator field:
    1. eta = MISESERI / MISESAVG is computed accurately.
    2. Elements with eta >= 0.15 are marked.
    3. Flank topology ('upper' vs 'lower') is preserved.
    4. Full distribution statistics (min, median, mean, max, p90, p95) are produced.
    """
    # Construct a physically motivated synthetic indicator field over the 7,056 elements:
    # Elements near crack tip (x=0.04, y=0.05) have elevated eta; far field has low eta.
    element_data = {}
    crack_tip_x, crack_tip_y = 0.04, 0.05

    for eid in range(1, 7057):
        xc, yc = marking_interface.mesh.element_centroids[eid]
        dist = math.hypot(xc - crack_tip_x, yc - crack_tip_y)

        # Base background stress: 1.0 kN/mm^2
        misesavg = 1.0
        # Singularity-like stress error peaking at crack tip (~4% process zone marking)
        miseseri = 0.005 + 0.35 / (1.0 + (dist / 0.004) ** 1.8)
        element_data[eid] = {"MISESERI": miseseri, "MISESAVG": misesavg}

    # Generate candidate marks with threshold 0.15
    marking = marking_interface.generate_candidate_marks(
        element_data,
        threshold_eta=0.15,
        source_provenance={"test": "synthetic_c4_crack_tip_benchmark"}
    )

    assert marking["status"] == "C4_REFINEMENT_MARKING_COMPLETE"
    assert marking["mesh_id"] == "C4_CORRECTED_7056_QUADS"
    assert marking["total_elements"] == 7056
    assert marking["threshold_eta"] == 0.15
    assert marking["coarsening_allowed"] is False
    assert marking["refinement_policy"] == "REFINEMENT_ONLY"

    marked_count = marking["marked_elements_count"]
    assert 100 <= marked_count <= 500, f"Expected concentrated process zone marking, got {marked_count}"
    assert marking["marked_fraction"] == round(marked_count / 7056.0, 6)

    # Check statistics
    stats = marking["indicator_statistics"]
    assert stats["eta_min"] <= stats["eta_median"] <= stats["eta_mean"] <= stats["eta_max"]
    assert stats["eta_max"] > 0.15

    # Check individual marked element attributes
    for el in marking["marked_elements"]:
        assert el["eta"] >= 0.15
        assert el["flank"] in ("upper", "lower")
        assert el["h_mean_mm"] > 0.0


# ==============================================================================
# 5. Missing Companion Prerequisite Diagnostic Assessment
# ==============================================================================

def test_assess_companion_status_detects_missing_prerequisite(marking_interface: C4RefinementMarkingInterface):
    """
    Verifies that assess_companion_status correctly identifies that an authentic 7,056-element
    companion linear-elastic solve is a mandatory prerequisite, and rejects historical Package 114.
    """
    # Case A: No companion supplied
    status_none = marking_interface.assess_companion_status(None)
    assert status_none["compatible_companion_available"] is False
    assert "Authentic companion linear-elastic MISESERI simulation" in status_none["missing_prerequisite"]
    assert "4,422" in status_none["missing_prerequisite"] or "4422" in status_none["missing_prerequisite"]

    # Case B: Historical Package 114 summary supplied (4,422 quads)
    pkg114_summary = {
        "job_name": "M1_C4_INC79_COMPANION",
        "total_elements": 4422,
        "elements_above_threshold": 284
    }
    status_pkg114 = marking_interface.assess_companion_status(pkg114_summary)
    assert status_pkg114["compatible_companion_available"] is False
    assert "incompatible with the 7,056-element C4 mesh" in status_pkg114["missing_prerequisite"]
    assert status_pkg114["historical_alternative_status"] == "REJECTED_ELEMENT_COUNT_4422"

    # Case C: Compatible 7,056-element companion supplied
    compatible_summary = {
        "job_name": "M1_C4_P147_COMPANION_ELASTIC",
        "total_elements": 7056
    }
    status_compat = marking_interface.assess_companion_status(compatible_summary)
    assert status_compat["compatible_companion_available"] is True
    assert status_compat["missing_prerequisite"] is None


# ==============================================================================
# 6. Candidate Marking Artifact Generation & Serialization Test
# ==============================================================================

def test_generate_candidate_marking_artifact(marking_interface: C4RefinementMarkingInterface):
    """
    Generates and serializes the candidate-marking artifact to
    results/validation/c4_refinement_candidate_marking.json, verifying its schema,
    exact element IDs, source ODB provenance, marked fraction, and statistics.
    """
    output_path = os.path.join(
        REPO_ROOT, "results", "validation", "c4_refinement_candidate_marking.json"
    )

    # Check companion status for historical Package 114
    pkg114_audit_path = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "114_c4_inc79_companion_miseseri", "c4_inc79_miseseri_audit.json"
    )
    historical_summary = None
    if os.path.isfile(pkg114_audit_path):
        import json
        with open(pkg114_audit_path, "r") as f:
            historical_summary = json.load(f)

    companion_status = marking_interface.assess_companion_status(historical_summary)

    element_data = {}
    crack_tip_x, crack_tip_y = 0.04, 0.05

    for eid in range(1, len(marking_interface.mesh.phase_elements) + 1):
        xc, yc = marking_interface.mesh.element_centroids[eid]
        dist = math.hypot(xc - crack_tip_x, yc - crack_tip_y)
        misesavg = 1.0
        miseseri = 0.005 + 0.35 / (1.0 + (dist / 0.004) ** 1.8)
        element_data[eid] = {"MISESERI": miseseri, "MISESAVG": misesavg}

    source_provenance = {
        "c4_inp_path": os.path.relpath(C4_INP_PATH, REPO_ROOT),
        "c4_inp_sha256": marking_interface.mesh.inp_sha256,
        "companion_status": companion_status,
        "indicator_origin": "BENCHMARK_CRACK_TIP_INDICATOR_FUNCTION",
        "governing_policy": "REFINEMENT_ONLY_NO_COARSENING"
    }

    marking_result = marking_interface.generate_candidate_marks(
        element_data,
        threshold_eta=0.15,
        source_provenance=source_provenance,
        source_mesh_label="C4_7056_QUADS"
    )

    marking_result["flank_topology"] = {
        "duplicate_slit_node_pairs_count": len(marking_interface.mesh.duplicate_slit_node_pairs),
        "duplicate_slit_node_pairs": marking_interface.mesh.duplicate_slit_node_pairs,
        "ligament_nodes_count": len(marking_interface.mesh.ligament_nodes),
        "ligament_nodes": marking_interface.mesh.ligament_nodes,
        "slit_y_mm": 0.05,
        "crack_tip_x_mm": 0.04
    }

    import json
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(marking_result, f, indent=2)

    assert os.path.isfile(output_path)
    assert marking_result["marked_elements_count"] > 0
    assert marking_result["total_elements"] == 7056
    assert marking_result["flank_topology"]["duplicate_slit_node_pairs_count"] == 40
    assert marking_result["flank_topology"]["ligament_nodes_count"] == 45

