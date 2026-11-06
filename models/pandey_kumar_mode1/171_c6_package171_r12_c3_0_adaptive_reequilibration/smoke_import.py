#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remote import smoke test for Package 171-R12 / F1629."""
import sys
from pathlib import Path

cur_dir = Path(__file__).resolve().parent
repo = cur_dir / "runtime"
if str(repo) not in sys.path:
    sys.path.insert(0, str(repo))

try:
    import tempfile
    import scripts.state_transfer.anderson_acceleration as anderson
    assert hasattr(anderson, "AndersonAccelerator"), "Anderson class missing"
    import scripts.state_transfer.driver_package171_r12_c6_coupled_pdas as p171_r12
    assert hasattr(p171_r12, "Package171R12C6PDASDriver"), "Driver class missing"
    assert hasattr(p171_r12, "DONOR_REFERENCE_FORCE_KN"), "Reference constants missing"

    class _SmokeMesh:
        def __init__(self):
            self.elements = {1: [1, 2, 3, 4]}
            self.nodes = {1: (0.0, 0.0), 2: (1.0, 0.0), 3: (1.0, 1.0), 4: (0.0, 1.0)}
            self.node_flank = {}

    with tempfile.TemporaryDirectory() as td:
        drv = p171_r12.Package171R12C6PDASDriver(
            package=str(cur_dir),
            output=td,
            extractor=str(repo / "scripts" / "validation" / "extract_package148_iteration.py"),
            anderson_enabled=True,
            max_outer=2,
        )
        drv.mesh = _SmokeMesh()
        drv.d0 = {1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1}
        drv.h0 = {(1, g): 10.0 for g in range(1, 5)}
        drv.u0 = {n: (0.0, 0.0) for n in range(1, 5)}
        drv.target_uy = 0.0018703125442191958
        drv.load = lambda: None
        u_mock = {n: (0.0001, 0.0018703125442191958) for n in range(1, 5)}
        ep_mock = {
            "rf2_kN": p171_r12.DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": p171_r12.DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": p171_r12.DONOR_REFERENCE_FRACTURE_ENERGY_KNMM,
            "total_energy_kNmm": p171_r12.DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
        }
        drv.solve_subproblem = lambda s, o, i, role, d, act, u, h, tuy: (
            (d, u_mock, ep_mock) if role == "mechanical" else ({n: 0.1 + 0.005 * (0.98 ** o) for n in range(1, 5)}, None, {})
        )
        summary = drv.solve_coupled_equilibration()
        assert summary["outer_iterations_completed"] == 2

    print("REMOTE_IMPORT_SUCCESS: True")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
