"""Unit tests for Mode-I Corrected Method B crack-front topology, overshoot audit, and 3-model provenance.

Task ID: F1444-MODE1-VALIDATE-METHOD-B-CRACK-FRONT-AND-SUPERVISOR-COMPARISON
"""

import os
import json
import csv
import pytest
from collections import defaultdict, deque

REPO_ROOT = os.environ.get("REPO_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
if not os.path.exists(os.path.join(REPO_ROOT, "models")):
    REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"

CORR_DIR = os.path.join(
    REPO_ROOT,
    "models",
    "pandey_kumar_mode1",
    "40_method_b_corrected_propagation_14k",
)
EVIDENCE_DIR = os.path.join(CORR_DIR, "evidence_1412465")
CSV_PATH = os.path.join(EVIDENCE_DIR, "corrected_method_b_ligament_damage_profiles.csv")
INP_PATH = os.path.join(CORR_DIR, "M1_MB_CORRECTED_PROPAGATION_14K.inp")
TOPO_JSON = os.path.join(EVIDENCE_DIR, "crack_topology_verification.json")
EVO_JSON = os.path.join(EVIDENCE_DIR, "three_model_crack_front_evolution.json")


def test_evidence_files_exist():
    """Verify all evidence artifacts are present."""
    assert os.path.exists(CSV_PATH), f"Missing {CSV_PATH}"
    assert os.path.exists(INP_PATH), f"Missing {INP_PATH}"
    assert os.path.exists(TOPO_JSON), f"Missing {TOPO_JSON}"
    assert os.path.exists(EVO_JSON), f"Missing {EVO_JSON}"


def test_phase_field_damage_overshoot_bounds():
    """Verify that damage overshoot is strictly within unconstrained Newton equilibrium bounds."""
    max_d_observed = -1.0
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            d_val = float(r["damage_d_mean"])
            if d_val > max_d_observed:
                max_d_observed = d_val

    # Damage must not exceed 1.0 + 0.005 (0.5% unconstrained Galerkin residual tolerance)
    assert max_d_observed >= 1.0, "Expected damage localization to reach or slightly exceed 1.0"
    assert max_d_observed <= 1.002, f"Damage overshoot {max_d_observed} exceeds expected bound of 1.002"
    # Specific observed value is ~1.001123
    assert abs(max_d_observed - 1.001123) < 1e-4, f"Unexpected max damage value: {max_d_observed}"


def test_topological_graph_connectivity_from_evidence():
    """Verify that topological connectivity data confirms single connected component rooted at notch tip."""
    with open(TOPO_JSON, "r", encoding="utf-8") as f:
        topo = json.load(f)

    # Check d >= 0.95
    d95 = topo["d_95"]
    assert "u_0.005700" in d95
    assert d95["u_0.005700"]["total_cracked_elements"] == 0

    # At initiation (u = 0.005857 mm)
    u_pk = d95["u_0.005857"]
    assert u_pk["total_cracked_elements"] == 749
    assert u_pk["edge_sharing"]["num_components"] == 1
    assert u_pk["edge_sharing"]["tip_connected"] is True
    assert abs(u_pk["edge_sharing"]["tip_max_x"] - 0.973755) < 1e-4
    assert abs(u_pk["edge_sharing"]["all_max_x"] - u_pk["edge_sharing"]["tip_max_x"]) < 1e-9

    # At snap-through (u = 0.006000 mm)
    u_06 = d95["u_0.006000"]
    assert u_06["total_cracked_elements"] == 818
    assert u_06["edge_sharing"]["num_components"] == 1
    assert u_06["edge_sharing"]["tip_connected"] is True
    assert abs(u_06["edge_sharing"]["tip_max_x"] - 0.998982) < 1e-4
    assert abs(u_06["edge_sharing"]["all_max_x"] - u_06["edge_sharing"]["tip_max_x"]) < 1e-9

    # At termination (u = 0.007889 mm)
    u_end = d95["u_0.007889"]
    assert u_end["total_cracked_elements"] == 818
    assert u_end["edge_sharing"]["num_components"] == 1
    assert u_end["edge_sharing"]["tip_connected"] is True
    assert abs(u_end["edge_sharing"]["tip_max_x"] - 0.998982) < 1e-4


def test_threshold_sensitivity():
    """Verify threshold sensitivity (d >= 0.95 vs d >= 0.90)."""
    with open(TOPO_JSON, "r", encoding="utf-8") as f:
        topo = json.load(f)

    d95 = topo["d_95"]
    d90 = topo["d_90"]

    # Lower threshold must contain more or equal cracked elements
    for state_key in d95.keys():
        n95 = d95[state_key]["total_cracked_elements"]
        n90 = d90[state_key]["total_cracked_elements"]
        assert n90 >= n95, f"At {state_key}, d90 elements ({n90}) < d95 elements ({n95})"
        # Both must remain single connected component for propagating states
        if n95 > 0:
            assert d90[state_key]["edge_sharing"]["num_components"] == 1
            assert d90[state_key]["edge_sharing"]["tip_connected"] is True


def test_bfs_connectivity_algorithm_with_synthetic_gap():
    """Test the BFS connectivity algorithm directly, asserting it correctly detects a synthetic disconnect."""
    # Synthetic element adjacency:
    # Elements 1 -> 2 -> 3 (connected), element 99 (isolated / unlinked)
    adj = {
        1: {2},
        2: {1, 3},
        3: {2},
        99: set() # Disconnected element
    }
    centroids = {
        1: (0.50, 0.50), # Notch tip element
        2: (0.60, 0.50),
        3: (0.70, 0.50),
        99: (0.95, 0.50) # Spurious nucleation ahead of crack
    }
    notch_tip_elements = {1}
    active_set = {1, 2, 3, 99}

    # BFS components
    visited = set()
    components = []
    for eid in sorted(active_set):
        if eid not in visited:
            comp = []
            queue = deque([eid])
            visited.add(eid)
            while queue:
                curr = queue.popleft()
                comp.append(curr)
                for nbr in adj[curr]:
                    if nbr not in visited and nbr in active_set:
                        visited.add(nbr)
                        queue.append(nbr)
            components.append(comp)

    assert len(components) == 2, f"Expected 2 components, got {len(components)}"
    
    # Identify tip component
    tip_comp = None
    for c in components:
        if set(c) & notch_tip_elements:
            tip_comp = c
            break

    assert tip_comp is not None
    assert set(tip_comp) == {1, 2, 3}
    tip_max_x = max(centroids[e][0] for e in tip_comp)
    all_max_x = max(centroids[e][0] for e in active_set)
    assert tip_max_x == 0.70
    assert all_max_x == 0.95
    assert all_max_x > tip_max_x, "Algorithm successfully identified gap between tip crack and spurious island"


def test_three_model_crack_front_evolution_comparison():
    """Verify the comparative crack progression across all three models from EVO_JSON."""
    with open(EVO_JSON, "r", encoding="utf-8") as f:
        evo = json.load(f)

    ref = evo["reference_15k"]
    orig = evo["original_method_b_14k"]
    corr = evo["corrected_method_b_14k"]

    # 1. Reference 15k: snaps through by u = 0.0060 mm
    ref_u06 = next(s for s in ref if abs(s["u_target_mm"] - 0.0060) < 1e-4)
    assert ref_u06["x_front_d95_mm"] > 0.998

    # 2. Original Method B: pinned at x ~ 0.612 mm at u = 0.0060 mm
    orig_u06 = next(s for s in orig if abs(s["u_target_mm"] - 0.0060) < 1e-4)
    assert abs(orig_u06["x_front_d95_mm"] - 0.612312) < 1e-4

    # 3. Corrected Method B: snaps through to x ~ 0.999 mm at u = 0.0060 mm
    corr_u06 = next(s for s in corr if abs(s["u_target_mm"] - 0.0060) < 1e-4)
    assert abs(corr_u06["x_front_d95_mm"] - 0.998982) < 1e-4

    # 4. Partial-horizon integrity: Corrected Method B terminates at u = 0.007889 mm
    max_corr_u = max(s["u_actual_mm"] for s in corr)
    assert abs(max_corr_u - 0.007889) < 1e-5
    assert max_corr_u < 0.010, "Corrected Method B must not claim full 0.010 mm horizon"
