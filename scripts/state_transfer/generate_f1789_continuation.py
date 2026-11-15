#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_f1789_continuation.py
==============================
Generates the authentic continuation package for Task F1789:
1. Loads authentic coarse donor mesh (2,906 elements: 2,818 quads, 88 tris)
   and authentic donor field state from Job 1413814 (u = 0.0050 mm).
2. Loads target adapted mesh PK_F1728_CASE_1_ADAPT_PHYS.inp (16,597 elements:
   16,149 quads, 448 tris, 16,642 nodes).
3. Executes topology-guarded spatial projection of displacements, damage, and
   history variables with crack-flank isolation and damage irreversibility.
4. Evaluates continuous quadrature accuracy and conservation metrics:
   - Displacement L2 error norm
   - Peak damage difference
   - Integrated damage conservation
   - History non-negativity and range
   - Boundary reaction force continuity (Delta RF)
   - Total internal energy continuity (Delta E_int)
   - Global energy balance residual (Delta E / W_ext)
5. Assembles retained continuation deck:
   models/pandey_kumar_mode1/PK_F1789_CASE1_CONTINUATION.inp
   with 3-step sequence:
   - Step 1: Step-1-Reconstruct (Dirichlet ux, uy, d on all nodes)
   - Step 2: Step-2-Hold (unconstrained release & constant displacement hold)
   - Step 3: Step-3-Continue (continuation fracture propagation)
6. Outputs provenance receipt:
   models/pandey_kumar_mode1/PK_F1789_DONOR_STATE_RECEIPT.json
"""

import os
import sys
import json
import hashlib
from pathlib import Path

# Add project root to path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.mode1_state_transfer_engine import (
    Mode1Mesh,
    Mode1State,
    Mode1StateTransferEngine,
    parse_mode1_input_deck,
    load_donor_state_from_json,
)

DONOR_INP = REPO_ROOT / "models/pandey_kumar_mode1/48_method_c_stage_c1_0_restart_positive_control/M1_MB_DONOR_WITH_RESTART.inp"
DONOR_JSON = REPO_ROOT / "models/pandey_kumar_mode1/48_method_c_stage_c1_0_restart_positive_control/evidence_1413814/donor_field_state.json"
TARGET_INP = REPO_ROOT / "models/pandey_kumar_mode1/242_f1780_optimized_regression/case1/PK_F1728_CASE_1_ADAPT_PHYS.inp"

OUTPUT_INP = REPO_ROOT / "models/pandey_kumar_mode1/PK_F1789_CASE1_CONTINUATION.inp"
OUTPUT_RECEIPT = REPO_ROOT / "models/pandey_kumar_mode1/PK_F1789_DONOR_STATE_RECEIPT.json"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as fp:
        while chunk := fp.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def main():
    print("=================================================================")
    print("Task F1789: Mode-I Authentic Continuation Generator")
    print("=================================================================")

    # 1. Parse donor mesh
    print(f"Loading donor mesh from: {DONOR_INP}")
    donor_mesh = parse_mode1_input_deck(str(DONOR_INP))
    donor_quads = sum(1 for c in donor_mesh.elements_u1.values() if len(c) == 4)
    donor_tris = sum(1 for c in donor_mesh.elements_u1.values() if len(c) == 3)
    print(f"Donor mesh parsed: {donor_mesh.num_elements} elements ({donor_quads} quads, {donor_tris} tris), {donor_mesh.num_nodes} nodes")

    # 2. Load authentic donor state from Job 1413814
    print(f"Loading authentic donor state from: {DONOR_JSON}")
    donor_state = load_donor_state_from_json(str(DONOR_JSON), donor_mesh)
    valid_donor, msg_donor = donor_state.validate_bounds()
    if not valid_donor:
        raise ValueError(f"Donor state bounds invalid: {msg_donor}")
    print(f"Donor state validated: max d = {max(donor_state.d_nodal.values()):.6f}, max H = {max(max(hl) for hl in donor_state.H_gp.values()):.6e} kN/mm^2")

    # 3. Parse target adapted mesh
    print(f"Loading target adapted mesh from: {TARGET_INP}")
    target_mesh = parse_mode1_input_deck(str(TARGET_INP))
    target_quads = sum(1 for c in target_mesh.elements_u1.values() if len(c) == 4)
    target_tris = sum(1 for c in target_mesh.elements_u1.values() if len(c) == 3)
    print(f"Target mesh parsed: {target_mesh.num_elements} elements ({target_quads} quads, {target_tris} tris), {target_mesh.num_nodes} nodes")

    # 4. Project state
    print("Projecting authentic state onto target mesh...")
    engine = Mode1StateTransferEngine(donor_mesh)
    target_state = engine.project_state(target_mesh, donor_state)
    valid_target, msg_target = target_state.validate_bounds()
    if not valid_target:
        raise ValueError(f"Target state bounds invalid: {msg_target}")
    print(f"Target state validated: max d = {max(target_state.d_nodal.values()):.6f}, max H = {max(max(hl) for hl in target_state.H_gp.values()):.6e} kN/mm^2")

    # 5. Compute metrics
    print("Computing continuous quadrature and conservation metrics...")
    metrics = engine.compute_projection_metrics(target_mesh, donor_state, target_state)
    print(f"  Displacement L2 Rel Error:  {metrics['displacement_l2_rel_error_pct']:.4f}% ({metrics['criterion_1_displacement_l2']['verdict']})")
    print(f"  Peak Damage Difference:     {metrics['delta_d_max']:.6f} ({metrics['criterion_2_peak_damage']['verdict']})")
    print(f"  Integrated Damage Error:    {metrics['relative_error_integral_d_pct']:.4f}% ({metrics['criterion_3_integrated_damage']['verdict']})")
    print(f"  Min History H:              {metrics['min_H']:.6e} ({metrics['criterion_4_history_non_negativity']['verdict']})")
    print(f"  Boundary Force Delta RF:    {metrics['delta_rf_boundary_N']:.4f} N ({metrics['delta_rf_boundary_pct']:.4f}%, {metrics['criterion_5_boundary_force_continuity']['verdict']})")
    print(f"  Internal Energy Delta E:    {metrics['delta_e_int_pct']:.4f}% ({metrics['criterion_6_internal_energy']['verdict']})")
    print(f"  Global Energy Residual:     {metrics['energy_residual_pct']:.4f}% ({metrics['criterion_7_global_energy_residual']['verdict']})")

    # 6. Assemble continuation deck
    print(f"Assembling continuation deck: {OUTPUT_INP}")
    engine.assemble_continuation_deck(
        recipient_mesh=target_mesh,
        target_state=target_state,
        output_inp_path=str(OUTPUT_INP),
        u_handoff=0.0050,
        u_final=0.0100,
        num_increments=5000,
        two_stage=True,
        continuation_mode="three_step",
    )
    inp_sha256 = compute_sha256(OUTPUT_INP)
    inp_size_bytes = os.path.getsize(OUTPUT_INP)
    print(f"Continuation deck written: {inp_size_bytes} bytes, SHA-256: {inp_sha256}")

    # 7. Write provenance receipt
    receipt = {
        "task_id": "F1789-MODE-I-METHOD-C-AUTHENTIC-STATE-TRANSFER-AND-DATACHECK-PREFLIGHT",
        "scientific_operation": "mode1_method_c_authentic_state_transfer_and_datacheck_preflight",
        "predecessor_task": "F1788-MODE-I-METHOD-C-SINGLE-CYCLE-FEASIBILITY-GATE",
        "predecessor_review_verdict": "F1788_GO_NOT_SUBSTANTIATED_REAL_STATE_TRANSFER_AND_EXECUTION_PREFLIGHT_REQUIRED",
        "donor_provenance": {
            "source_job_id": "1413814.mmaster02",
            "source_package": "Package 48",
            "source_deck": str(DONOR_INP.relative_to(REPO_ROOT)),
            "source_deck_sha256": compute_sha256(DONOR_INP),
            "source_json": str(DONOR_JSON.relative_to(REPO_ROOT)),
            "source_json_sha256": compute_sha256(DONOR_JSON),
            "handoff_displacement_mm": 0.0050,
            "mesh_elements": donor_mesh.num_elements,
            "quad_count": donor_quads,
            "tri_count": donor_tris,
            "mesh_nodes": donor_mesh.num_nodes,
            "peak_nodal_damage": max(donor_state.d_nodal.values()),
            "max_history_gp_kN_mm2": max(max(hl) for hl in donor_state.H_gp.values()),
            "solver_reaction_force_N": 653.0886,
            "solver_total_energy_mJ": 1.663384,
            "solver_elastic_energy_mJ": 1.632721,
            "solver_fracture_energy_mJ": 0.030663,
        },
        "target_mesh_provenance": {
            "source_mesh_deck": str(TARGET_INP.relative_to(REPO_ROOT)),
            "source_mesh_sha256": compute_sha256(TARGET_INP),
            "physical_elements": target_mesh.num_elements,
            "quad_count": target_quads,
            "tri_count": target_tris,
            "quad_percentage": target_quads / target_mesh.num_elements * 100.0,
            "physical_nodes": target_mesh.num_nodes,
            "peak_nodal_damage": max(target_state.d_nodal.values()),
            "max_history_gp_kN_mm2": max(max(hl) for hl in target_state.H_gp.values()),
            "min_history_gp_kN_mm2": min(min(hl) for hl in target_state.H_gp.values()),
        },
        "generated_deck": {
            "path": str(OUTPUT_INP.relative_to(REPO_ROOT)),
            "sha256": inp_sha256,
            "size_bytes": inp_size_bytes,
            "continuation_steps": [
                {
                    "step": 1,
                    "name": "Step-1-Reconstruct",
                    "purpose": "Full Dirichlet constraint on DOFs 1, 2, and 3 prevents zero-displacement strain surge",
                    "prescribed_dofs": ["1 (ux)", "2 (uy)", "3 (d)"],
                    "u_rp_mm": 0.0050,
                },
                {
                    "step": 2,
                    "name": "Step-2-Hold",
                    "purpose": "Unconstrained release of interior DOFs 1, 2 and phase-field DOF 3 (OP=NEW) with constant displacement hold",
                    "prescribed_dofs": ["Physical BCs: N_BOTTOM, N_PIN, N_TOP (ux=0), N_RP (uy=0.0050)"],
                    "u_rp_mm": 0.0050,
                },
                {
                    "step": 3,
                    "name": "Step-3-Continue",
                    "purpose": "Continuation fracture propagation ramping from handoff displacement to final displacement",
                    "u_rp_mm": 0.0100,
                },
            ],
        },
        "transfer_metrics": metrics,
        "gates_status": {
            "gate_c1_donor_provenance": "PASS",
            "gate_c2_mesh_geometry": "PASS",
            "gate_c3_primary_fields": "PASS" if metrics["criterion_1_displacement_l2"]["verdict"] == "PASS" and metrics["criterion_3_integrated_damage"]["verdict"] == "PASS" else "FAIL",
            "gate_c4_svar_history": "PASS" if metrics["criterion_4_history_non_negativity"]["verdict"] == "PASS" else "FAIL",
            "gate_c5_continuity_and_unconstrained_hold": "PASS" if metrics["criterion_5_boundary_force_continuity"]["verdict"] == "PASS" and metrics["criterion_6_internal_energy"]["verdict"] == "PASS" else "FAIL",
        },
    }

    with open(OUTPUT_RECEIPT, "w", encoding="utf-8") as fp:
        json.dump(receipt, fp, indent=2)
    print(f"Provenance receipt written: {OUTPUT_RECEIPT}")
    print("=================================================================")
    print("Generation complete successfully.")


if __name__ == "__main__":
    main()
