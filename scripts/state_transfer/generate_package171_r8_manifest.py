#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_package171_r8_manifest.py
==================================
Generates PACKAGE_MANIFEST.json for Package 171-R8.
"""

import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
pkg = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r8_c3_0_adaptive_reequilibration"

files = {}
for p in sorted(pkg.iterdir()):
    if p.is_file() and p.name != "PACKAGE_MANIFEST.json":
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        files[p.name] = h

manifest = {
    "package_name": "mode1_c6_package171_r8_c3_0_adaptive_reequilibration",
    "protocol_version": 2,
    "description": "Package 171-R8: Mode-I C6 Stage C3-0 genuine coupled PDAS re-equilibration with two-phase safeguarded relaxation: Stage 1 omega_d = 0.50, Stage 2 omega_d = 0.85 activated upon compound active-set condition (|A_k| <= 500, |Delta A_k| <= 10, Delta A^+ = 0 sustained for 3 consecutive iterations); multi-tier rollback safeguards (5% residual growth, divergence factor 1.50, catastrophic cap 0.05); budget of 140 outer iterations.",
    "donor_source": {
        "checkpoint": "Checkpoint 03 (Job 1419566.mmaster02)",
        "target_uy_mm": 0.0018703125442191958,
        "donor_reference_force_kN": 0.17992419004440308,
        "donor_reference_total_energy_kNmm": 0.00022639903
    },
    "receiver_mesh": {
        "name": "C6_Receiver",
        "elements_quad": 15252,
        "physical_nodes": 15559,
        "slit_pairs": 59
    },
    "numerical_parameters": {
        "damping_omega_d_stage1": 0.50,
        "damping_omega_d_stage2": 0.85,
        "max_active_cardinality": 500,
        "max_symmetric_diff": 10,
        "max_added_nodes": 0,
        "stabilization_window": 3,
        "rollback_factor": 1.05,
        "divergence_factor": 1.50,
        "catastrophic_delta_d_cap": 0.05,
        "max_outer_iterations": 140,
        "delta_d_tol": 1e-05,
        "delta_u_tol_mm": 1e-09,
        "delta_h_tol_MPa": 0.0001,
        "consistency_delta_u_tol_mm": 1e-09,
        "consistency_delta_h_tol_MPa": 0.0001,
        "kkt_tol": 1e-06
    },
    "remediation_status": {
        "relaxation_mechanism": "TWO_PHASE_SAFEGUARDED_ADAPTIVE_DAMPING_COMPOUND_TRANSITION",
        "telemetry": "EXPLICIT_NODE_RESOLVED_ACTIVE_SET_SYMMETRIC_DIFFERENCE_AND_ANTI_EXPANSION",
        "safeguards_rollback": "MULTI_TIER_ROLLBACK_ON_RESIDUAL_GROWTH_DIVERGENCE_OR_CATASTROPHIC_JUMP",
        "defect_phase_decoding": "PRESERVED_FAIL_CLOSED_15559_NODES_REJECT_2COMP_MIXED",
        "defect_1_gauss_point_history_loading": "PRESERVED_4_GP_DISTINCT",
        "defect_2_split_keyword_blocks_unpacking": "PRESERVED_STRING_BLOCK_PARSING",
        "defect_3_uel_solution_state_formatting": "PRESERVED_ELEMENT_LEVEL_INITIAL_CONDITIONS",
        "defect_4_odb_extractor_cli_args": "PRESERVED_PHYSICAL_NODES_ELEMENTS_STEP",
        "defect_5_displacement_consistency_gate": "PRESERVED_STRICT_1E-9_MM",
        "defect_6_history_consistency_gate": "PRESERVED_STRICT_1E-4_MPA",
        "defect_7_final_kkt_stationarity_gate": "PRESERVED_STRICT_1E-6",
        "defect_8_gated_checkpoint_commitment": "PRESERVED_PHYSICAL_PASS_CONDITIONAL"
    },
    "files": files
}

manifest_path = pkg / "PACKAGE_MANIFEST.json"
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Generated {manifest_path} with {len(files)} files.")
