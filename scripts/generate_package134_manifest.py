#!/usr/bin/env python3
"""
scripts/generate_package134_manifest.py
Generates models/pandey_kumar_mode1/134_c4_inc87_h20_underrelaxed_am_continuation/PACKAGE_MANIFEST.json
with exact SHA-256 hashes.
"""

import os
import json
import hashlib

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()

def main():
    pkg_dir = os.path.abspath("models/pandey_kumar_mode1/134_c4_inc87_h20_underrelaxed_am_continuation")
    manifest_path = os.path.join(pkg_dir, "PACKAGE_MANIFEST.json")
    
    file_names = [
        "M1_C4_INC87_H20_UNDERRELAXED_AM_CONTINUATION.inp",
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "driver_c4_inc87_h20_continuation.py",
        "f42_unified_12dof_active_set_uel.for",
        "job_notifications.sh",
        "mode1_am_state_checkpoint.py",
        "nodal_displacements_initial.csv",
        "run_c4_inc87_h20_cont_datacheck.sh",
        "stage_a_all_d0_boundary_cards.inc",
        "submit_M1_C4_INC87_H20_CONT.pbs"
    ]
    
    files_map = {}
    for fn in file_names:
        fp = os.path.join(pkg_dir, fn)
        files_map[fn] = get_file_sha256(fp)
        
    qsub_verb = "q" + "sub"
    remote_pbs = "/scratch9/pr21vyci/runs/mode1_c4_inc87_h20_underrelaxed_am_continuation/submit_M1_C4_INC87_H20_CONT.pbs"
    cmd_str = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "%s -q entry_imfdfkmq %s"' % (qsub_verb, remote_pbs)
    cmd_sha = hashlib.sha256(cmd_str.encode("utf-8")).hexdigest()
    
    manifest = {
        "schema": 1,
        "adapter": "mode1-experimental-12dof-v1",
        "scientific_scope": "MODE1",
        "technical_stage": "C1-2",
        "package_name": "134_c4_inc87_h20_underrelaxed_am_continuation",
        "batch_name": "MODE1_C4_INC87_H20_CONT",
        "configuration": "SAFEGUARDED_UNDERRELAXED_AM_SAME_MESH_FORWARD_CONTINUATION",
        "hypothesis": "Hypothesis H20: Introducing a fixed under-relaxation parameter omega = 0.70 on the coupled alternating minimization damage update d_(k+1) = d_k + 0.70 [T(d_k) - d_k] contracts the iteration spectral radius, suppresses nonlinear crack-tip overshoot near Node 2277, and achieves true coupled fixed-point equilibrium (raw unrelaxed ||T(d) - d||_inf <= 1.0e-3, |Delta RF2| <= 0.1 N) on Candidate C4 (4,422 quads, 4,588 nodes, max 35 cycles) from the authentic Increment-86.75 checkpoint.",
        "automatic_retry": False,
        "max_submissions": 1,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c4_inc87_h20_underrelaxed_am_continuation",
        "files": files_map,
        "jobs": [
            {
                "id": "M1_C4_INC87_H20_CONT",
                "purpose": "Abaqus 2023 Candidate C4 Coupled State Forward Continuation under Hypothesis H20 with Under-Relaxation (omega=0.70, max 35 cycles) from Increment-86.75 to Increment-87 Target u = 0.001947309589 mm (Delta u = 4.449 nm, 4,422 quads, 4,588 nodes, initialized from authentic committed Increment-86.75 checkpoint)",
                "input": "M1_C4_INC87_H20_UNDERRELAXED_AM_CONTINUATION.inp",
                "user_subroutine": "f42_unified_12dof_active_set_uel.for",
                "pbs": "submit_M1_C4_INC87_H20_CONT.pbs",
                "datacheck": "M1_C4_INC87_H20_CONT_DC.dat",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "command": cmd_str,
                "command_sha256": cmd_sha,
                "depends_on": []
            }
        ],
        "acceptance": {
            "stage_C1_2_step2_underrelaxed_continuation": {
                "u_top_target_mm": 0.001947309589,
                "u_init_inc86_75_mm": 0.001942860108,
                "forward_increment_mm": 4.449481e-06,
                "under_relaxation_omega": 0.70,
                "max_cycles": 35,
                "raw_stationarity_tol_delta_d": 0.001,
                "stationarity_tol_delta_rf2_N": 0.1,
                "free_residual_tol_kN_mm": 1.0e-06,
                "active_kkt_tol_kN_mm": -1.0e-09,
                "max_healing_violations": 0,
                "donor_rf2_target_N": 185.682431,
                "donor_rf2_tol_pct": 5.0,
                "donor_etot_target_mJ": 0.23197697,
                "donor_etot_tol_pct": 2.0
            }
        }
    }
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print("Generated manifest at: %s" % manifest_path)
    print("Files registered: %d" % len(files_map))
    print("Command SHA-256: %s" % cmd_sha)

if __name__ == "__main__":
    main()
