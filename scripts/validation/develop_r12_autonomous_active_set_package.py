#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
develop_r12_autonomous_active_set_package.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 142)
Protocol Version: 2

Develops Candidate Package 108 Revision 12 (R12):
Autonomous (oracle-free) active-set continuation in genuine Abaqus/Standard 2023.
"""

import sys
import os
import shutil
import hashlib
import json
from pathlib import Path
import pandas as pd
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
R11_DIR = REPO_ROOT / "models/pandey_kumar_mode1/108_r11_c3_active_set_continuation"
R12_DIR = REPO_ROOT / "models/pandey_kumar_mode1/108_r12_c3_autonomous_active_set"

R12_DIR.mkdir(parents=True, exist_ok=True)

# 1. Copy frozen/verified assets from R11
# UEL
src_uel = R11_DIR / "f42_unified_12dof_active_set_uel.for"
dst_uel = R12_DIR / "f42_unified_12dof_active_set_uel.for"
shutil.copy2(src_uel, dst_uel)

# Bounds
src_bounds = R11_DIR / "d_lower_bounds.csv"
dst_bounds = R12_DIR / "d_lower_bounds.csv"
shutil.copy2(src_bounds, dst_bounds)

# Notifications
src_notif = R11_DIR / "job_notifications.sh"
dst_notif = R12_DIR / "job_notifications.sh"
shutil.copy2(src_notif, dst_notif)

# 2. Generate stage_a_all_d0_boundary_cards.inc (constraining all 2,769 nodes to d0 in Step 1 Stage-A)
df_bounds = pd.read_csv(dst_bounds, skipinitialspace=True)
# Parse nodes from C3 mesh to get nodal d0
# Each element row in d_lower_bounds.csv has EID, D0_1, D0_2, D0_3, D0_4
# Let's map elements to nodes using R11 continuation deck
inp_r11_lines = (R11_DIR / "M1_C3_ACTIVE_SET_R11_CONTINUATION.inp").read_text(encoding="utf-8").splitlines()

# Extract *Element section
elements = {}
reading_elems = False
for line in inp_r11_lines:
    if line.startswith("*Element"):
        reading_elems = True
        continue
    if reading_elems:
        if line.startswith("*"):
            break
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if len(parts) >= 5:
            eid = int(parts[0])
            nodes = [int(p) for p in parts[1:5]]
            elements[eid] = nodes

nodal_d0 = {}
for _, row in df_bounds.iterrows():
    eid = int(row['EID'])
    if eid in elements:
        for k in range(4):
            nid = elements[eid][k]
            d0_k = float(row[f'D0_{k+1}'])
            if nid not in nodal_d0 or d0_k > nodal_d0[nid]:
                nodal_d0[nid] = d0_k

all_nids = sorted(nodal_d0.keys())
print(f"Total mapped physical nodes with d0 bounds: {len(all_nids)}")

# Write stage_a_all_d0_boundary_cards.inc
stage_a_inc = R12_DIR / "stage_a_all_d0_boundary_cards.inc"
with open(stage_a_inc, "w", newline="\n") as f:
    for nid in all_nids:
        f.write(f"{nid}, 3, 3, {nodal_d0[nid]:.8f}\n")

# Write initial active_set_boundary_cards.inc (all nodes active at start)
init_active_inc = R12_DIR / "active_set_boundary_cards.inc"
with open(init_active_inc, "w", newline="\n") as f:
    for nid in all_nids:
        f.write(f"{nid}, 3, 3, {nodal_d0[nid]:.8f}\n")

# 3. Create M1_C3_ACTIVE_SET_R12_CONTINUATION.inp
# In R12, Step 1 uses stage_a_all_d0_boundary_cards.inc
# Step 2 uses *Boundary, OP=NEW and includes active_set_boundary_cards.inc
inp_lines = []
for line in inp_r11_lines:
    if line.strip() == "*Include, input=active_set_boundary_cards.inc":
        inp_lines.append("*Include, input=stage_a_all_d0_boundary_cards.inc")
    elif line.strip() == "** STEP 2: Inc1-Coupled (+1 nm forward loading to u = 0.00196610735 mm)":
        inp_lines.append(line)
        # Advance until *Boundary in Step 2
    elif line.strip() == "*Boundary" and len(inp_lines) > 5660:
        # Step 2 boundary block: replace with OP=NEW and include active_set_boundary_cards.inc
        inp_lines.append("*Boundary, OP=NEW")
        inp_lines.append("N_BOTTOM, 2, 2, 0.0")
        inp_lines.append("N_PIN, 1, 1, 0.0")
        inp_lines.append("N_TOP, 1, 1, 0.0")
        inp_lines.append("N_RP, 1, 1, 0.0")
        inp_lines.append("N_RP, 2, 2, 0.00196610735")
        inp_lines.append("*Include, input=active_set_boundary_cards.inc")
        # Skip the original N_RP line in Step 2
    elif line.strip() == "N_RP, 2, 2, 0.00196610735" and len(inp_lines) > 5660:
        continue # already added
    else:
        inp_lines.append(line)

r12_inp_path = R12_DIR / "M1_C3_ACTIVE_SET_R12_CONTINUATION.inp"
r12_inp_path.write_text("\n".join(inp_lines) + "\n", encoding="utf-8")
print(f"Created R12 input deck: {r12_inp_path} ({len(inp_lines)} lines)")

# 4. Create driver_r12_autonomous_continuation.py (executed by abaqus python)
driver_code = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
driver_r12_autonomous_continuation.py
Autonomous (oracle-free) active-set continuation driver in genuine Abaqus/Standard 2023.
Package: PACKAGE_108_R12_C3_AUTONOMOUS_ACTIVE_SET
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
"""

import sys
import os
import subprocess
import json
import math
from odbAccess import openOdb

def log(msg):
    print("[R12-DRIVER] " + str(msg))
    sys.stdout.flush()

def load_nodal_d0():
    # Read stage_a_all_d0_boundary_cards.inc
    nodal_d0 = {}
    with open("stage_a_all_d0_boundary_cards.inc", "r") as f:
        for line in f:
            line = line.strip()
            if line:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if len(parts) >= 4:
                    nid = int(parts[0])
                    d0 = float(parts[3])
                    nodal_d0[nid] = d0
    return nodal_d0

def write_active_boundary_cards(active_nodes, nodal_d0):
    with open("active_set_boundary_cards.inc", "w") as f:
        for nid in sorted(active_nodes):
            f.write("%d, 3, 3, %.8f\\n" % (nid, nodal_d0[nid]))

def run_abaqus_iteration(iter_idx):
    job_name = "M1_C3_ACTIVE_SET_R12_IT%d" % iter_idx
    inp_name = "M1_C3_ACTIVE_SET_R12_CONTINUATION.inp"
    user_sub = "f42_unified_12dof_active_set_uel.for"

    cmd = ["abaqus", "job=" + job_name, "input=" + inp_name, "user=" + user_sub, "cpus=1", "interactive"]
    log("Executing Abaqus command: " + " ".join(cmd))

    ret = subprocess.call(cmd)
    log("Abaqus solver process exited with return code: %d" % ret)
    return job_name, ret

def extract_iteration_results(job_name, active_nodes, nodal_d0, tau_release, tau_heal):
    odb_path = job_name + ".odb"
    if not os.path.exists(odb_path):
        raise RuntimeError("ODB file not found: " + odb_path)

    odb = openOdb(odb_path, readOnly=True)

    # Inspect Step 2 (Inc1-Coupled)
    if "Inc1-Coupled" not in odb.steps:
        odb.close()
        raise RuntimeError("Step Inc1-Coupled missing in ODB")

    step2 = odb.steps["Inc1-Coupled"]
    last_frame = step2.frames[-1]

    # Extract energies
    energies = {}
    for key, reg in step2.historyRegions.items():
        for e_key, series in reg.historyOutputs.items():
            if len(series.data) > 0:
                energies[e_key] = series.data[-1][1]

    # Extract fields
    u_field = last_frame.fieldOutputs.get("U")
    rf_field = last_frame.fieldOutputs.get("RF")

    rf2_rp = 0.0
    u2_rp = 0.0
    u_vals = {}
    rf_vals = {}

    if u_field:
        for val in u_field.values:
            nid = val.nodeLabel
            if nid == 999999:
                u2_rp = float(val.data[1])
            if len(val.data) >= 3:
                u_vals[nid] = (float(val.data[0]), float(val.data[1]), float(val.data[2]))

    if rf_field:
        for val in rf_field.values:
            nid = val.nodeLabel
            if nid == 999999:
                rf2_rp = float(val.data[1] * 1000.0) # to N
            if len(val.data) >= 3:
                rf_vals[nid] = (float(val.data[0]), float(val.data[1]), float(val.data[2]))

    odb.close()

    # Postprocess active set
    release_candidates = []
    activate_candidates = []
    healing_nodes = []
    d_max = 0.0

    min_lambda = 0.0
    max_lambda = 0.0
    max_phase_res = 0.0

    active_set = set(active_nodes)

    for nid, d0 in nodal_d0.items():
        u_tuple = u_vals.get(nid, (0.0, 0.0, d0))
        rf_tuple = rf_vals.get(nid, (0.0, 0.0, 0.0))
        d_val = u_tuple[2]
        rf3_val = rf_tuple[2]

        if d_val > d_max:
            d_max = d_val

        # Active node check
        if nid in active_set:
            if rf3_val < min_lambda:
                min_lambda = rf3_val
            if rf3_val > max_lambda:
                max_lambda = rf3_val

            # KKT release criterion: lambda = RF3 < -tau_release
            if rf3_val < -tau_release:
                release_candidates.append(nid)
        else:
            # Free node check: healing & residual
            delta_d = d_val - d0
            if delta_d < -tau_heal:
                activate_candidates.append(nid)
                healing_nodes.append((nid, delta_d))

            if abs(rf3_val) > max_phase_res:
                max_phase_res = abs(rf3_val)

    return {
        "job_name": job_name,
        "rf2_rp_N": rf2_rp,
        "u2_rp_mm": u2_rp,
        "energies": energies,
        "allse_mJ": energies.get("ALLSE", 0.0) * 1000.0,
        "d_max": d_max,
        "min_lambda": min_lambda,
        "max_lambda": max_lambda,
        "max_phase_res": max_phase_res,
        "release_count": len(release_candidates),
        "activate_count": len(activate_candidates),
        "release_candidates": release_candidates,
        "activate_candidates": activate_candidates,
        "healing_count": len(healing_nodes)
    }

def main():
    log("Starting R12 Autonomous Active-Set Continuation Driver")

    nodal_d0 = load_nodal_d0()
    n_nodes = len(nodal_d0)
    log("Loaded %d nodes with d0 lower bounds" % n_nodes)

    # Physical tolerances
    tau_release = 5.0e-7  # kN/mm (standard physical KKT bound)
    tau_heal = 1.0e-8     # dimensionless damage bound

    # Initial active set: all nodes active
    active_nodes = set(nodal_d0.keys())
    log("Initial Active Set: %d nodes active, 0 nodes free" % len(active_nodes))

    iteration_history = []
    converged = False
    fail_fast_triggered = None

    for outer_iter in range(1, 9):
        log("=======================================================")
        log("--- OUTER ACTIVE-SET ITERATION %d (Active: %d, Free: %d) ---" %
            (outer_iter, len(active_nodes), n_nodes - len(active_nodes)))
        log("=======================================================")

        # 1. Write active boundary cards
        write_active_boundary_cards(active_nodes, nodal_d0)

        # 2. Run Abaqus solver
        job_name, exit_code = run_abaqus_iteration(outer_iter)
        if exit_code != 0:
            fail_fast_triggered = "SOLVER_ABORT_EXIT_%d" % exit_code
            log("FAIL-FAST: " + fail_fast_triggered)
            break

        # 3. Extract results
        res = extract_iteration_results(job_name, active_nodes, nodal_d0, tau_release, tau_heal)

        log("Iteration %d Results:" % outer_iter)
        log("  RF2: %.4f N | ALLSE: %.6f mJ | d_max: %.6f" %
            (res["rf2_rp_N"], res["allse_mJ"], res["d_max"]))
        log("  Min Lambda (Active): %.3e kN/mm | Max Residual (Free): %.3e kN/mm" %
            (res["min_lambda"], res["max_phase_res"]))
        log("  Release candidates: %d | Activate candidates: %d | Healing: %d" %
            (res["release_count"], res["activate_count"], res["healing_count"]))

        iteration_history.append({
            "outer_iter": outer_iter,
            "job_name": job_name,
            "active_node_count": len(active_nodes),
            "free_node_count": n_nodes - len(active_nodes),
            "rf2_rp_N": res["rf2_rp_N"],
            "u2_rp_mm": res["u2_rp_mm"],
            "allse_mJ": res["allse_mJ"],
            "d_max": res["d_max"],
            "min_lambda": res["min_lambda"],
            "max_lambda": res["max_lambda"],
            "max_phase_res": res["max_phase_res"],
            "release_count": res["release_count"],
            "activate_count": res["activate_count"],
            "healing_count": res["healing_count"],
            "energies": res["energies"]
        })

        # Check Fail-Fast Conditions
        # 1. Damage upper bound violation
        if res["d_max"] > 1.0 + 1.0e-5:
            fail_fast_triggered = "DAMAGE_OVERFLOW_DMAX_%.4f" % res["d_max"]
            log("FAIL-FAST: " + fail_fast_triggered)
            break

        # 2. Severe healing divergence
        if res["healing_count"] > 0:
            log("WARNING: %d nodes exhibited healing" % res["healing_count"])

        # 3. Target displacement error
        target_u2 = 0.00196610735
        if abs(res["u2_rp_mm"] - target_u2) > 1.0e-7:
            fail_fast_triggered = "KINEMATIC_INCONSISTENCY_U2_%.8f" % res["u2_rp_mm"]
            log("FAIL-FAST: " + fail_fast_triggered)
            break

        # 4. Check Convergence
        if res["release_count"] == 0 and res["activate_count"] == 0:
            log("--> ACTIVE-SET CONVERGED AT ITERATION %d!" % outer_iter)
            converged = True
            break

        # 5. Update active set
        new_active = set(active_nodes)
        for nid in res["release_candidates"]:
            new_active.discard(nid)
        for nid in res["activate_candidates"]:
            new_active.add(nid)

        # Check for oscillation / flip-flop
        if len(iteration_history) >= 2:
            prev_counts = (iteration_history[-2]["active_node_count"], iteration_history[-2]["release_count"])
            curr_counts = (len(active_nodes), res["release_count"])
            if prev_counts == curr_counts and res["release_count"] > 0:
                log("CYCLE WARNING: Active set count unchanged across iterations")

        active_nodes = new_active

    # Final summary output
    final_status = "CONVERGED" if converged else ("FAIL_FAST_" + fail_fast_triggered if fail_fast_triggered else "ACTIVE_SET_NOT_CONVERGED")
    log("Driver completed with status: " + final_status)

    summary = {
        "schema": 1,
        "package": "PACKAGE_108_R12_C3_AUTONOMOUS_ACTIVE_SET",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "status": final_status,
        "converged": converged,
        "fail_fast_triggered": fail_fast_triggered,
        "outer_iterations_completed": len(iteration_history),
        "tau_release_kN_mm": tau_release,
        "tau_heal": tau_heal,
        "history": iteration_history,
        "final_metrics": iteration_history[-1] if iteration_history else None
    }

    with open("r12_autonomous_continuation_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    log("Saved r12_autonomous_continuation_summary.json successfully.")

if __name__ == "__main__":
    main()
'''

driver_path = R12_DIR / "driver_r12_autonomous_continuation.py"
driver_path.write_text(driver_code, encoding="utf-8")
print(f"Created R12 driver script: {driver_path}")

# 5. Create run_pkg108_r12_datacheck.sh
datacheck_sh = '''#!/bin/bash
set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r12"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Running Abaqus 2023 preflight datacheck for Package 108 R12..."
abaqus datacheck job=M1_C3_ACTIVE_SET_R12 input=M1_C3_ACTIVE_SET_R12_CONTINUATION.inp user=f42_unified_12dof_active_set_uel.for interactive
'''
(R12_DIR / "run_pkg108_r12_datacheck.sh").write_text(datacheck_sh, encoding="utf-8")

# 6. Create submit_M1_C3_ACTIVE_SET_R12.pbs
pbs_content = '''#!/bin/bash
#PBS -N M1_C3_ACTIVE_SET_R12
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r12/pbs_execution.log
#PBS -e /scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r12/pbs_error.log

set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r12"
cd "${RUN_DIR}"

# Storage compliance guard
if [[ "$(pwd -P)" =~ ^/home/ ]]; then
    echo "ERROR: Running under /home is strictly prohibited by HPC storage policy." >&2
    exit 2
fi

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

export NOTIFICATION_CONFIG="${HOME}/.config/adaptive-remeshing/notifications.env"
source ./job_notifications.sh
notification_load_config

notification_install_terminal_trap
notify_start

abaqus python driver_r12_autonomous_continuation.py
'''
(R12_DIR / "submit_M1_C3_ACTIVE_SET_R12.pbs").write_text(pbs_content, encoding="utf-8")

# 7. Compute file hashes and generate PACKAGE_MANIFEST.json
manifest_files = {}
for fname in [
    "M1_C3_ACTIVE_SET_R12_CONTINUATION.inp",
    "f42_unified_12dof_active_set_uel.for",
    "stage_a_all_d0_boundary_cards.inc",
    "active_set_boundary_cards.inc",
    "d_lower_bounds.csv",
    "driver_r12_autonomous_continuation.py",
    "run_pkg108_r12_datacheck.sh",
    "submit_M1_C3_ACTIVE_SET_R12.pbs",
    "job_notifications.sh"
]:
    p = R12_DIR / fname
    h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
    manifest_files[fname] = h

manifest = {
    "package_name": "PACKAGE_108_R12_C3_AUTONOMOUS_ACTIVE_SET",
    "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
    "turn": 142,
    "model": "pandey_kumar_mode1",
    "continuation_step": "C3",
    "displacement_increment_nm": 1.0,
    "target_rp_u2_mm": 0.00196610735,
    "formulation": "UNIFIED_12DOF_MONOLITHIC_COUPLED_UEL_AUTONOMOUS_ACTIVE_SET",
    "files": manifest_files
}

(R12_DIR / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

# 8. Create M1_C3_ACTIVE_SET_R12_AUTHORIZATION.json
auth = {
    "schema": 1,
    "adapter": "mode1-experimental-12dof-v1",
    "scientific_scope": "MODE1",
    "technical_stage": "C1-1",
    "batch_name": "MODE1_C3_ACTIVE_SET_CONTINUATION_R12",
    "configuration": "UNIFIED_12DOF_AUTONOMOUS_ACTIVE_SET",
    "hypothesis": "Deploying the autonomous active-set iteration driver in genuine Abaqus/Standard 2023 eliminates R11's artificial crack-tip damage locking (Delta_d = 0) without relying on a precomputed oracle mask, progressively discovering the active crack band, relaxing reaction force monotonically toward 180.25 N (+0.14%), preserving strict Stage-A checkpoint reset semantics, and verifying KKT complementarity in genuine Abaqus.",
    "automatic_retry": False,
    "max_submissions": 1,
    "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r12",
    "files": manifest_files,
    "jobs": [
        {
            "id": "M1_C3_ACTIVE_SET_R12",
            "purpose": "Abaqus 2023 Candidate C3 autonomous active-set continuation driver (R12)",
            "input": "M1_C3_ACTIVE_SET_R12_CONTINUATION.inp",
            "user_subroutine": "f42_unified_12dof_active_set_uel.for",
            "pbs": "submit_M1_C3_ACTIVE_SET_R12.pbs",
            "datacheck": "M1_C3_ACTIVE_SET_R12.dat",
            "queue": "entry_imfdfkmq",
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "execution": "single-rank serial",
            "max_submissions": 1,
            "command": 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r12/submit_M1_C3_ACTIVE_SET_R12.pbs"',
            "command_sha256": hashlib.sha256('powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r12/submit_M1_C3_ACTIVE_SET_R12.pbs"'.encode("utf-8")).hexdigest(),
            "depends_on": []
        }
    ],
    "acceptance": {
        "stage_A_same_load": {
            "u_top_target_mm": 0.00196510735,
            "rf2_expected_N": 184.851,
            "rf2_continuity_pct_max": 1.0,
            "kkt_violations_max": 0
        },
        "stage_B_forward_continuation": {
            "delta_u_mm": 1e-06,
            "u_top_target_mm": 0.00196610735,
            "expected_rf2_N_approx": 180.5077,
            "rf2_tolerance_pct": 2.0,
            "expected_allse_mJ_approx": 0.1818,
            "allse_tolerance_pct": 2.0,
            "expected_dmax_approx": 0.7006,
            "dmax_tolerance_pct": 5.0,
            "kkt_violations_max": 0,
            "healing_magnitude_max": 1e-08
        }
    }
}

(R12_DIR / "M1_C3_ACTIVE_SET_R12_AUTHORIZATION.json").write_text(json.dumps(auth, indent=2), encoding="utf-8")

print(f"Successfully generated all Package 108 Revision 12 deliverables in: {R12_DIR}")

if __name__ == "__main__":
    pass
