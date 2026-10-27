import os
import json
import hashlib

pkg_dir = os.path.abspath("models/pandey_kumar_mode1/119_c4_inc85_holdout_diagnostic")

file_list = [
    "M1_C4_INC85_HOLDOUT.inp",
    "active_set_boundary_cards.inc",
    "d_lower_bounds.csv",
    "driver_c4_inc85_holdout.py",
    "f42_unified_12dof_active_set_uel.for",
    "job_notifications.sh",
    "nodal_displacements_initial.csv",
    "run_c4_inc85_holdout_datacheck.sh",
    "stage_a_all_d0_boundary_cards.inc",
    "submit_M1_C4_INC85_HOLDOUT.pbs"
]

files_dict = {}
for fname in file_list:
    fpath = os.path.join(pkg_dir, fname)
    with open(fpath, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest().lower()
    files_dict[fname] = h

remote_dir = "/scratch9/pr21vyci/runs/mode1_c4_inc85_holdout_diagnostic"
pbs_remote_path = remote_dir + "/submit_M1_C4_INC85_HOLDOUT.pbs"
command_str = r'powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq ' + pbs_remote_path + '"'
command_hash = hashlib.sha256(command_str.encode("utf-8")).hexdigest().lower()

auth_data = {
    "schema": 1,
    "adapter": "mode1-experimental-12dof-v1",
    "scientific_scope": "MODE1",
    "technical_stage": "C1-1",
    "batch_name": "MODE1_C4_INC85_HOLDOUT_DIAGNOSTIC",
    "configuration": "ALTERNATING_MINIMIZATION_SAME_LOAD_HOLDOUT_DIAGNOSTIC",
    "hypothesis": "Independent Increment-85 C4 Holdout Diagnostic to test state-dependent mesh-aware energy correction without circular calibration.",
    "automatic_retry": False,
    "max_submissions": 1,
    "remote_run_dir": remote_dir,
    "files": files_dict,
    "jobs": [
        {
            "id": "M1_C4_INC85_HOLDOUT",
            "purpose": "Abaqus 2023 Candidate C4 Independent Holdout Diagnostic at u = 0.00191171 mm (4,422 quads, 4,588 nodes, up to 15 AM cycles with irreversible history transferred from authentic C3 Increment 85)",
            "input": "M1_C4_INC85_HOLDOUT.inp",
            "user_subroutine": "f42_unified_12dof_active_set_uel.for",
            "pbs": "submit_M1_C4_INC85_HOLDOUT.pbs",
            "datacheck": "M1_C4_INC85_HOLDOUT_DC.dat",
            "queue": "entry_imfdfkmq",
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "execution": "single-rank serial",
            "max_submissions": 1,
            "command": command_str,
            "command_sha256": command_hash,
            "depends_on": []
        }
    ],
    "acceptance": {
        "stage_C1_1_direct_transfer": {
            "u_top_target_mm": 0.001911713858,
            "rf2_expected_N": 185.97407639,
            "rf2_continuity_pct_max": 5.0,
            "energy_continuity_pct_max": 2.5,
            "kkt_violations_max": 0,
            "free_phase_residual_max_kN_mm": 1e-06,
            "healing_tolerance": 0,
            "stationarity_delta_d_max": 0.001,
            "stationarity_delta_rf2_max_N": 0.1
        }
    },
    "package_name": "119_c4_inc85_holdout_diagnostic"
}

auth_path = os.path.join(pkg_dir, "M1_C4_INC85_HOLDOUT_AUTHORIZATION.json")
with open(auth_path, "w", encoding="utf-8") as f:
    json.dump(auth_data, f, indent=2)

print("Generated:", auth_path)
print("Command:", command_str)
print("Command SHA256:", command_hash)
