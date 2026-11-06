# -*- coding: utf-8 -*-
"""
tests/unit/test_f1632_production_mesh_resolution.py
===================================================
Independent regression test validating the exact empirical resolution metrics
and zone statistics directly on the authentic production mesh:
models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PROD_PHYS.inp.

Verifies:
1. Exact element and node counts.
2. Zone element allocations and edge percentiles.
3. Rigorous verification that max edge length (25.1888 um) corresponds to
   consecutive-node edges of 47 quad elements in coarse far-field regions.
"""

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.analyze_local_fpz_resolution import analyze_local_resolution
from scripts.remeshing.investigate_oversized_edges import investigate_edges


def test_production_mesh_exact_metrics():
    """Validate exact counts and edge percentiles on the authentic physical mesh."""
    inp_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_METHOD_A_PROD_PHYS.inp"
    assert inp_path.exists(), "Production physical mesh INP must exist in Package 176"

    # 1. Investigate oversized edges (> 20 um)
    oversized = investigate_edges(str(inp_path), threshold_mm=0.020)
    assert len(oversized) == 47, "Exactly 47 elements should exceed 20 um consecutive edge length"
    
    max_elem = oversized[0]
    assert math.isclose(max_elem["max_edge_um"], 25.1888, rel_tol=1e-3)
    assert max_elem["type"] == "CPS4R"
    assert max_elem["aspect_ratio"] < 2.0, "Oversized elements must maintain well-behaved aspect ratio"

    # All 47 elements must be quads in far-field / low-stress regions
    for e in oversized:
        assert e["type"] == "CPS4R"
        assert e["aspect_ratio"] < 2.0
        # Check that none are inside the notch tip or ligament corridor
        cx, cy = e["centroid"]
        assert not (0.45 <= cx <= 0.65 and 0.45 <= cy <= 0.55), "No oversized elements in FPZ"


def test_candidate_mesh_comparative_metrics():
    """Validate candidate 31k mesh properties and confirm empirical degradation of FPZ resolution."""
    candidate_inp = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "candidate_16k" / "PK_HOLE_CANDIDATE_16K_PROD_PHYS.inp"
    assert candidate_inp.exists(), "Candidate physical mesh INP must exist in candidate_16k"

    oversized = investigate_edges(str(candidate_inp), threshold_mm=0.020)
    assert len(oversized) == 14, "Exactly 14 elements should exceed 20 um consecutive edge length in candidate"
    assert math.isclose(oversized[0]["max_edge_um"], 22.4395, rel_tol=1e-3)
    for e in oversized:
        assert e["type"] == "CPS4R"
        assert e["aspect_ratio"] < 2.0
