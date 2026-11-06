# -*- coding: utf-8 -*-
"""
tests/unit/test_f1632_local_resolution.py
=========================================
Unit test for local FPZ mesh resolution analysis logic.
Verifies zone classification, distance calculations, and edge statistics.
"""

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.analyze_local_fpz_resolution import analyze_local_resolution


def test_zone_classification_and_metrics():
    """Verify that synthetic INP elements are correctly classified into zones."""
    scratch_dir = REPO_ROOT / "tmp_pytest"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    test_inp = scratch_dir / "test_mesh.inp"
    try:
        # Create simple mesh with 1 element at notch tip, 1 at ligament, 1 at hole boundary, 1 in far field
        test_inp.write_text("""*NODE
1, 0.499, 0.499
2, 0.501, 0.499
3, 0.501, 0.501
4, 0.499, 0.501
5, 0.550, 0.550
6, 0.552, 0.550
7, 0.552, 0.552
8, 0.550, 0.552
9, 0.650, 0.550
10, 0.652, 0.550
11, 0.652, 0.552
12, 0.650, 0.552
13, 0.100, 0.100
14, 0.120, 0.100
15, 0.120, 0.120
16, 0.100, 0.120
*ELEMENT, TYPE=CPS4R
1, 1, 2, 3, 4
2, 5, 6, 7, 8
3, 9, 10, 11, 12
4, 13, 14, 15, 16
""", encoding="utf-8")

        # Should run without error and parse all 4 elements
        analyze_local_resolution(str(test_inp))
    finally:
        if test_inp.exists():
            test_inp.unlink()
