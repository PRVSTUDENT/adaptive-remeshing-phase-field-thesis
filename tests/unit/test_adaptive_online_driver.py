#!/usr/bin/env python3
"""
Unit and Integration Tests for Automated Closed-Loop Adaptive Remeshing Driver.
Comprehensive Qualification Suite:
  1. State Machine Transitions & JSON Persistence
  2. Crash Recovery & Idempotency
  3. Multi-Criteria Trigger Engine (TR-01, TR-02, TR-03, TR-04) & Conservative Sizing
  4. Adaptive Mesh Generator, Slit Flank Duplication & Signed-Area Validation
  5. 3-Layer UEL Deck Rebuilder (Quads & Mixed Topologies)
  6. Nonmatching State Transfer & Thermodynamic Invariant Auditor
  7. 4-Stage Restart Package Builder & Step Control Verification
  8. Full End-to-End Pilot Cycle Dry-Run & State Semantics
  9. Genuine Real Donor State Extractor (Job 1390447.mmaster02)
  10. Full Genuine Real-Pilot Cycle (REAL_PILOT_CYCLE_001) Generation
  11. Notification Preflight Smoke Test (PBS Email & Telegram Without Submitting)
  12. Same-Mesh Identity State Preservation & No-Healing Regression Test
"""

import sys
import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.adaptive_online.state_machine import AdaptiveStateMachine, AdaptiveState
from scripts.adaptive_online.trigger_engine import evaluate_adaptive_triggers, compute_element_metrics
from scripts.adaptive_online.mesh_adapter import generate_adaptive_mesh, compute_signed_polygon_area, StructuredCorridorStrategy, PandeyKumarNativeStrategy
from scripts.adaptive_online.deck_rebuilder import build_layered_uel_deck
from scripts.adaptive_online.transfer_pipeline import execute_full_state_transfer, validate_transfer_invariants
from scripts.adaptive_online.restart_builder import generate_four_stage_restart_package
from scripts.adaptive_online.field_extractor import extract_real_donor_state, parse_inp_physical_mesh
from scripts.adaptive_online.adaptive_driver import AdaptiveOnlineDriver


class TestAdaptiveOnlineDriver(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_adaptive_"))

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_state_machine_transitions_and_persistence(self):
        """Test 1: FSM transitions, validation, and atomic JSON persistence."""
        state_file = self.test_dir / "state.json"
        sm = AdaptiveStateMachine(state_file)
        
        self.assertEqual(sm.current_state, AdaptiveState.INITIALIZE.value)
        self.assertEqual(sm.current_cycle, "cycle_000")

        # Valid transition
        sm.transition_to(AdaptiveState.SEGMENT_READY, {"donor": "test_donor"})
        self.assertEqual(sm.current_state, AdaptiveState.SEGMENT_READY.value)
        self.assertEqual(sm.get_cycle_data("donor"), "test_donor")

        # Reload from disk
        sm2 = AdaptiveStateMachine(state_file)
        self.assertEqual(sm2.current_state, AdaptiveState.SEGMENT_READY.value)
        self.assertEqual(sm2.get_cycle_data("donor"), "test_donor")

        # Invalid transition should raise ValueError
        with self.assertRaises(ValueError):
            sm.transition_to(AdaptiveState.COMPLETE)

    def test_02_state_machine_crash_recovery(self):
        """Test 2: Crash recovery from interrupted states and idempotency."""
        state_file = self.test_dir / "crash_state.json"
        sm = AdaptiveStateMachine(state_file)
        sm.transition_to(AdaptiveState.SEGMENT_READY)
        sm.transition_to(AdaptiveState.SEGMENT_SOLVED, {"solved_u1": 0.0075})
        sm.transition_to(AdaptiveState.FIELDS_EXTRACTED, {"d_max": 0.42})

        # Simulate sudden process termination and restart
        sm_recovered = AdaptiveStateMachine(state_file)
        self.assertEqual(sm_recovered.current_state, AdaptiveState.FIELDS_EXTRACTED.value)
        self.assertEqual(sm_recovered.get_cycle_data("d_max"), 0.42)
        self.assertEqual(len(sm_recovered.data["history"]), 3)

    def test_03_trigger_engine_evaluation(self):
        """Test 3: Multi-criteria trigger evaluation and conservative sizing metrics."""
        mesh = generate_adaptive_mesh(
            refined_zone={"x_min": -0.02, "x_max": 0.02, "y_min": -0.02, "y_max": 0.02},
            local_h=0.010, global_h=0.025
        )
        
        # Test conservative element metrics
        elem_metrics = compute_element_metrics(mesh["nodes"], mesh["elements"])
        self.assertEqual(len(elem_metrics), mesh["num_physical_elements"])
        for m in elem_metrics.values():
            self.assertIn("h_max", m)
            self.assertIn("h_area", m)
            self.assertGreater(m["h_max"], 0.0)
            self.assertGreater(m["area"], 0.0)

        # Uncracked case
        uncracked_phase = {nid: 0.0 for nid in mesh["nodes"]}
        res_uncracked = evaluate_adaptive_triggers(
            nodes=mesh["nodes"],
            elements=mesh["elements"],
            nodal_phase=uncracked_phase,
            l0=0.015,
            d_invade_threshold=0.05
        )
        self.assertFalse(res_uncracked.remesh_required)
        self.assertEqual(len(res_uncracked.fired_triggers), 0)
        self.assertEqual(res_uncracked.classifications["h_res_limit_rule"], "ADOPTED_PHASE_FIELD_RESOLUTION_SIZING_RULE")

        # Cracked case invading coarse elements
        cracked_phase = {}
        for nid, (x, y) in mesh["nodes"].items():
            dist = math.hypot(x - 0.2, y - 0.2)
            cracked_phase[nid] = max(0.0, min(1.0, 0.9 * math.exp(-(dist / 0.02)**2)))

        res_cracked = evaluate_adaptive_triggers(
            nodes=mesh["nodes"],
            elements=mesh["elements"],
            nodal_phase=cracked_phase,
            l0=0.015,
            d_invade_threshold=0.05
        )
        self.assertTrue(res_cracked.remesh_required)
        self.assertIn("TR-01_COARSE_DAMAGE_INVASION", res_cracked.fired_triggers)
        self.assertGreater(res_cracked.refined_zone["x_max"], 0.20)

    def test_04_adaptive_mesh_geometry_and_area(self):
        """Test 4: Adaptive mesh generator, slit node duplication, and signed area validation."""
        zone = {"x_min": -0.05, "x_max": 0.10, "y_min": -0.03, "y_max": 0.03}
        mesh = generate_adaptive_mesh(
            refined_zone=zone,
            local_h=0.005,
            global_h=0.025,
            ratio=1.5
        )
        self.assertTrue(mesh["geometry_valid"])
        self.assertAlmostEqual(mesh["total_area"], 1.0, places=5)
        self.assertGreater(mesh["num_physical_elements"], 1000)
        self.assertEqual(len(mesh["invalid_elements"]), 0)
        self.assertIn("bottom_nodes", mesh["node_sets"])
        self.assertIn("top_nodes", mesh["node_sets"])
        self.assertIn("RP", mesh["node_sets"])
        self.assertGreater(len(mesh["split_node_pairs"]), 0)

        # Test strategies
        strat1 = StructuredCorridorStrategy()
        mesh1 = strat1.generate_mesh(refined_zone=zone)
        self.assertEqual(mesh1["strategy"], "STRUCTURED_CORRIDOR_EXPERIMENTAL")

        strat2 = PandeyKumarNativeStrategy()
        mesh2 = strat2.generate_mesh(refined_zone=zone)
        self.assertEqual(mesh2["strategy"], "PANDEY_KUMAR_ABAQUS_NATIVE")

    def test_05_3layer_uel_deck_rebuilder(self):
        """Test 5: Rebuilding 3-layer UEL deck with full element counts and shear coupling."""
        zone = {"x_min": -0.02, "x_max": 0.02, "y_min": -0.02, "y_max": 0.02}
        mesh = generate_adaptive_mesh(refined_zone=zone, local_h=0.010, global_h=0.025)
        out_inp = self.test_dir / "test_model.inp"
        
        info = build_layered_uel_deck(
            mesh_data=mesh,
            output_path=out_inp,
            job_name="TEST_MODEL",
            step_u1_target=0.001
        )
        self.assertTrue(out_inp.is_file())
        self.assertEqual(info["n_physical_elements"], mesh["num_physical_elements"])
        self.assertEqual(info["n_layered_elements"], 3 * mesh["num_physical_elements"])

        content = out_inp.read_text(encoding="utf-8")
        self.assertIn("*User Element, nodes=4, type=U1", content)
        self.assertIn("*User Element, nodes=4, type=U2", content)
        self.assertIn("*Element, type=CPE4, elset=UMAT_QUAD", content)
        self.assertIn("top_nodes, 1, 1.", content)
        self.assertIn("RP, 1, -1.", content)

    def test_06_state_transfer_and_invariants(self):
        """Test 6: State transfer and thermodynamic invariant audit."""
        src_mesh = generate_adaptive_mesh(
            refined_zone={"x_min": -0.02, "x_max": 0.02, "y_min": -0.02, "y_max": 0.02},
            local_h=0.010, global_h=0.025
        )
        tgt_mesh = generate_adaptive_mesh(
            refined_zone={"x_min": -0.05, "x_max": 0.08, "y_min": -0.03, "y_max": 0.03},
            local_h=0.005, global_h=0.025
        )

        src_nodal_f = {}
        for nid, (x, y) in src_mesh["nodes"].items():
            u1 = (y + 0.5) * 0.01
            d = max(0.0, min(1.0, 0.8 * math.exp(-((x**2 + y**2) / 0.01))))
            src_nodal_f[nid] = {"U1": u1, "U2": 0.0, "U3": d}

        src_h = {eid: (0.0001, 0.0001, 0.0001, 0.0001) for eid in src_mesh["elements"]}

        out_trans_dir = self.test_dir / "transfer_out"
        manifest, val_res = execute_full_state_transfer(
            source_mesh_data=src_mesh,
            source_nodal_fields=src_nodal_f,
            source_h_fields=src_h,
            target_mesh_data=tgt_mesh,
            output_dir=out_trans_dir,
            target_mesh_name="TARGET_TEST",
            handoff_rp_u1=0.0075,
            source_provenance={"test": "source_data"}
        )

        self.assertTrue(val_res.passed)
        self.assertEqual(val_res.metrics["unmapped_nodes"], 0)
        self.assertGreaterEqual(val_res.metrics["target_min_d"], -1e-6)
        self.assertLessEqual(val_res.metrics["target_max_d"], 1.0 + 1e-6)
        self.assertGreaterEqual(val_res.metrics["target_min_H"], 0.0)
        self.assertTrue((out_trans_dir / "STAGE_D_COMMITTED_STATE.bin").is_file())

    def test_07_restart_package_builder(self):
        """Test 7: 4-stage restart input deck and package generation."""
        mesh = generate_adaptive_mesh(
            refined_zone={"x_min": -0.02, "x_max": 0.02, "y_min": -0.02, "y_max": 0.02},
            local_h=0.010, global_h=0.025
        )
        out_pkg_dir = self.test_dir / "restart_pkg"
        pkg = generate_four_stage_restart_package(
            target_mesh_data=mesh,
            cycle_id="cycle_001",
            handoff_u1=0.0075,
            target_u1=0.0100,
            output_dir=out_pkg_dir,
            target_prefix="TARGET_TEST"
        )
        self.assertEqual(pkg["job_name"], "M2ADAPT_CYCLE_001_RESTART")
        self.assertTrue((out_pkg_dir / "M2ADAPT_CYCLE_001_RESTART.inp").is_file())
        self.assertTrue((out_pkg_dir / "M2ADAPT_CYCLE_001_RESTART.pbs").is_file())
        self.assertTrue((out_pkg_dir / "submit_m2adapt_cycle_001_restart.sh").is_file())
        self.assertTrue((out_pkg_dir / "MODE_STAGED.flag").is_file())
        self.assertTrue((out_pkg_dir / "PACKAGE_MANIFEST.json").is_file())

        inp_text = (out_pkg_dir / "M2ADAPT_CYCLE_001_RESTART.inp").read_text(encoding="utf-8")
        self.assertIn("*Step, name=STATE_INSTALL", inp_text)
        self.assertIn("*Step, name=MECH_EQUILIBRATION", inp_text)
        self.assertIn("*Step, name=PHASE_RELEASE", inp_text)
        self.assertIn("*Step, name=CONTINUATION", inp_text)
        self.assertIn("1.0e-14", inp_text)
        self.assertIn("*Controls, parameters=field, field=displacement", inp_text)
        self.assertIn("20", inp_text)

    def test_08_full_pilot_dryrun_cycle(self):
        """Test 8: End-to-end pilot cycle execution in dry-run mode and state semantics."""
        driver = AdaptiveOnlineDriver(
            workspace_root=ROOT,
            dry_run=True
        )
        result = driver.run_pilot_cycle()
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "DRY_RUN_PILOT_ACCEPTED")
        self.assertTrue(result["trigger_evaluation"]["remesh_required"])
        self.assertTrue(result["invariant_audit"]["passed"])
        self.assertIn("restart_inp", result["cryptographic_hashes"])
        self.assertIn("pbs_script", result["cryptographic_hashes"])
        self.assertFalse(result["execution_plan"]["qsub_authorized"])

    def test_09_real_donor_extraction_1390447(self):
        """Test 9: Real donor state extraction from genuine Job 1390447.mmaster02 deck."""
        inp_path = ROOT / "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL.inp"
        curve_path = ROOT / "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL/force_displacement_curve.csv"
        
        self.assertTrue(inp_path.is_file(), f"Missing canonical donor deck: {inp_path}")
        donor = extract_real_donor_state(
            donor_inp_path=inp_path,
            curve_csv_path=curve_path,
            target_frame=17,
            expected_u1=0.010512890294194221,
            job_id="1390447.mmaster02"
        )
        self.assertEqual(donor["provenance"]["job_id"], "1390447.mmaster02")
        self.assertEqual(donor["provenance"]["num_physical_nodes"], 9073)
        self.assertEqual(donor["provenance"]["num_physical_elements"], 8836)
        self.assertEqual(donor["provenance"]["frame"], 17)
        self.assertAlmostEqual(donor["actual_u1_mm"], 0.01051289, places=6)
        self.assertAlmostEqual(donor["d_max"], 0.304318, places=4)
        self.assertFalse(donor["provenance"]["synthetic"])
        self.assertTrue(donor["provenance"]["real_primary_evidence_donor"])
        self.assertGreater(len(donor["h_fields"]), 0)

    def test_10_real_pilot_cycle_generation(self):
        """Test 10: Generate full genuine real-evidence pilot adaptive cycle (REAL_PILOT_CYCLE_001)."""
        driver = AdaptiveOnlineDriver(
            workspace_root=ROOT,
            dry_run=True
        )
        result = driver.run_real_pilot_cycle(
            cycle_id="TEST_REAL_PILOT_001",
            datacheck_only=True
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "DATACHECK_PACKAGE_READY")
        self.assertFalse(result["donor_state"]["synthetic"])
        self.assertEqual(result["donor_state"]["donor_job"], "1390447.mmaster02")
        self.assertTrue(result["invariant_audit"]["passed"])
        self.assertEqual(result["mesh_statistics"]["strategy"], "STRUCTURED_CORRIDOR_EXPERIMENTAL")
        self.assertEqual(result["execution_plan"]["datacheck_mode"], True)

    def test_11_notification_preflight_smoke(self):
        """Test 11: Notification preflight smoke test verifying dual-channel settings without submitting."""
        notif_sh = ROOT / "scripts/hpc/notifications/job_notifications.sh"
        self.assertTrue(notif_sh.is_file())
        
        # Verify email directive format
        from scripts.adaptive_online.restart_builder import APPROVED_EMAIL_DIRECTIVE
        self.assertIn("Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de", APPROVED_EMAIL_DIRECTIVE)
        self.assertIn("pr21vyci@mailserver.tu-freiberg.de", APPROVED_EMAIL_DIRECTIVE)
        self.assertIn("#PBS -M", APPROVED_EMAIL_DIRECTIVE)

    def test_12_same_mesh_identity_state_preservation(self):
        """Test 12: Regression test verifying exact identity state carry-forward and zero healing on unchanged meshes."""
        mesh = generate_adaptive_mesh(
            refined_zone={"x_min": -0.02, "x_max": 0.02, "y_min": -0.02, "y_max": 0.02},
            local_h=0.010, global_h=0.025
        )
        
        # Create arbitrary localized damage profile
        src_nodal_f = {}
        for nid, (x, y) in mesh["nodes"].items():
            u1 = (y + 0.5) * 0.0125
            u2 = 0.001 * math.sin(x)
            d = max(0.0, min(1.0, 0.304318 * math.exp(-((x**2 + y**2) / 0.005))))
            src_nodal_f[nid] = {"U1": u1, "U2": u2, "U3": d}

        src_h = {eid: (0.0123, 0.0456, 0.0789, 0.0011) for eid in mesh["elements"]}

        out_trans_dir = self.test_dir / "same_mesh_transfer_out"
        manifest, val_res = execute_full_state_transfer(
            source_mesh_data=mesh,
            source_nodal_fields=src_nodal_f,
            source_h_fields=src_h,
            target_mesh_data=mesh,
            output_dir=out_trans_dir,
            target_mesh_name="TARGET_SAME_MESH",
            handoff_rp_u1=0.0125,
            source_provenance={"job_id": "test_same_mesh"},
            same_mesh=True
        )

        self.assertTrue(val_res.passed, f"Validation failed: {val_res.summary_text}")
        self.assertTrue(val_res.metrics["same_mesh_identity_transfer"])
        self.assertEqual(val_res.metrics["unmapped_nodes"], 0)
        self.assertEqual(val_res.metrics["unmapped_gps"], 0)
        self.assertEqual(val_res.metrics["max_mapping_residual"], 0.0)
        
        # Verify exact d_max identity (no numerical drop/healing)
        self.assertAlmostEqual(val_res.metrics["target_max_d"], 0.304318, places=6)
        self.assertEqual(val_res.metrics["target_max_d"], val_res.metrics["donor_max_d"])


if __name__ == "__main__":
    unittest.main()
