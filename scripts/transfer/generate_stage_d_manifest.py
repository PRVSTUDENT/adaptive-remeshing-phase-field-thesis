#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate manifest.json with SHA-256 hashes for Stage-D Nonmatching Transfer Package.
"""

import os
import json
import hashlib

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def generate_manifest():
    pkg_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL"
    
    files_to_hash = {
        "inp": "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.inp",
        "uel": "f44_mixed_uel_restart_stateinit.for",
        "primary_state_bc_include": "STAGE_D_PRIMARY_STATE_BOUNDARY.inp",
        "u3_only_bc_include": "STAGE_D_U3_ONLY_BOUNDARY.inp",
        "committed_state_bin": "STAGE_D_COMMITTED_STATE.bin",
        "launcher": "submit_job.pbs",
        "source_mesh_generator": "../../../../../scripts/transfer/generate_stage_d_target_mesh.py",
        "transfer_pipeline_script": "../../../../../scripts/transfer/transfer_stage_d_state.py"
    }
    
    hashes = {}
    for key, rel_path in files_to_hash.items():
        abs_path = os.path.normpath(os.path.join(pkg_dir, rel_path))
        if os.path.exists(abs_path):
            hashes[key] = sha256_file(abs_path)
            print("%-25s: %s (%s)" % (key, hashes[key], os.path.basename(abs_path)))
        else:
            print("WARNING: %s not found at %s" % (key, abs_path))
            
    manifest = {
        "job_name": "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL",
        "scientific_purpose": "Stage-D Pure Nonmatching Mesh Same-Topology State Transfer Solver Qualification",
        "validation_stage": "Stage D",
        "handoff_source": {
            "source_job_name": "M2CORR_H1_FREEU2_FULL_U050",
            "source_job_pbs_id": "1389686.mmaster02",
            "source_frame": 29,
            "physical_u1_mm": 0.010143300518393517,
            "source_mesh": {
                "node_count": 12383,
                "physical_element_count": 24128,
                "element_type": "CPE4_UEL_PAIR"
            },
            "source_field_extrema": {
                "u1_max_mm": 0.010143,
                "u2_min_mm": -0.004277,
                "u2_max_mm": 0.010725,
                "d_max": 0.285585,
                "H_max_kn_mm2": 0.848870
            }
        },
        "target_mesh": {
            "node_count": 18700,
            "physical_element_count": 18360,
            "grid_dimensions": {"nx": 135, "ny": 136},
            "crack_topology": "OPEN_SLIT_VERIFIED",
            "split_nodes_along_slit": 68,
            "shared_slit_nodes": 0
        },
        "transfer_rules": {
            "phase_field_d": "HOST_ELEMENT_SHAPE_FUNCTION_INTERPOLATION_CLAMPED_0_1",
            "displacement_u": "HOST_ELEMENT_SHAPE_FUNCTION_INTERPOLATION",
            "history_variable_H": "HOST_NEAREST_GP_WITH_NONNEGATIVE_IRREVERSIBILITY"
        },
        "transferred_target_extrema": {
            "u1_range_mm": [-0.000007, 0.010143],
            "u2_range_mm": [-0.004277, 0.010725],
            "d_range": [0.000000, 0.279282],
            "H_max_kn_mm2": 0.289181
        },
        "execution_resources": {
            "requested_queue": "entry_imfdfkmq",
            "cpus": 1,
            "memory_gb": 16,
            "walltime": "24:00:00",
            "abaqus_version": "2023",
            "compiler_module": "gcc/11.4.0 -> intel/2024.2.0"
        },
        "qualification_status": {
            "uel_compilation_status": "PASSED_EXIT_0",
            "abaqus_datacheck_status": "PASSED_EXIT_0",
            "state_import_status": "SUCCESS_VERIFIED"
        },
        "file_hashes_sha256": hashes
    }
    
    manifest_path = os.path.join(pkg_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print("Saved manifest: %s" % manifest_path)

if __name__ == "__main__":
    generate_manifest()
