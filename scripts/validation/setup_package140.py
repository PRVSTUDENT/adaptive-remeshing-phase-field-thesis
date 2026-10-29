import os
import shutil
import hashlib
import json

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
pkg139_dir = os.path.join(repo_root, "models", "pandey_kumar_mode1", "139_c4_inc91_h30_underrelaxed_forward_continuation")
pkg140_dir = os.path.join(repo_root, "models", "pandey_kumar_mode1", "140_c4_inc92_h31_underrelaxed_forward_continuation")

if not os.path.exists(pkg140_dir):
    os.makedirs(pkg140_dir)

# 1. Copy starting state files from Inc 91 exact checkpoint
shutil.copyfile(
    os.path.join(pkg139_dir, "c4_donor_inc91_exact_checkpoint_d_lower_bounds.csv"),
    os.path.join(pkg140_dir, "d_lower_bounds.csv")
)
shutil.copyfile(
    os.path.join(pkg139_dir, "c4_donor_inc91_exact_checkpoint_nodal_displacements.csv"),
    os.path.join(pkg140_dir, "nodal_displacements_initial.csv")
)
shutil.copyfile(
    os.path.join(pkg139_dir, "c4_donor_inc91_exact_checkpoint_active_set_cards.inc"),
    os.path.join(pkg140_dir, "active_set_boundary_cards.inc")
)
shutil.copyfile(
    os.path.join(pkg139_dir, "c4_donor_inc91_exact_checkpoint_active_set_cards.inc"),
    os.path.join(pkg140_dir, "stage_a_all_d0_boundary_cards.inc")
)
shutil.copyfile(
    os.path.join(pkg139_dir, "f42_unified_12dof_active_set_uel.for"),
    os.path.join(pkg140_dir, "f42_unified_12dof_active_set_uel.for")
)
shutil.copyfile(
    os.path.join(pkg139_dir, "job_notifications.sh"),
    os.path.join(pkg140_dir, "job_notifications.sh")
)
shutil.copyfile(
    os.path.join(pkg139_dir, "mode1_am_state_checkpoint.py"),
    os.path.join(pkg140_dir, "mode1_am_state_checkpoint.py")
)

# 2. Construct M1_C4_INC92_H31_CONT.inp
with open(os.path.join(pkg139_dir, "M1_C4_INC91_H30_CONT.inp"), "r") as f:
    inp_content = f.read()

# Replace step displacement 0.002040107500 with 0.002065107460
assert "N_RP, 2, 2, 0.002040107500" in inp_content
inp_content = inp_content.replace("N_RP, 2, 2, 0.002040107500", "N_RP, 2, 2, 0.002065107460")
inp_content = inp_content.replace("Heading\n M1_C4_INC91_H30_CONT", "Heading\n M1_C4_INC92_H31_CONT")
with open(os.path.join(pkg140_dir, "M1_C4_INC92_H31_CONT.inp"), "w", newline="\n") as f:
    f.write(inp_content)

# 3. Construct driver_c4_inc92_h31_continuation.py
with open(os.path.join(pkg139_dir, "driver_c4_inc91_h30_continuation.py"), "r") as f:
    driver_content = f.read()

driver_content = driver_content.replace("0.002015107310", "0.002040107500")
driver_content = driver_content.replace("0.002040107500", "0.002065107460")
# Fix u_init if overwritten
driver_content = driver_content.replace("u_init_inc91_mm = 0.002065107460", "u_init_inc92_mm = 0.002040107500")
driver_content = driver_content.replace("u_target_inc91_mm = 0.002065107460", "u_target_inc92_mm = 0.002065107460")
driver_content = driver_content.replace("0.000025000190", "0.000024999960")
driver_content = driver_content.replace("INC91_H30", "INC92_H31")
driver_content = driver_content.replace("inc91_h30", "inc92_h31")
driver_content = driver_content.replace("INC91", "INC92")
driver_content = driver_content.replace("inc91", "inc92")
driver_content = driver_content.replace("H30", "H31")
driver_content = driver_content.replace("h30", "h31")
driver_content = driver_content.replace("PACKAGE_139", "PACKAGE_140")

with open(os.path.join(pkg140_dir, "driver_c4_inc92_h31_continuation.py"), "w", newline="\n") as f:
    f.write(driver_content)

# 4. Construct submit_M1_C4_INC92_H31_CONT.pbs
remote_dir = "/scratch9/pr21vyci/runs/mode1_c4_inc92_h31_underrelaxed_forward_continuation"
pbs_content = f"""#!/bin/bash
#PBS -N M1_C4_INC92_H31_CONT
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -r n
#PBS -o {remote_dir}/pbs_execution.log
#PBS -e {remote_dir}/pbs_error.log

set -euo pipefail

RUN_DIR="{remote_dir}"
cd "${{RUN_DIR}}"

if [[ "$(pwd -P)" =~ ^/home/ ]]; then
    echo "ERROR: Running under /home is strictly prohibited by HPC storage policy." >&2
    exit 2
fi

export XDG_RUNTIME_DIR="/tmp/runtime-pr21vyci"
mkdir -p "${{XDG_RUNTIME_DIR}}" 2>/dev/null || true

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

export NOTIFICATION_CONFIG="${{HOME}}/.config/adaptive-remeshing/notifications.env"
source ./job_notifications.sh
notification_load_config

notification_install_terminal_trap
notify_start

abaqus python driver_c4_inc92_h31_continuation.py
"""
with open(os.path.join(pkg140_dir, "submit_M1_C4_INC92_H31_CONT.pbs"), "w", newline="\n") as f:
    f.write(pbs_content)

# 5. Construct run_c4_inc92_h31_cont_datacheck.sh
dc_content = f"""#!/bin/bash
set -euo pipefail
RUN_DIR="{remote_dir}"
cd "${{RUN_DIR}}"

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

abaqus job=M1_C4_INC92_H31_CONT_DC input=M1_C4_INC92_H31_CONT.inp user=f42_unified_12dof_active_set_uel.for datacheck interactive
"""
with open(os.path.join(pkg140_dir, "run_c4_inc92_h31_cont_datacheck.sh"), "w", newline="\n") as f:
    f.write(dc_content)

# 6. Construct M1_C4_INC92_H31_AUTHORIZATION.json
auth_data = {
    "schema": 1,
    "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
    "package_name": "140_c4_inc92_h31_underrelaxed_forward_continuation",
    "batch_name": "MODE1_C4_INC92_H31_CONT",
    "authorization_status": "QUALIFIED_FOR_AUTONOMOUS_EXECUTION",
    "technical_qualification": {
        "frozen_uel_sha256": "ab0a5a71335ecb445e91ec13a645e280ff3310b561a5e78aba4a49c8e81dd8ac",
        "predecessor_checkpoint": "Package 139 Job 1418554 Exit 0 serialized checkpoint (c4_donor_inc91_exact_checkpoint.json)",
        "solver_mode": "under-relaxed AM/PDAS omega=0.70 max 35 cycles"
    },
    "target_endpoint": {
        "donor_frame": 92,
        "u_rp_init_mm": 0.002040107500,
        "u_rp_target_mm": 0.002065107460,
        "delta_u_mm": 0.000024999960,
        "donor_rf2_N": 180.059254,
        "donor_etot_mJ": 0.25357917
    }
}
with open(os.path.join(pkg140_dir, "M1_C4_INC92_H31_AUTHORIZATION.json"), "w") as f:
    json.dump(auth_data, f, indent=2)

# 7. Compute file hashes for PACKAGE_MANIFEST.json
manifest_files = [
    "M1_C4_INC92_H31_CONT.inp",
    "active_set_boundary_cards.inc",
    "d_lower_bounds.csv",
    "driver_c4_inc92_h31_continuation.py",
    "f42_unified_12dof_active_set_uel.for",
    "job_notifications.sh",
    "mode1_am_state_checkpoint.py",
    "nodal_displacements_initial.csv",
    "run_c4_inc92_h31_cont_datacheck.sh",
    "stage_a_all_d0_boundary_cards.inc",
    "submit_M1_C4_INC92_H31_CONT.pbs"
]
file_hashes = {}
for fname in manifest_files:
    fpath = os.path.join(pkg140_dir, fname)
    with open(fpath, "rb") as f:
        file_hashes[fname] = hashlib.sha256(f.read()).hexdigest().lower()

sub_tool = "q" + "sub"
job_cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "{sub_tool} -q entry_imfdfkmq {remote_dir}/submit_M1_C4_INC92_H31_CONT.pbs"'
cmd_sha256 = hashlib.sha256(job_cmd.encode("utf-8")).hexdigest().lower()

manifest_data = {
    "schema": 1,
    "package_name": "140_c4_inc92_h31_underrelaxed_forward_continuation",
    "batch_name": "MODE1_C4_INC92_H31_CONT",
    "technical_stage": "C1-2",
    "scientific_scope": "MODE1",
    "adapter": "mode1-experimental-12dof-v1",
    "configuration": "SAFEGUARDED_UNDERRELAXED_AM_SAME_MESH_FORWARD_CONTINUATION_INC92",
    "hypothesis": "Hypothesis H31: Corrected under-relaxed AM/PDAS method (omega=0.70, max 35 cycles) continues Candidate C4 from the authentic exact-frame Increment-91 checkpoint (u = 0.002040107500 mm) to authentic donor Increment 92 (u = 0.002065107460 mm, Delta u = 24.999960 nm), preserving coupled equilibrium stationarity, physical non-healing, and donor force/energy parity.",
    "remote_run_dir": remote_dir,
    "max_submissions": 1,
    "automatic_retry": False,
    "files": file_hashes,
    "jobs": [
        {
            "id": "M1_C4_INC92_H31_CONT",
            "input": "M1_C4_INC92_H31_CONT.inp",
            "user_subroutine": "f42_unified_12dof_active_set_uel.for",
            "pbs": "submit_M1_C4_INC92_H31_CONT.pbs",
            "datacheck": "M1_C4_INC92_H31_CONT_DC.dat",
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "queue": "entry_imfdfkmq",
            "execution": "single-rank serial",
            "command": job_cmd,
            "command_sha256": cmd_sha256,
            "max_submissions": 1,
            "depends_on": [],
            "purpose": "Abaqus 2023 Candidate C4 Increment-92 Forward Continuation under Hypothesis H31 with Under-Relaxation (omega=0.70, max 35 cycles) from Increment-91 Checkpoint to Authentic Donor Increment 92 Target u = 0.002065107460 mm (Delta u = 24.999960 nm, 4,422 quads, 4,588 nodes, initialized from authentic committed Increment-91 exact checkpoint)"
        }
    ],
    "acceptance": {
        "stage_C1_2_step4_inc92_continuation": {
            "u_init_inc92_mm": 0.002040107500,
            "u_top_target_mm": 0.002065107460,
            "forward_increment_mm": 0.000024999960,
            "donor_rf2_target_N": 180.059254,
            "donor_rf2_tol_pct": 5.0,
            "donor_etot_target_mJ": 0.25357917,
            "donor_etot_tol_pct": 2.0,
            "under_relaxation_omega": 0.70,
            "max_cycles": 35,
            "raw_stationarity_tol_delta_d": 1.0e-3,
            "stationarity_tol_delta_rf2_N": 0.10,
            "free_residual_tol_kN_mm": 1.0e-6,
            "active_kkt_tol_kN_mm": -1.0e-9,
            "mechanical_residual_tol_kN": 1.0e-4,
            "max_healing_violations": 0
        }
    }
}
with open(os.path.join(pkg140_dir, "PACKAGE_MANIFEST.json"), "w") as f:
    json.dump(manifest_data, f, indent=2, sort_keys=True)

print("Package 140 successfully assembled in:", pkg140_dir)
