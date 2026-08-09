#!/usr/bin/env python3
"""
Unit and Contract Tests for Task F43DUALREBUILD1:
Dual-Candidate Mixed CPE3/CPE4 Phase-Field UEL Rebuild for MM and PK5
"""

import os
import sys
import json
import unittest
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.model_generation.rebuild_f43_mixed_uel_deck import (
    F43MixedUELDeckRebuilder,
    validate_rebuilt_deck_static,
    compute_polygon_signed_area,
    DEFAULT_L0,
    DEFAULT_GC,
    DEFAULT_THICKNESS,
    DEFAULT_EMOD,
    DEFAULT_ENU,
    DEFAULT_PARK
)
from scripts.model_generation.run_f43_dual_candidate_rebuild import (
    CANDIDATES,
    SUBROUTINE_SOURCE,
    RECORD_PATH,
    run_dual_rebuild
)


class TestF43DualCandidateRebuild(unittest.TestCase):
    """Deterministic offline test suite for MM and PK5 Phase-Field UEL rebuilds."""

    def test_01_frozen_source_hashes(self):
        """Verify frozen physical candidate input deck hashes match recorded baseline."""
        for cand_key, cfg in CANDIDATES.items():
            src_path = cfg["source_deck"]
            self.assertTrue(src_path.is_file(), f"Source deck missing: {src_path}")
            actual_sha = hashlib.sha256(src_path.read_bytes()).hexdigest()
            self.assertEqual(actual_sha, cfg["expected_sha256"], f"Candidate {cand_key} hash mismatch")

    def test_02_subroutine_source_availability(self):
        """Verify qualified Fortran subroutine source exists and is non-empty."""
        self.assertTrue(SUBROUTINE_SOURCE.is_file(), f"Subroutine missing: {SUBROUTINE_SOURCE}")
        sub_text = SUBROUTINE_SOURCE.read_text(encoding="utf-8", errors="replace")
        self.assertIn("SUBROUTINE UEL", sub_text)
        self.assertIn("SUBROUTINE UMAT", sub_text)
        self.assertIn("SHAPEFUN_QUAD", sub_text)
        self.assertIn("SHAPEFUN_TRI", sub_text)

    def test_03_mm_element_count_mapping(self):
        """Verify MM candidate layered element counts (2206 physical -> 6618 layered)."""
        cfg = CANDIDATES["MM"]
        rebuilder = F43MixedUELDeckRebuilder(str(cfg["source_deck"]), "F43REM4_MM")
        rebuilder.parse()

        self.assertEqual(len(rebuilder.part_nodes), 2294)
        self.assertEqual(len(rebuilder.physical_quads), 2137)
        self.assertEqual(len(rebuilder.physical_tris), 69)
        self.assertEqual(len(rebuilder.ordered_elements), 2206)

        summary = rebuilder.generate_rebuilt_deck(str(cfg["rebuilt_deck"]))
        self.assertEqual(summary["total_layered_elements"], 6618)
        self.assertEqual(summary["counts"]["U1"], 2137)
        self.assertEqual(summary["counts"]["U2"], 2137)
        self.assertEqual(summary["counts"]["U3"], 69)
        self.assertEqual(summary["counts"]["U4"], 69)
        self.assertEqual(summary["counts"]["CPE4"], 2137)
        self.assertEqual(summary["counts"]["CPE3"], 69)

    def test_04_pk5_element_count_mapping(self):
        """Verify PK5 candidate layered element counts (4894 physical -> 14682 layered)."""
        cfg = CANDIDATES["PK5"]
        rebuilder = F43MixedUELDeckRebuilder(str(cfg["source_deck"]), "F43REM4_PK5")
        rebuilder.parse()

        self.assertEqual(len(rebuilder.part_nodes), 4998)
        self.assertEqual(len(rebuilder.physical_quads), 4766)
        self.assertEqual(len(rebuilder.physical_tris), 128)
        self.assertEqual(len(rebuilder.ordered_elements), 4894)

        summary = rebuilder.generate_rebuilt_deck(str(cfg["rebuilt_deck"]))
        self.assertEqual(summary["total_layered_elements"], 14682)
        self.assertEqual(summary["counts"]["U1"], 4766)
        self.assertEqual(summary["counts"]["U2"], 4766)
        self.assertEqual(summary["counts"]["U3"], 128)
        self.assertEqual(summary["counts"]["U4"], 128)
        self.assertEqual(summary["counts"]["CPE4"], 4766)
        self.assertEqual(summary["counts"]["CPE3"], 128)

    def test_05_element_id_offsets_and_layer_correspondence(self):
        """Verify exact element-ID offset scheme and connectivity across all 3 layers."""
        for cand_key in ["MM", "PK5"]:
            cfg = CANDIDATES[cand_key]
            rebuilder = F43MixedUELDeckRebuilder(str(cfg["source_deck"]), cfg["candidate_name"])
            rebuilder.parse()
            nphys = len(rebuilder.ordered_elements)

            for el in rebuilder.ordered_elements:
                orig_id = el["orig_id"]
                layer1_id = orig_id
                layer2_id = nphys + orig_id
                layer3_id = 2 * nphys + orig_id

                self.assertTrue(1 <= layer1_id <= nphys)
                self.assertTrue(nphys + 1 <= layer2_id <= 2 * nphys)
                self.assertTrue(2 * nphys + 1 <= layer3_id <= 3 * nphys)

    def test_06_geometry_orientation_and_area_conservation(self):
        """Verify positive signed area for all elements and exact domain area 1.0 mm^2."""
        for cand_key in ["MM", "PK5"]:
            cfg = CANDIDATES[cand_key]
            rebuilder = F43MixedUELDeckRebuilder(str(cfg["source_deck"]), cfg["candidate_name"])
            rebuilder.parse()

            self.assertTrue(rebuilder.geometry_valid)
            self.assertEqual(len(rebuilder.validation_errors), 0)

            total_area = 0.0
            for eid, nids in rebuilder.physical_quads.items():
                coords = [rebuilder.part_nodes[nid] for nid in nids]
                a = compute_polygon_signed_area(coords)
                self.assertGreater(a, 0.0, f"Quad {eid} non-positive in {cand_key}")
                total_area += a

            for eid, nids in rebuilder.physical_tris.items():
                coords = [rebuilder.part_nodes[nid] for nid in nids]
                a = compute_polygon_signed_area(coords)
                self.assertGreater(a, 0.0, f"Tri {eid} non-positive in {cand_key}")
                total_area += a

            self.assertAlmostEqual(total_area, 1.0, places=4, msg=f"Total area deviation in {cand_key}")

    def test_07_entity_and_boundary_preservation(self):
        """Verify required NSETs, RP, Equations, and BCs are fully preserved."""
        for cand_key in ["MM", "PK5"]:
            cfg = CANDIDATES[cand_key]
            val_res = validate_rebuilt_deck_static(
                rebuilt_deck_path=str(cfg["rebuilt_deck"]),
                expected_nphys=cfg["physical_elements"],
                expected_quads=cfg["physical_quads"],
                expected_tris=cfg["physical_tris"],
                expected_nodes=cfg["part_nodes"]
            )
            self.assertTrue(val_res["all_passed"], f"Static checks failed for {cand_key}: {val_res['checks']}")
            self.assertTrue(val_res["checks"]["rp_nset_exists"])
            self.assertTrue(val_res["checks"]["bottom_nodes_nset_exists"])
            self.assertTrue(val_res["checks"]["top_nodes_nset_exists"])
            self.assertTrue(val_res["checks"]["equation_shear_coupling_exists"])
            self.assertTrue(val_res["checks"]["bottom_fix_bc_exists"])
            self.assertTrue(val_res["checks"]["top_vertical_bc_exists"])
            self.assertTrue(val_res["checks"]["rp_shear_bc_exists"])

    def test_08_cross_candidate_scientific_equality(self):
        """Prove MM and PK5 use identical material parameters and differ only in mesh."""
        mm_rebuilder = F43MixedUELDeckRebuilder(str(CANDIDATES["MM"]["source_deck"]), "MM")
        pk5_rebuilder = F43MixedUELDeckRebuilder(str(CANDIDATES["PK5"]["source_deck"]), "PK5")

        self.assertEqual(mm_rebuilder.l0, pk5_rebuilder.l0)
        self.assertEqual(mm_rebuilder.gc, pk5_rebuilder.gc)
        self.assertEqual(mm_rebuilder.thickness, pk5_rebuilder.thickness)
        self.assertEqual(mm_rebuilder.emod, pk5_rebuilder.emod)
        self.assertEqual(mm_rebuilder.enu, pk5_rebuilder.enu)
        self.assertEqual(mm_rebuilder.park, pk5_rebuilder.park)

    def test_09_master_rebuild_record_integrity(self):
        """Verify F43DUALREBUILD1_RECORD.json contains complete decision and lineage state."""
        self.assertTrue(RECORD_PATH.is_file(), f"Master record missing: {RECORD_PATH}")
        rec = json.loads(RECORD_PATH.read_text(encoding="utf-8"))

        self.assertEqual(rec["task_id"], "F43DUALREBUILD1")
        self.assertEqual(rec["status"], "complete_pass")
        self.assertEqual(rec["scientific_decision_state"]["Gate_C1_localization"], "PASS")
        self.assertEqual(rec["scientific_decision_state"]["best_adaptive_candidate"], "F43REM4_MM")
        self.assertEqual(rec["scientific_decision_state"]["best_resolution_efficiency_compromise"], "F43REM4_PK5")
        self.assertEqual(rec["scientific_decision_state"]["final_selected_candidate"], "none")
        self.assertEqual(rec["scientific_decision_state"]["Gate_C1_phase_field_resolution"], "HOLD")
        self.assertEqual(rec["candidates"]["MM"]["total_layered_elements"], 6618)
        self.assertEqual(rec["candidates"]["PK5"]["total_layered_elements"], 14682)
        self.assertFalse(rec["authority_boundary"]["execution_authorized"])
        self.assertEqual(rec["authority_boundary"]["maximum_jobs_now"], 0)


if __name__ == "__main__":
    unittest.main()
