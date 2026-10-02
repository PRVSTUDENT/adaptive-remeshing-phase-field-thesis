#!/usr/bin/env python3
"""
Automated External-Driver Closed-Loop Adaptive Remeshing Engine.
Orchestrates repeated adaptive cycles during phase-field crack propagation:
  Solve Segment -> Extract Fields -> Remesh Decision -> Generate Mesh ->
  Rebuild 3-Layer UEL -> State Transfer -> Validate Invariants ->
  Assemble 4-Stage Restart -> Continue Propagation -> Repeat
"""

import os
import sys
import math
import json
import argparse
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Add workspace root to sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.adaptive_online.state_machine import AdaptiveStateMachine, AdaptiveState
from scripts.adaptive_online.trigger_engine import evaluate_adaptive_triggers, TriggerResult
from scripts.adaptive_online.mesh_adapter import generate_adaptive_mesh, StructuredCorridorStrategy, PandeyKumarNativeStrategy
from scripts.adaptive_online.deck_rebuilder import build_layered_uel_deck
from scripts.adaptive_online.transfer_pipeline import execute_full_state_transfer, TransferValidationResult
from scripts.adaptive_online.restart_builder import generate_four_stage_restart_package
from scripts.adaptive_online.manifest_manager import CycleManifest, compute_sha256_file
from scripts.adaptive_online.field_extractor import extract_real_donor_state

CANONICAL_REAL_DONOR_INP = ROOT / "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL.inp"
CANONICAL_REAL_DONOR_CURVE = ROOT / "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL/force_displacement_curve.csv"


class AdaptiveOnlineDriver:
    """
    Main controller for automated closed-loop adaptive remeshing.
    """

    def __init__(
        self,
        workspace_root: Path,
        config_path: Optional[Path] = None,
        dry_run: bool = True
    ):
        self.root = Path(workspace_root).resolve()
        self.dry_run = dry_run
        
        # Working directories
        self.state_dir = self.root / "results/adaptive_online/state"
        self.models_dir = self.root / "models/generated/adaptive_online"
        self.results_dir = self.root / "results/adaptive_online"
        
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.state_file = self.state_dir / "ADAPTIVE_DRIVER_STATE.json"
        self.sm = AdaptiveStateMachine(self.state_file)

        # Load or default configuration
        if config_path and Path(config_path).is_file():
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = self._default_config()

        self.sm.set_global("config", self.config)

    def _default_config(self) -> Dict[str, Any]:
        return {
            "pilot_name": "REAL_PILOT_CYCLE_001",
            "material": {
                "E": 210.0,
                "nu": 0.30,
                "Gc": 0.0027,
                "l0": 0.015,
                "park": 1.0e-7,
                "thickness": 1.0
            },
            "mesh_sizing": {
                "local_h": 0.0050,
                "global_h": 0.0250,
                "ratio": 1.5
            },
            "triggers": {
                "d_invade_threshold": 0.05,
                "d_crack_core": 0.30,
                "buffer_multiplier": 2.0
            },
            "simulation": {
                "start_u1": 0.0,
                "final_u1": 0.050,
                "delta_u1_segment": 0.0025,
                "initial_donor_u1": 0.01051289
            },
            "hpc": {
                "cpus": 1,
                "memory": "16gb",
                "walltime": "00:30:00",
                "queue": "entry_imfdfkmq"
            }
        }

    def print_status(self) -> None:
        print("================================================================================")
        print("AUTOMATED ADAPTIVE REMESHING DRIVER STATUS")
        print("================================================================================")
        print(f"Workspace:       {self.root}")
        print(f"Current Cycle:   {self.sm.current_cycle} (Index: {self.sm.cycle_index})")
        print(f"Current State:   {self.sm.current_state}")
        print(f"Dry Run Mode:    {self.dry_run}")
        print(f"State File:      {self.state_file}")
        print(f"Terminal State:  {self.sm.is_terminal()}")
        print(f"Waiting Auth:    {self.sm.is_waiting_for_human()}")
        print("================================================================================")

    def run_pilot_cycle(self) -> Dict[str, Any]:
        """
        Executes a complete Level-1 / Level-2 dry-run pilot cycle:
          1. Generates initial donor model and synthetic/representative cracked state
          2. Evaluates adaptive triggers
          3. Generates target refined mesh
          4. Rebuilds 3-layer UEL deck
          5. Executes nonmatching state transfer
          6. Audits invariants
          7. Builds 4-stage restart package
          8. Emits complete cycle manifest
        """
        cycle_id = self.sm.current_cycle
        print(f"\n>>> Launching Automated Pilot Adaptive Cycle: {cycle_id} (Dry Run: {self.dry_run}) <<<\n")

        cycle_dir = self.models_dir / cycle_id
        cycle_dir.mkdir(parents=True, exist_ok=True)
        manifest = CycleManifest(cycle_id, cycle_dir)

        # ----------------------------------------------------------------------
        # 1. INITIALIZE & DONOR SETUP
        # ----------------------------------------------------------------------
        print("--- Step 1: Initialize Donor State ---")
        self.sm.transition_to(AdaptiveState.INITIALIZE, {"status": "INITIALIZING"}, force=True)

        donor_mesh = generate_adaptive_mesh(
            refined_zone={"x_min": -0.02, "x_max": 0.02, "y_min": -0.02, "y_max": 0.02},
            local_h=0.010,
            global_h=0.025,
            ratio=1.5
        )
        donor_deck_info = build_layered_uel_deck(
            mesh_data=donor_mesh,
            output_path=cycle_dir / "DONOR_MODEL.inp",
            job_name=f"{cycle_id.upper()}_DONOR",
            step_u1_target=0.0075
        )
        print(f"Donor Model: {donor_mesh['num_physical_elements']} physical elements, {donor_mesh['num_physical_nodes']} nodes")
        print(f"Donor Deck:  {donor_deck_info['deck_path']} (SHA: {donor_deck_info['sha256'][:16]}...)")

        donor_nodes = donor_mesh["nodes"]
        donor_elems = donor_mesh["elements"]
        
        donor_nodal_fields: Dict[int, Dict[str, float]] = {}
        donor_h_fields: Dict[int, Tuple[float, float, float, float]] = {}
        donor_phase_dict: Dict[int, float] = {}

        for nid, (x, y) in donor_nodes.items():
            u1_val = (y + 0.5) * 0.0075
            u2_val = 0.0
            dist_crack = math.hypot(x - 0.02, y - 0.01)
            if -0.05 <= x <= 0.05 and abs(y) <= 0.03:
                d_val = max(0.0, min(0.85, 0.85 * math.exp(-((dist_crack / 0.02)**2))))
            else:
                d_val = 0.0
            donor_nodal_fields[nid] = {"U1": u1_val, "U2": u2_val, "U3": d_val}
            donor_phase_dict[nid] = d_val

        for eid, conn in donor_elems.items():
            pts = [donor_nodes[n] for n in conn]
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            d_e = math.hypot(cx - 0.02, cy - 0.01)
            h_base = max(0.0, 0.0005 * math.exp(-((d_e / 0.03)**2)))
            donor_h_fields[eid] = (h_base, h_base, h_base, h_base)

        donor_dmax = max(f["U3"] for f in donor_nodal_fields.values())
        print(f"Donor Crack State: Max damage d_max = {donor_dmax:.4f}, Handoff U1 = 0.0075 mm")

        manifest.set_donor(
            donor_job=f"{cycle_id.upper()}_DONOR",
            donor_frame=10,
            donor_u1=0.0075,
            donor_dmax=donor_dmax,
            donor_inp_sha=donor_deck_info["sha256"],
            synthetic=True
        )

        self.sm.transition_to(AdaptiveState.SEGMENT_READY, {"donor_model": donor_deck_info})
        self.sm.transition_to(AdaptiveState.SEGMENT_SOLVED, {"solver_exit_code": 0, "mock": True})
        self.sm.transition_to(AdaptiveState.FIELDS_EXTRACTED, {"d_max": donor_dmax})

        # ----------------------------------------------------------------------
        # 2. TRIGGER EVALUATION
        # ----------------------------------------------------------------------
        print("\n--- Step 2: Trigger Evaluation ---")
        self.sm.transition_to(AdaptiveState.REMESH_DECISION)
        
        trigger_res: TriggerResult = evaluate_adaptive_triggers(
            nodes=donor_nodes,
            elements=donor_elems,
            nodal_phase=donor_phase_dict,
            l0=0.015,
            d_invade_threshold=0.05,
            d_crack_core=0.30,
            buffer_multiplier=2.0,
            min_element_size=0.0050,
            global_element_size=0.0250,
            current_u1=0.0075,
            final_u1=0.050
        )

        print(f"Trigger Status: Remesh Required = {trigger_res.remesh_required}")
        print(f"Fired Triggers: {trigger_res.fired_triggers}")
        print(f"Rationale:      {trigger_res.rationale}")

        manifest.set_trigger(
            fired_triggers=trigger_res.fired_triggers,
            metrics=trigger_res.metrics,
            rationale=trigger_res.rationale,
            classifications=trigger_res.classifications
        )

        if not trigger_res.remesh_required:
            print("No remeshing needed; continuing on current mesh.")
            self.sm.transition_to(AdaptiveState.NEXT_SEGMENT)
            manifest.save(status="CONTINUE_WITHOUT_REMESH")
            return manifest.data

        # ----------------------------------------------------------------------
        # 3. TARGET MESH GENERATION & UEL DECK REBUILDING
        # ----------------------------------------------------------------------
        print("\n--- Step 3: Target Mesh Generation & Layered Deck Building ---")
        self.sm.transition_to(AdaptiveState.REMESH_GENERATED)

        target_mesh = generate_adaptive_mesh(
            refined_zone=trigger_res.refined_zone,
            local_h=0.0050,
            global_h=0.0250,
            ratio=1.5
        )

        if not target_mesh["geometry_valid"]:
            print(f"ERROR: Generated target mesh failed geometry validation: {target_mesh['invalid_elements']}")
            self.sm.transition_to(AdaptiveState.REMESH_REJECTED)
            manifest.save(status="FAILED_GEOMETRY_VALIDATION")
            return manifest.data

        manifest.set_target_mesh_stats(
            n_phys=target_mesh["num_physical_elements"],
            n_nodes=target_mesh["num_physical_nodes"],
            n_layered=3 * target_mesh["num_physical_elements"],
            h_min=0.0050,
            h_max=0.0250,
            area=target_mesh["total_area"]
        )

        # ----------------------------------------------------------------------
        # 4. STATE TRANSFER & INVARIANT VALIDATION
        # ----------------------------------------------------------------------
        print("\n--- Step 4: Nonmatching State Transfer ---")
        self.sm.transition_to(AdaptiveState.STATE_TRANSFERRED)

        source_mesh_wrapper = {
            "nodes": donor_nodes,
            "elements": donor_elems
        }
        source_prov = {
            "donor_cycle": cycle_id,
            "donor_u1_mm": 0.0075,
            "donor_dmax": donor_dmax
        }

        target_prefix = f"TARGET_{cycle_id.upper()}"
        transfer_manifest, val_result = execute_full_state_transfer(
            source_mesh_data=source_mesh_wrapper,
            source_nodal_fields=donor_nodal_fields,
            source_h_fields=donor_h_fields,
            target_mesh_data=target_mesh,
            output_dir=cycle_dir,
            target_mesh_name=target_prefix,
            handoff_rp_u1=0.0075,
            source_provenance=source_prov,
            enable_phase_projection=False
        )

        print(f"State Transfer Status:")
        print(f"  {val_result.summary_text}")
        print(f"  Target d range: [{val_result.metrics['target_min_d']:.4f}, {val_result.metrics['target_max_d']:.4f}]")
        print(f"  Target H range: [{val_result.metrics['target_min_H']:.4e}, {val_result.metrics['target_max_H']:.4e}]")
        print(f"  Unmapped Nodes: {val_result.metrics.get('unmapped_nodes', 0)}")

        manifest.set_transfer_audit(val_result.metrics)

        if not val_result.passed:
            print(f"ERROR: Transfer invariant validation failed: {val_result.violations}")
            self.sm.transition_to(AdaptiveState.TRANSFER_VALIDATED)
            self.sm.transition_to(AdaptiveState.TRANSFER_REJECTED)
            manifest.save(status="TRANSFER_REJECTED")
            return manifest.data

        self.sm.transition_to(AdaptiveState.TRANSFER_VALIDATED)

        # ----------------------------------------------------------------------
        # 5. ASSEMBLE FOUR-STAGE RESTART PACKAGE
        # ----------------------------------------------------------------------
        print("\n--- Step 5: Assemble 4-Stage Restart Package ---")
        target_u1_endpoint = 0.0075 + self.config["simulation"]["delta_u1_segment"]
        manifest.set_segment(u1_start=0.0075, u1_end=target_u1_endpoint)

        restart_package = generate_four_stage_restart_package(
            target_mesh_data=target_mesh,
            cycle_id=cycle_id,
            handoff_u1=0.0075,
            target_u1=target_u1_endpoint,
            output_dir=cycle_dir,
            target_prefix=target_prefix,
            source_job_id=f"{cycle_id.upper()}_DONOR",
            cpus=self.config["hpc"]["cpus"],
            memory=self.config["hpc"]["memory"],
            walltime=self.config["hpc"]["walltime"],
            queue=self.config["hpc"]["queue"]
        )

        job_name = restart_package["job_name"]

        files_to_hash = {
            "restart_inp": cycle_dir / f"{job_name}.inp",
            "uel_source": cycle_dir / "f44_mixed_uel_restart_stateinit.for",
            "pbs_script": cycle_dir / f"{job_name}.pbs",
            "submit_wrapper": cycle_dir / f"submit_{job_name.lower()}.sh",
            "primary_state_csv": cycle_dir / f"{target_prefix}_PRIMARY_STATE.csv",
            "state_install_inp": cycle_dir / f"{target_prefix}_STATE_INSTALL_BOUNDARY.inp",
            "u3_only_inp": cycle_dir / f"{target_prefix}_U3_ONLY_BOUNDARY.inp",
            "committed_binary": cycle_dir / "STAGE_D_COMMITTED_STATE.bin"
        }
        manifest.record_hashes(files_to_hash)

        solver_cmd = f"abaqus job={job_name} input={job_name}.inp user=f44_mixed_uel_restart_stateinit.for cpus=1 interactive"
        pbs_cmd = f"qsub {job_name}.pbs"
        manifest.set_execution_plan(solver_cmd, pbs_cmd, dry_run=self.dry_run)

        self.sm.transition_to(AdaptiveState.PACKAGE_GENERATED, {"restart_package": restart_package})

        # Dry run / Governance gate
        if self.dry_run:
            print("\n[DRY RUN]: Stopping prior to solver execution or PBS submission.")
            print(f"Exact Solver Command (would run): {solver_cmd}")
            print(f"Exact PBS Command (would run):    {pbs_cmd}")
            print(f"Package Manifest Path:            {manifest.manifest_path}")
            self.sm.transition_to(AdaptiveState.DRY_RUN_ACCEPTED, {"dry_run_completed": True})
            self.sm.transition_to(AdaptiveState.NEXT_SEGMENT)
            manifest.save(status="DRY_RUN_PILOT_ACCEPTED")
        else:
            print("\n[HUMAN AUTHORIZATION GATE]: Production PBS submission requires explicit authorization.")
            self.sm.transition_to(AdaptiveState.WAITING_FOR_HUMAN_AUTHORIZATION)
            manifest.save(status="WAITING_FOR_HUMAN_AUTHORIZATION")

        print("\n================================================================================")
        print(f"PILOT ADAPTIVE CYCLE {cycle_id} COMPLETED SUCCESSFULLY IN DRY-RUN MODE")
        print("================================================================================")
        return manifest.data

    def run_real_pilot_cycle(
        self,
        cycle_id: str = "REAL_PILOT_CYCLE_001",
        donor_inp_path: Optional[Path] = None,
        curve_csv_path: Optional[Path] = None,
        datacheck_only: bool = True
    ) -> Dict[str, Any]:
        """
        Executes genuine real-evidence pilot adaptive cycle:
          Ingests real donor job 1390447.mmaster02 Frame 17 (u1=0.01051289 mm, d_max=0.304318),
          evaluates multi-criteria triggers, builds target adaptive mesh, executes
          nonmatching state transfer, validates invariants, and generates sealed 4-stage restart package.
        """
        print(f"\n>>> Launching Genuine Real-Pilot Adaptive Cycle: {cycle_id} (Datacheck Mode: {datacheck_only}) <<<\n")

        inp_target = donor_inp_path or CANONICAL_REAL_DONOR_INP
        curve_target = curve_csv_path or CANONICAL_REAL_DONOR_CURVE

        cycle_dir = self.models_dir / cycle_id.lower()
        cycle_dir.mkdir(parents=True, exist_ok=True)
        manifest = CycleManifest(cycle_id, cycle_dir)

        # 1. Real Donor Ingestion
        print(f"--- Step 1: Extract Genuine Donor State from {inp_target.name} ---")
        self.sm.transition_to(AdaptiveState.INITIALIZE, {"cycle_id": cycle_id}, force=True)

        donor_data = extract_real_donor_state(
            donor_inp_path=inp_target,
            curve_csv_path=curve_target,
            target_frame=17,
            expected_u1=0.010512890294194221,
            job_id="1390447.mmaster02"
        )

        donor_prov = donor_data["provenance"]
        donor_u1 = donor_data["actual_u1_mm"]
        donor_dmax = donor_data["d_max"]

        print(f"Real Donor Extracted:")
        print(f"  Source Job:        {donor_prov['job_id']}")
        print(f"  Physical Nodes:    {donor_prov['num_physical_nodes']}")
        print(f"  Physical Quads:    {donor_prov['num_physical_elements']}")
        print(f"  Handoff Frame:     {donor_prov['frame']}")
        print(f"  Handoff U1:        {donor_u1:.8f} mm")
        print(f"  Handoff RF1:       {donor_prov['rf1_kN']:.6f} kN")
        print(f"  Handoff Max d:     {donor_dmax:.6f}")
        print(f"  Donor Deck SHA256: {donor_prov['donor_inp_sha256']}")

        manifest.set_donor(
            donor_job=donor_prov["job_id"],
            donor_frame=donor_prov["frame"],
            donor_u1=donor_u1,
            donor_dmax=donor_dmax,
            donor_inp_sha=donor_prov["donor_inp_sha256"],
            synthetic=False,
            provenance_details=donor_prov
        )

        self.sm.transition_to(AdaptiveState.SEGMENT_READY, {"donor_provenance": donor_prov})
        self.sm.transition_to(AdaptiveState.SEGMENT_SOLVED, {"donor_job": donor_prov["job_id"], "exit_code": 0})
        self.sm.transition_to(AdaptiveState.FIELDS_EXTRACTED, {"d_max": donor_dmax, "u1": donor_u1})

        # 2. Trigger Evaluation
        print("\n--- Step 2: Trigger Evaluation on Real Donor State ---")
        self.sm.transition_to(AdaptiveState.REMESH_DECISION)

        trigger_res: TriggerResult = evaluate_adaptive_triggers(
            nodes=donor_data["nodes"],
            elements=donor_data["elements"],
            nodal_phase=donor_data["nodal_phase"],
            l0=0.015,
            d_invade_threshold=0.05,
            d_crack_core=0.30,
            buffer_multiplier=2.0,
            min_element_size=0.0050,
            global_element_size=0.0250,
            current_u1=donor_u1,
            final_u1=0.050
        )

        print(f"Trigger Status: Remesh Required = {trigger_res.remesh_required}")
        print(f"Fired Triggers: {trigger_res.fired_triggers}")
        print(f"Rationale:      {trigger_res.rationale}")

        manifest.set_trigger(
            fired_triggers=trigger_res.fired_triggers,
            metrics=trigger_res.metrics,
            rationale=trigger_res.rationale,
            classifications=trigger_res.classifications
        )

        # 3. Target Mesh Generation
        print("\n--- Step 3: Target Mesh Generation (STRUCTURED_CORRIDOR_EXPERIMENTAL) ---")
        self.sm.transition_to(AdaptiveState.REMESH_GENERATED)

        target_mesh = generate_adaptive_mesh(
            refined_zone=trigger_res.refined_zone,
            local_h=0.0050,
            global_h=0.0250,
            ratio=1.5
        )

        if not target_mesh["geometry_valid"]:
            print(f"ERROR: Generated target mesh failed geometry validation: {target_mesh['invalid_elements']}")
            self.sm.transition_to(AdaptiveState.REMESH_REJECTED)
            manifest.save(status="FAILED_GEOMETRY_VALIDATION")
            return manifest.data

        print(f"Target Mesh Statistics:")
        print(f"  Physical Elements: {target_mesh['num_physical_elements']}")
        print(f"  Physical Nodes:    {target_mesh['num_physical_nodes']}")
        print(f"  Layered Elements:  {3 * target_mesh['num_physical_elements']}")
        print(f"  Domain Area:       {target_mesh['total_area']:.8f} mm^2")
        print(f"  Geometry Valid:    {target_mesh['geometry_valid']}")

        manifest.set_target_mesh_stats(
            n_phys=target_mesh["num_physical_elements"],
            n_nodes=target_mesh["num_physical_nodes"],
            n_layered=3 * target_mesh["num_physical_elements"],
            h_min=0.0050,
            h_max=0.0250,
            area=target_mesh["total_area"],
            strategy="STRUCTURED_CORRIDOR_EXPERIMENTAL"
        )

        # 4. State Transfer & Invariant Audit
        print("\n--- Step 4: Nonmatching State Transfer & Thermodynamic Invariant Audit ---")
        self.sm.transition_to(AdaptiveState.STATE_TRANSFERRED)

        source_mesh_wrapper = {
            "nodes": donor_data["nodes"],
            "elements": donor_data["elements"]
        }
        target_prefix = f"TARGET_{cycle_id.upper()}"
        transfer_manifest, val_result = execute_full_state_transfer(
            source_mesh_data=source_mesh_wrapper,
            source_nodal_fields=donor_data["nodal_fields"],
            source_h_fields=donor_data["h_fields"],
            target_mesh_data=target_mesh,
            output_dir=cycle_dir,
            target_mesh_name=target_prefix,
            handoff_rp_u1=donor_u1,
            source_provenance=donor_prov,
            enable_phase_projection=False
        )

        print(f"State Transfer Invariant Status:")
        print(f"  {val_result.summary_text}")
        print(f"  Target d: [{val_result.metrics['target_min_d']:.4f}, {val_result.metrics['target_max_d']:.4f}]")
        print(f"  Target H: [{val_result.metrics['target_min_H']:.4e}, {val_result.metrics['target_max_H']:.4e}]")
        print(f"  Unmapped Nodes: {val_result.metrics.get('unmapped_nodes', 0)}")

        manifest.set_transfer_audit(val_result.metrics)

        if not val_result.passed:
            print(f"ERROR: State transfer invariant validation failed: {val_result.violations}")
            self.sm.transition_to(AdaptiveState.TRANSFER_VALIDATED)
            self.sm.transition_to(AdaptiveState.TRANSFER_REJECTED)
            manifest.save(status="TRANSFER_REJECTED")
            return manifest.data

        self.sm.transition_to(AdaptiveState.TRANSFER_VALIDATED)

        # 5. Assemble 4-Stage Restart Package
        print("\n--- Step 5: Assemble 4-Stage Restart Package ---")
        target_u1_endpoint = donor_u1 + 0.0025 # Continuation segment +2.5 um
        manifest.set_segment(u1_start=donor_u1, u1_end=target_u1_endpoint)

        restart_package = generate_four_stage_restart_package(
            target_mesh_data=target_mesh,
            cycle_id=cycle_id,
            handoff_u1=donor_u1,
            target_u1=target_u1_endpoint,
            output_dir=cycle_dir,
            target_prefix=target_prefix,
            source_job_id=donor_prov["job_id"],
            cpus=1,
            memory="16gb",
            walltime="00:30:00" if datacheck_only else "01:00:00",
            queue="entry_imfdfkmq",
            datacheck_mode=datacheck_only
        )

        job_name = restart_package["job_name"]
        files_to_hash = {
            "restart_inp": cycle_dir / f"{job_name}.inp",
            "uel_source": cycle_dir / "f44_mixed_uel_restart_stateinit.for",
            "pbs_script": cycle_dir / f"{job_name}.pbs",
            "submit_wrapper": cycle_dir / f"submit_{job_name.lower()}.sh",
            "primary_state_csv": cycle_dir / f"{target_prefix}_PRIMARY_STATE.csv",
            "state_install_inp": cycle_dir / f"{target_prefix}_STATE_INSTALL_BOUNDARY.inp",
            "u3_only_inp": cycle_dir / f"{target_prefix}_U3_ONLY_BOUNDARY.inp",
            "committed_binary": cycle_dir / "STAGE_D_COMMITTED_STATE.bin"
        }
        manifest.record_hashes(files_to_hash)

        exec_cmd = "abaqus datacheck" if datacheck_only else "abaqus"
        solver_cmd = f"{exec_cmd} job={job_name} input={job_name}.inp user=f44_mixed_uel_restart_stateinit.for cpus=1 interactive"
        pbs_cmd = f"qsub {job_name}.pbs"
        manifest.set_execution_plan(solver_cmd, pbs_cmd, dry_run=False, datacheck_mode=datacheck_only)

        self.sm.transition_to(AdaptiveState.PACKAGE_GENERATED, {"restart_package": restart_package})

        if datacheck_only:
            manifest.save(status="DATACHECK_PACKAGE_READY")
            print(f"\nReal-Pilot Datacheck Package Assembled and Frozen:")
            print(f"  Package Dir:    {cycle_dir}")
            print(f"  Job Name:       {job_name}")
            print(f"  Restart Deck:   {cycle_dir / f'{job_name}.inp'}")
            print(f"  PBS Script:     {cycle_dir / f'{job_name}.pbs'}")
            print(f"  Submit Wrapper: {cycle_dir / f'submit_{job_name.lower()}.sh'}")
            print(f"  Input SHA256:   {restart_package['hashes']['input_deck_sha256']}")
            print(f"  UEL SHA256:     {restart_package['hashes']['uel_sha256']}")
            print(f"  PBS SHA256:     {restart_package['hashes']['pbs_script_sha256']}")
            print(f"  Wrapper SHA256: {restart_package['hashes']['wrapper_sha256']}")
        else:
            manifest.save(status="PRODUCTION_RESTART_PACKAGE_READY")

        return manifest.data


def main():
    parser = argparse.ArgumentParser(description="Automated Closed-Loop Adaptive Remeshing Driver")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Execute in dry-run mode (default: True)")
    parser.add_argument("--pilot", action="store_true", help="Run Level-1/Level-2 complete pilot cycle")
    parser.add_argument("--real-pilot", action="store_true", help="Run genuine real-donor pilot adaptive cycle")
    parser.add_argument("--status", action="store_true", help="Print current driver status")
    parser.add_argument("--config", type=Path, help="Path to run configuration JSON")
    args = parser.parse_args()

    driver = AdaptiveOnlineDriver(workspace_root=ROOT, config_path=args.config, dry_run=args.dry_run)

    if args.status:
        driver.print_status()
        return 0

    if args.pilot:
        driver.run_pilot_cycle()
        return 0

    if args.real_pilot:
        driver.run_real_pilot_cycle(datacheck_only=True)
        return 0

    driver.print_status()
    print("Use --pilot or --real-pilot to run automated adaptive remeshing cycles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
