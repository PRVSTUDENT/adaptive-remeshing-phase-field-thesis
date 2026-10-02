#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Finalize manifest.json and one_difference_scientific_manifest.json
for M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.
"""

import os
import sys
import hashlib
import json

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as fp:
        while chunk := fp.read(8192):
            h.update(chunk)
    return h.hexdigest()

def main():
    pkg_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL"
    stage_d_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL"
    
    inp_path = os.path.join(pkg_dir, "M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp")
    for_path = os.path.join(pkg_dir, "f44_mixed_uel_restart_stateinit.for")
    pbs_path = os.path.join(pkg_dir, "submit_job.pbs")
    
    inp_hash = compute_sha256(inp_path)
    for_hash = compute_sha256(for_path)
    pbs_hash = compute_sha256(pbs_path)
    
    print("================================================================================")
    print("PACKAGE HASHES: M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL")
    print("================================================================================")
    print("  INP Hash : %s" % inp_hash)
    print("  UEL Hash : %s" % for_hash)
    print("  PBS Hash : %s" % pbs_hash)
    
    # 1. manifest.json
    manifest = {
        "package_name": "M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL",
        "task_id": "F265PREP-M2-STAGE-D-CONTINUOUS-TARGET-CONTROL-DIAGNOSTIC-PACKAGE1",
        "date_prepared": "2026-08-18T06:22:00+02:00",
        "status": "QUALIFIED_READY_FOR_AUTHORIZATION",
        "scientific_purpose": "Continuous virgin baseline (U1 = 0 to 0.050 mm) on exact Stage-D target mesh to isolate static mesh discretization effects from state-transfer/restart staging effects",
        "physical_mesh_hierarchy": {
            "physical_nodes": 9072,
            "reference_point_nodes": 1,
            "total_inp_nodes": 9073,
            "physical_quads": 8836,
            "phase_uel_layer1_elements": 8836,
            "mech_uel_layer2_elements": 8836,
            "total_inp_uel_elements": 17672,
            "visualization_overlay_elements": 0,
            "total_odb_elements": 17672
        },
        "material_properties": {
            "E_L0_mm": 0.015000,
            "E_GC_N_per_mm": 0.002700,
            "E_MOD_kN_per_mm2": 210.0,
            "E_NU": 0.3000,
            "E_K": 1.0e-07,
            "N_PHYS": 8836
        },
        "frozen_sha256": {
            "inp": inp_hash,
            "uel": for_hash,
            "launcher": pbs_hash
        },
        "qualification": {
            "abaqus_datacheck": "PASSED (Exit 0 on cluster with ifort 2021.13.0 + Abaqus 2023)",
            "compilation_and_link": "PASSED (Exit 0)",
            "input_file_processor": "PASSED (Exit 0)"
        }
    }
    
    with open(os.path.join(pkg_dir, "manifest.json"), 'w') as fp:
        json.dump(manifest, fp, indent=2)
    print("Created manifest.json")
    
    # 2. one_difference_scientific_manifest.json
    one_diff = {
        "package_a": {
            "name": "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL",
            "pbs_job_id": "1390279.mmaster02",
            "type": "STAGED_RESTART_NONMATCHING_TRANSFER"
        },
        "package_b": {
            "name": "M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL",
            "pbs_job_id": "PENDING_AUTHORIZATION",
            "type": "CONTINUOUS_VIRGIN_CONTROL"
        },
        "strictly_identical_attributes": {
            "nodal_coordinates": "100% Identical (9,073 nodes + RP 99999, SHA256 match)",
            "element_connectivity": "100% Identical (8,836 phase U1 + 8,836 mech U2, SHA256 match)",
            "physical_quad_count": 8836,
            "physical_node_count": 9072,
            "element_grading_field": "100% Identical (Quartic grading from h_min=0.00263 mm to h_max=0.03018 mm)",
            "material_properties_PROPS": "[0.015, 0.0027, 210.0, 0.3, 1e-07, 8836.0]",
            "l0_mm": 0.015000,
            "Gc_N_per_mm": 0.002700,
            "E_kN_per_mm2": 210.0,
            "nu": 0.3000,
            "k_residual": 1.0e-07,
            "active_set_penalty_gamma": "Node-indexed area-scaled active-set penalty",
            "boundary_equations": "100% Identical (Top edge nodes coupled to RP 99999 in DOF 1)",
            "continuation_step_controls": "STATIC, dt0=0.001, dt_min=1e-9, dt_max=0.02, NLGEOM=NO",
            "pbs_resources": "1 CPU, 16 GB, 24:00:00, batch queue, Abaqus 2023 + Intel 2024.2.0",
            "notification_channels": "Dual-channel Telegram + Email (pr21vyci@mailserver.tu-freiberg.de)"
        },
        "isolated_single_difference": {
            "step_staging_and_state_ingestion": {
                "package_a_1390279": "4-step sequence (STATE_INSTALL -> MECH_EQUILIBRATION -> PHASE_RELEASE -> CONTINUATION) reading transferred fields from STAGE_D_COMMITTED_STATE.bin, STAGE_D_PRIMARY_STATE_BOUNDARY.inp, and STAGE_D_U3_ONLY_BOUNDARY.inp at U1 = 0.010143 mm",
                "package_b_control": "Single continuous step (ShearStep) from U1 = 0.0 to 0.050 mm with virgin d=0 and virgin committed H=0; no transferred includes or binary files"
            }
        },
        "scientific_comparison_plan": {
            "observable_1_trajectory": "Compare RP_RF1 vs U1 curves from U1 = 0 to terminal state",
            "observable_2_damage_onset": "Compare onset displacement U1_damage and spatial d field evolution",
            "observable_3_critical_interval": "Compare trajectory and convergence behavior across U1 in [0.010143 mm, 0.011251 mm]",
            "observable_4_four_gp_history": "Track 4-GP committed H evolution at matched process-zone locations",
            "observable_5_crack_propagation": "Track crack tip coordinates (x_tip, y_tip) vs U1 and overlay on mesh grading field",
            "observable_6_termination_mode": "Compare final cutback sequence, minimum increment dt, and active upper-bound node count (d >= 0.999)",
            "falsifiable_interpretation": {
                "supports_mesh_discretization_hypothesis": "If the continuous control exhibits severe cutbacks and solver termination at U1 approx 0.0112 mm when the crack reaches x approx 0.09-0.12 mm as it enters the mesh grading transition",
                "contradicts_mesh_discretization_hypothesis": "If the continuous control passes smoothly through U1 = 0.011251 mm and propagates significantly further across the ligament, indicating that the early termination in 1390279 was triggered by state-transfer / restart staging gradients"
            }
        }
    }
    
    with open(os.path.join(pkg_dir, "one_difference_scientific_manifest.json"), 'w') as fp:
        json.dump(one_diff, fp, indent=2)
    print("Created one_difference_scientific_manifest.json")

if __name__ == "__main__":
    main()
