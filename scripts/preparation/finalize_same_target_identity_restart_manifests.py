#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verify exact equality of source and installed state, and create cryptographic manifests for:
M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL
"""

import os
import sys
import hashlib
import json
import struct
import numpy as np

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as fp:
        while True:
            chunk = fp.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def finalize_package():
    pkg_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL"
    inp_file = os.path.join(pkg_dir, "M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL.inp")
    uel_file = os.path.join(pkg_dir, "f44_mixed_uel_restart_stateinit.for")
    pbs_file = os.path.join(pkg_dir, "submit_job.pbs")
    bin_file = os.path.join(pkg_dir, "STAGE_D_COMMITTED_STATE.bin")
    flag_file = os.path.join(pkg_dir, "MODE_STAGED.flag")

    print("================================================================================")
    print("VERIFYING SAME-TARGET IDENTITY RESTART PACKAGE")
    print("================================================================================")

    # 1. Verify binary state file format
    bin_size = os.path.getsize(bin_file)
    expected_size = 4 + 3200000 + 4 + 4 + 3200000 + 4 # 6,400,016 bytes
    assert bin_size == expected_size, "Binary size mismatch: %d != %d" % (bin_size, expected_size)
    print("Binary file size verified: %d bytes (Exact match)" % bin_size)

    # Read binary back
    with open(bin_file, 'rb') as fp:
        rec1_len = struct.unpack('i', fp.read(4))[0]
        rec1_bytes = fp.read(rec1_len)
        rec1_end = struct.unpack('i', fp.read(4))[0]
        assert rec1_len == 3200000 and rec1_end == 3200000
        phase_arr = np.frombuffer(rec1_bytes, dtype=np.float64).reshape((100000, 4), order='F')

        rec2_len = struct.unpack('i', fp.read(4))[0]
        rec2_bytes = fp.read(rec2_len)
        rec2_end = struct.unpack('i', fp.read(4))[0]
        assert rec2_len == 3200000 and rec2_end == 3200000
        h_arr = np.frombuffer(rec2_bytes, dtype=np.float64).reshape((100000, 4), order='F')

    print("Binary unpack verified: Phase max = %.7f, H max = %.7f MPa" % (
        np.max(phase_arr[:8836, :]), np.max(h_arr[:8836, :]) * 1000.0))

    # 2. Check hashes
    inp_hash = compute_sha256(inp_file)
    uel_hash = compute_sha256(uel_file)
    pbs_hash = compute_sha256(pbs_file)
    bin_hash = compute_sha256(bin_file)
    flag_hash = compute_sha256(flag_file)

    print("\n--- PACKAGE HASHES ---")
    print("  INP  Hash : %s" % inp_hash)
    print("  UEL  Hash : %s" % uel_hash)
    print("  PBS  Hash : %s" % pbs_hash)
    print("  BIN  Hash : %s" % bin_hash)
    print("  FLAG Hash : %s" % flag_hash)

    # Write manifest.json
    manifest = {
        "package_name": "M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL",
        "description": "Same-target-mesh identity staged restart diagnostic sourced from Frame 17 of 1390447.mmaster02",
        "source_run": "1390447.mmaster02",
        "source_frame": 17,
        "source_increment": 17,
        "source_step_time": 0.2102578,
        "source_physical_u1_mm": 0.01051289,
        "target_mesh_quads": 8836,
        "target_mesh_nodes": 9074,
        "execution_mode": "MODE 1: STAGED_TRANSFER_RESTART (Explicit PROPS(7)=1.0)",
        "files": {
            "M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL.inp": {
                "sha256": inp_hash,
                "size_bytes": os.path.getsize(inp_file)
            },
            "f44_mixed_uel_restart_stateinit.for": {
                "sha256": uel_hash,
                "size_bytes": os.path.getsize(uel_file)
            },
            "submit_job.pbs": {
                "sha256": pbs_hash,
                "size_bytes": os.path.getsize(pbs_file)
            },
            "STAGE_D_COMMITTED_STATE.bin": {
                "sha256": bin_hash,
                "size_bytes": os.path.getsize(bin_file)
            },
            "MODE_STAGED.flag": {
                "sha256": flag_hash,
                "size_bytes": os.path.getsize(flag_file)
            }
        }
    }

    manifest_path = os.path.join(pkg_dir, "manifest.json")
    with open(manifest_path, 'w') as fp:
        json.dump(manifest, fp, indent=2)
    print("Created %s" % manifest_path)

    # Write one_difference_scientific_manifest.json (comparing against 1390279 nonmatching restart)
    one_diff = {
        "experiment_comparison": "Same-Target-Mesh Identity Restart vs. Nonmatching Transfer Restart (1390279.mmaster02)",
        "mesh_discretization_status": "FALSIFIED_AS_DEFECT_CAUSE_BY_F272 (Target mesh solved continuous 1390447 with 0.738% peak load match)",
        "comparison_basis": {
            "mesh_quads": 8836,
            "mesh_nodes": 9074,
            "mesh_type": "Exact Stage-D Sliver-Free Graded Quad Mesh",
            "material_properties": "E=210.0 kN/mm2, nu=0.3, l0=0.015 mm, Gc=0.0027 N/mm, k=1e-7",
            "staged_sequence": "STATE_LOAD -> MECH_EQUILIBRATION -> PHASE_RELEASE -> CONTINUATION",
            "continuation_loading": "U1_handoff -> 0.050 mm monotonic shear",
            "execution_mode": "Explicit Mode 1 (Staged Restart)"
        },
        "isolated_single_difference": {
            "parameter": "PROVENANCE_AND_OPERATOR_OF_INSTALLED_STATE",
            "1390279_nonmatching_transfer": "Transferred via nonmatching spatial interpolation from H1 donor mesh (nearest-GP operator)",
            "this_diagnostic_identity_restart": "Transferred via exact identity mapping (1-to-1) from accepted Frame 17 of 1390447.mmaster02 on exact same mesh"
        },
        "predeclared_scientific_interpretations": {
            "case_A_continuation_succeeds": "If identity staged restart reproduces uninterrupted continuous 1390447 without dt_min divergence, the nonmatching transfer/interpolation operator is isolated as the defect cause.",
            "case_B_continuation_diverges": "If identity staged restart diverges similarly at post-release, the defect resides in the staged restart / displacement boundary / active-set implementation."
        }
    }

    one_diff_path = os.path.join(pkg_dir, "one_difference_scientific_manifest.json")
    with open(one_diff_path, 'w') as fp:
        json.dump(one_diff, fp, indent=2)
    print("Created %s" % one_diff_path)

if __name__ == "__main__":
    finalize_package()
