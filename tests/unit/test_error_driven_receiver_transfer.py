#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_error_driven_receiver_transfer.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: e39e61b8-9aaa-4c83-af32-a9b0d93b40fa
Turn: 415
Protocol Version: 2

Unit test suite for the C4 -> Error-Driven Receiver nonmatching state transfer.
"""
from __future__ import print_function, division
import json
import math
import unittest
from pathlib import Path
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

from scripts.state_transfer.c4_to_c5_spatial_mapping import Mesh2D, C4ToC5TransferMapper
from scripts.validation.audit_error_driven_receiver_transfer import (
    C4_DONOR_INP, RECEIVER_INP, C4_STEP1_ENDPOINT, C4_STEP1_FULL_HISTORY, OUTPUT_REPORT,
    compute_mesh_quadrature_integrals
)


class TestErrorDrivenReceiverTransfer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c4 = Mesh2D.from_inp(C4_DONOR_INP, name="C4_Donor", max_physical_node=7265)
        cls.rec = Mesh2D.from_inp(RECEIVER_INP, name="ErrorDriven_Receiver", max_physical_node=12821)
        cls.mapper = C4ToC5TransferMapper(cls.c4, cls.rec)

    def test_topology_and_seam_pairs(self):
        """Verify element, node, and duplicate slit counts for donor and receiver."""
        self.assertEqual(len(self.c4.elements), 7056)
        self.assertEqual(len(self.c4.nodes), 7265)
        self.assertEqual(len(self.c4.seam_pairs), 40)

        self.assertEqual(len(self.rec.elements), 12544)
        self.assertEqual(len(self.rec.nodes), 12821)
        self.assertEqual(len(self.rec.seam_pairs), 52)

    def test_mapping_coverage_and_reconstruction(self):
        """Verify 100% mapping coverage, 0 flank violations, and machine-precision reconstruction."""
        node_map, n_stats = self.mapper.build_node_transfer_map()
        self.assertEqual(n_stats["mapped_nodes"], 12821)
        self.assertEqual(n_stats["flank_violations"], 0)
        self.assertLess(n_stats["max_recon_error"], 1e-15)

        gp_map, gp_stats = self.mapper.build_gauss_point_transfer_map()
        self.assertEqual(gp_stats["mapped_gps"], 50176)
        self.assertLess(gp_stats["max_recon_error"], 1e-15)

    def test_synthetic_patch_benchmarks(self):
        """Verify constant, affine, and slit discontinuity benchmarks."""
        u_c = (0.0012, -0.0008)
        d_c = 0.45
        h_c = 2.5
        donor_u = {nid: u_c for nid in self.c4.nodes}
        donor_d = {nid: d_c for nid in self.c4.nodes}
        donor_h = {(eid, gp): h_c for (eid, gp) in self.c4.gauss_points}
        res_const = self.mapper.transfer_fields(donor_u, donor_d, donor_h)

        max_u_err = max(max(abs(res_const["u"][n][0] - u_c[0]), abs(res_const["u"][n][1] - u_c[1])) for n in self.rec.nodes)
        max_d_err = max(abs(res_const["d"][n] - d_c) for n in self.rec.nodes)
        max_h_err = max(abs(res_const["h"][k] - h_c) for k in self.rec.gauss_points)

        self.assertLess(max_u_err, 1e-14)
        self.assertLess(max_d_err, 1e-14)
        self.assertLess(max_h_err, 1e-14)

        # Slit flank step discontinuity
        slit_fn = lambda flank: 3.0 if flank == "UPPER" else 0.5
        donor_h_slit = {(eid, gp): slit_fn(self.c4.element_flank[eid]) for (eid, gp) in self.c4.gauss_points}
        res_slit = self.mapper.transfer_fields(donor_u, donor_d, donor_h_slit)
        slit_leakage = max(abs(res_slit["h"][(eid, gp)] - slit_fn(self.rec.element_flank[eid])) for (eid, gp) in self.rec.gauss_points)
        self.assertLess(slit_leakage, 1e-12)

    def test_authentic_fixture_transfer(self):
        """Verify authentic Step-1 C4 fixture transfer satisfies damage, history, and energy gates."""
        with open(C4_STEP1_ENDPOINT, "r", encoding="utf-8") as f:
            ep = json.load(f)
        with open(C4_STEP1_FULL_HISTORY, "r", encoding="utf-8") as f:
            fh = json.load(f)

        fixture_u = {r[0]: (r[1], r[2]) for r in ep["nodes"]}
        fixture_d = {r[0]: r[3] for r in ep["nodes"]}
        fixture_h = {(rec_h["element_id"], rec_h["gp"]): rec_h["h_MPa"] for rec_h in fh["history_gp_records"]}

        fixture_res = self.mapper.transfer_fields(fixture_u, fixture_d, fixture_h)

        # Damage in [0, 1]
        for d in fixture_res["d"].values():
            self.assertGreaterEqual(d, 0.0)
            self.assertLessEqual(d, 1.0)

        # History non-negativity
        for h in fixture_res["h"].values():
            self.assertGreaterEqual(h, 0.0)

        # Energy integrals
        c4_int = compute_mesh_quadrature_integrals(self.c4, fixture_d, fixture_h)
        rec_int = compute_mesh_quadrature_integrals(self.rec, fixture_res["d"], fixture_res["h"])

        rel_area = abs(rec_int["area_mm2"] - c4_int["area_mm2"]) / c4_int["area_mm2"]
        rel_e_frac = abs(rec_int["e_frac_kn_mm"] - c4_int["e_frac_kn_mm"]) / c4_int["e_frac_kn_mm"]

        self.assertLess(rel_area, 1e-10)
        self.assertLess(rel_e_frac, 0.001)  # 0.073% discrepancy, well below 0.1%

    def test_audit_report_consistency(self):
        """Verify the generated JSON audit report is valid and consistent."""
        self.assertTrue(OUTPUT_REPORT.exists())
        with open(OUTPUT_REPORT, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "ERROR_DRIVEN_RECEIVER_TRANSFER_TECHNICALLY_VERIFIED")
        self.assertTrue(report["verification_passed"])
        self.assertEqual(report["mapping_completeness"]["unmapped_receiver_nodes"], 0)
        self.assertEqual(report["mapping_completeness"]["unmapped_receiver_gps"], 0)
        self.assertEqual(report["mapping_completeness"]["flank_isolation_violations"], 0)


if __name__ == "__main__":
    unittest.main()
