#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_mode1_turn113_c3_continuation_package.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 113)
Protocol Version: 2

Generates the complete genuine Abaqus 2023 Candidate C3 continuation package:
1. Computes the authentic Turn 107 re-equilibrated state (u, d, H) on Candidate C3.
2. Writes d_lower_bounds.csv for all 2,650 C3 quad elements (10,600 Gauss points).
3. Constructs M1_C3_IRREV_CONTINUATION.inp (2-step Abaqus deck: Stage A same-load, Stage B +5 nm continuation).
4. Packages f42_experimental_irreversible_uel.for, PBS scripts, notifications, and manifest.
5. Computes and records all SHA-256 hashes.
"""

import sys
import os
import json
import math
import shutil
import hashlib
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))

from evaluate_corrected_c3_coupled_transfer_and_increment import (
    C2_INP, C2_CSV, C3_MESH_INP,
    E_MOD, NU, E_GC, E_L0, K_DEGRAD,
    UEL_GP_COORDS, UEL_WEIGHTS, shape_functions,
    parse_mesh, load_c2_donor_state, classify_slit_flanks,
    build_fe_interpolator, solve_coupled_staggered,
    compute_plane_strain_c0, solve_elasticity_uel, compute_energies_uel
)

PACKAGE_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "105_c3_irreversible_continuation"
EXP_UEL_SRC = REPO_ROOT / "models" / "pandey_kumar_mode1" / "104_experimental_irreversible_uel" / "f42_experimental_irreversible_uel.for"
NOTIF_SRC = REPO_ROOT / "models" / "pandey_kumar_mode1" / "104_experimental_irreversible_uel" / "diagnostic_patch" / "job_notifications.sh"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    print("=" * 80, flush=True)
    print("TURN 113: BUILDING CANDIDATE C3 EXPERIMENTAL IRREVERSIBLE PACKAGE", flush=True)
    print("=" * 80, flush=True)

    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Parse C2 donor and C3 recipient meshes
    print("\n[1/5] Loading meshes and donor state...", flush=True)
    nodes_c2, elements_c2, nlist_c2, n2idx_c2 = parse_mesh(C2_INP, max_phys_eid=2300)
    u_c2, d_c2, elem_H_c2 = load_c2_donor_state(C2_CSV, n2idx_c2, max_phys_eid=2300)
    flanks_c2 = classify_slit_flanks(nodes_c2, elements_c2)

    nodes_c3, elements_c3, nlist_c3, n2idx_c3 = parse_mesh(C3_MESH_INP, max_phys_eid=2650)
    flanks_c3 = classify_slit_flanks(nodes_c3, elements_c3)
    n_nodes_c3 = len(nlist_c3)
    n_elems_c3 = len(elements_c3)
    print(f"  C3 Discretization: {n_nodes_c3} nodes, {n_elems_c3} elements.", flush=True)

    # 2. Build FE interpolator and project continuous fields
    print("\n[2/5] Projecting continuous donor fields onto C3...", flush=True)
    locate_c2 = build_fe_interpolator(nodes_c2, elements_c2, flanks_c2)
    u_c3_mapped = np.zeros((n_nodes_c3, 2))
    d_c3_mapped = np.zeros(n_nodes_c3)

    for nid in nlist_c3:
        idx = n2idx_c3[nid]
        pt = nodes_c3[nid]
        fl = flanks_c3[nid]
        eid, xi, eta = locate_c2(pt[0], pt[1], fl)
        conn = elements_c2[eid]
        N, _, _ = shape_functions(xi, eta)

        u1 = sum(N[k] * u_c2[n2idx_c2[conn[k]], 0] for k in range(4))
        u2 = sum(N[k] * u_c2[n2idx_c2[conn[k]], 1] for k in range(4))
        dam = sum(N[k] * d_c2[n2idx_c2[conn[k]]] for k in range(4))
        dam = max(0.0, min(1.0, dam))

        u_c3_mapped[idx, 0] = u1
        u_c3_mapped[idx, 1] = u2
        d_c3_mapped[idx] = dam

    # Gauss point history mapping
    s3 = math.sqrt(3.0)
    elem_H_c3_pure = {}
    for eid, conn in elements_c3.items():
        coords = np.array([nodes_c3[n] for n in conn])
        h_list = []
        for kpt in range(4):
            xi, eta = UEL_GP_COORDS[kpt]
            N, _, _ = shape_functions(xi, eta)
            gx = float(np.dot(N, coords[:, 0]))
            gy = float(np.dot(N, coords[:, 1]))
            fl = "upper" if gy > 0.050 else ("lower" if gy < 0.050 else "intact")

            donor_eid, d_xi, d_eta = locate_c2(gx, gy, fl)
            xi_gp = max(-1.0, min(1.0, d_xi * s3))
            eta_gp = max(-1.0, min(1.0, d_eta * s3))
            N_gp, _, _ = shape_functions(xi_gp, eta_gp)

            donor_h = elem_H_c2[donor_eid]
            h_interp = max(0.0, float(sum(N_gp[k] * donor_h[k] for k in range(4))))
            h_list.append(h_interp)
        elem_H_c3_pure[eid] = h_list

    # 3. Coupled Same-Load Re-Equilibration at u = 0.00196510735 mm
    u_prescribed = 0.00196510735
    print(f"\n[3/5] Solving coupled re-equilibration at u = {u_prescribed:.9f} mm...", flush=True)
    res_equil = solve_coupled_staggered(
        nodes=nodes_c3, elements=elements_c3, node_list=nlist_c3, node_to_idx=n2idx_c3,
        d_init=d_c3_mapped, d_lower_bounds=d_c3_mapped, elem_H_base=elem_H_c3_pure,
        u_top=u_prescribed, tol_stagger=1e-5, max_iters=25, update_H=True
    )
    d_equil = res_equil["d"]
    u_equil = res_equil["u"]
    elem_H_equil = res_equil["elem_H"]

    print(f"  Converged in {res_equil['iterations']} iters (Status: {res_equil['converged']}).", flush=True)
    print(f"  RF2:    {res_equil['rf2_N']:.4f} N", flush=True)
    print(f"  E_frac: {res_equil['e_frac_mJ']:.6f} mJ", flush=True)
    print(f"  d_max:  {res_equil['d_max']:.6f}", flush=True)

    # Save state artifact
    state_record = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "turn": 113,
        "u_top_mm": u_prescribed,
        "rf2_N": res_equil["rf2_N"],
        "e_frac_mJ": res_equil["e_frac_mJ"],
        "e_elas_mJ": res_equil["e_elas_mJ"],
        "d_max": res_equil["d_max"],
        "n_nodes": n_nodes_c3,
        "n_elements": n_elems_c3,
        "iterations": res_equil["iterations"]
    }
    state_json_path = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "turn113_c3_equilibrated_state.json"
    with open(state_json_path, "w", encoding="utf-8") as f:
        json.dump(state_record, f, indent=2)

    # 4. Write d_lower_bounds.csv for Candidate C3
    print("\n[4/5] Writing d_lower_bounds.csv...", flush=True)
    d_bounds_csv = PACKAGE_DIR / "d_lower_bounds.csv"
    with open(d_bounds_csv, "w", encoding="utf-8") as f:
        f.write("EID, D0_1, D0_2, D0_3, D0_4, H0_1, H0_2, H0_3, H0_4\n")
        for eid in sorted(elements_c3.keys()):
            conn = elements_c3[eid]
            d_nodal = [float(d_equil[n2idx_c3[n]]) for n in conn]
            h_gps = [float(h) for h in elem_H_equil[eid]]
            row_str = f"{eid}, " + ", ".join(f"{v:.10e}" for v in d_nodal) + ", " + ", ".join(f"{v:.10e}" for v in h_gps) + "\n"
            f.write(row_str)

    d_bounds_sha = sha256_file(d_bounds_csv)
    print(f"  d_lower_bounds.csv created ({n_elems_c3} rows, SHA-256: {d_bounds_sha})", flush=True)

    # 5. Build M1_C3_IRREV_CONTINUATION.inp
    print("\n[5/5] Building Abaqus 2023 input deck M1_C3_IRREV_CONTINUATION.inp...", flush=True)
    inp_path = PACKAGE_DIR / "M1_C3_IRREV_CONTINUATION.inp"

    # Read base mesh nodes and equations from C3_MESH_INP
    with open(C3_MESH_INP, "r", encoding="utf-8") as f:
        mesh_text = f.read()

    # Extract Node section
    node_start = mesh_text.find("*Node\n")
    node_end = mesh_text.find("** ==========================================================\n** USER ELEMENTS", node_start)
    if node_end == -1:
        node_end = mesh_text.find("*Element", node_start)
    node_section = mesh_text[node_start:node_end].strip()

    # Extract Sets and Equations
    sets_start = mesh_text.find("** ==========================================================\n** NODE SETS & BOUNDARY CONDITIONS")
    if sets_start == -1:
        sets_start = mesh_text.find("*Nset, nset=N_BOTTOM")
    
    # Extract until the Step keyword
    step_start = mesh_text.find("*Step", sets_start)
    sets_and_eq_section = mesh_text[sets_start:step_start].strip()

    # Build full input deck
    deck_lines = []
    deck_lines.append("*Heading")
    deck_lines.append("** Candidate C3: Authentic Two-Step Irreversible UEL Continuation")
    deck_lines.append("** Elements: 2,650 Quads, Nodes: 2,769 physical + RP 999999")
    deck_lines.append(f"** Parameters: E={E_MOD} kN/mm^2, nu={NU}, Gc={E_GC} kN/mm, l0={E_L0} mm, k={K_DEGRAD}, N_PHYS={n_elems_c3}")
    deck_lines.append("** Step 1 (Stage A): Same-load re-equilibration at u_RP = 0.00196510735 mm")
    deck_lines.append("** Step 2 (Stage B): +5 nm forward continuation to u_RP = 0.00197010735 mm")
    deck_lines.append("*Preprint, echo=NO, model=NO, history=NO, contact=NO")
    deck_lines.append("** ----------------------------------------------------------------")
    deck_lines.append("** USER ELEMENTS (Phase U1: 1..2650, Mech U2: 2651..5300)")
    deck_lines.append("** ----------------------------------------------------------------")
    deck_lines.append("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    deck_lines.append("3")
    deck_lines.append("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    deck_lines.append("1, 2")
    deck_lines.append("** ----------------------------------------------------------------")
    deck_lines.append(node_section)
    deck_lines.append("** ----------------------------------------------------------------")
    deck_lines.append("** LAYER 1: Phase Elements (Type U1: 1..2650)")
    deck_lines.append("** ----------------------------------------------------------------")
    deck_lines.append("*Element, type=U1, elset=PHASE_QUADS")
    for eid in sorted(elements_c3.keys()):
        conn = elements_c3[eid]
        deck_lines.append(f"{eid}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}")

    deck_lines.append("** ----------------------------------------------------------------")
    deck_lines.append("** LAYER 2: Mechanical Elements (Type U2: 2651..5300)")
    deck_lines.append("** ----------------------------------------------------------------")
    deck_lines.append("*Element, type=U2, elset=MECH_QUADS")
    for eid in sorted(elements_c3.keys()):
        conn = elements_c3[eid]
        deck_lines.append(f"{eid + n_elems_c3}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}")

    deck_lines.append("** ----------------------------------------------------------------")
    deck_lines.append("** LAYER 3: Visualization CPE4 Elements (5301..7950)")
    deck_lines.append("** ----------------------------------------------------------------")
    deck_lines.append("*Element, type=CPE4, elset=VIS_QUADS")
    for eid in sorted(elements_c3.keys()):
        conn = elements_c3[eid]
        deck_lines.append(f"{eid + 2 * n_elems_c3}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}")

    deck_lines.append("** ----------------------------------------------------------------")
    deck_lines.append("** UEL PROPERTIES (l0, Gc, E, nu, k, N_PHYS)")
    deck_lines.append("** ----------------------------------------------------------------")
    deck_lines.append("*UEL PROPERTY, ELSET=PHASE_QUADS")
    deck_lines.append(f"{E_L0}, {E_GC}, {E_MOD}, {NU}, {K_DEGRAD}, {float(n_elems_c3)}")
    deck_lines.append("*UEL PROPERTY, ELSET=MECH_QUADS")
    deck_lines.append(f"{E_L0}, {E_GC}, {E_MOD}, {NU}, {K_DEGRAD}, {float(n_elems_c3)}")
    deck_lines.append("** ----------------------------------------------------------------")
    deck_lines.append("** VISUALIZATION SOLID SECTION & UMAT")
    deck_lines.append("** ----------------------------------------------------------------")
    deck_lines.append("*Solid Section, elset=VIS_QUADS, material=DUMMY_MAT")
    deck_lines.append("1.0")
    deck_lines.append("*Material, name=DUMMY_MAT")
    deck_lines.append("*User Material, constants=3")
    deck_lines.append(f"{E_MOD}, {NU}, {float(n_elems_c3)}")
    deck_lines.append("*Depvar")
    deck_lines.append("18")
    deck_lines.append("** ----------------------------------------------------------------")
    deck_lines.append(sets_and_eq_section)
    deck_lines.append("** ================================================================")
    deck_lines.append("** STEP 1: Stage-A Same-Load Re-Equilibration at u = 0.00196510735 mm")
    deck_lines.append("** ================================================================")
    deck_lines.append("*Step, name=Stage-A, nlgeom=NO, inc=25")
    deck_lines.append("*Static")
    deck_lines.append("1.0, 1.0, 1.0E-5, 1.0")
    deck_lines.append("*Boundary")
    deck_lines.append("N_BOTTOM, 2, 2, 0.0")
    deck_lines.append("N_PIN, 1, 1, 0.0")
    deck_lines.append("N_TOP, 1, 1, 0.0")
    deck_lines.append(f"N_RP, 2, 2, {u_prescribed:.11f}")
    deck_lines.append("*Output, field, frequency=1")
    deck_lines.append("*Node Output")
    deck_lines.append("U, RF")
    deck_lines.append("*Element Output, elset=VIS_QUADS")
    deck_lines.append("SDV, S, E")
    deck_lines.append("*Output, history, frequency=1")
    deck_lines.append("*Energy Output")
    deck_lines.append("ALLSE, ALLIE, ALLWK, ALLFD, ALLCD, ALLVD, ALLPD, ALLAE, ETOTAL")
    deck_lines.append("*End Step")
    deck_lines.append("** ================================================================")
    deck_lines.append("** STEP 2: Stage-B Forward Continuation (+5 nm) to u = 0.00197010735 mm")
    deck_lines.append("** ================================================================")
    deck_lines.append("*Step, name=Stage-B, nlgeom=NO, inc=50")
    deck_lines.append("*Static")
    deck_lines.append("0.1, 1.0, 1.0E-5, 0.2")
    deck_lines.append("*Boundary")
    deck_lines.append(f"N_RP, 2, 2, {u_prescribed + 0.000005:.11f}")
    deck_lines.append("*Output, field, frequency=1")
    deck_lines.append("*Node Output")
    deck_lines.append("U, RF")
    deck_lines.append("*Element Output, elset=VIS_QUADS")
    deck_lines.append("SDV, S, E")
    deck_lines.append("*Output, history, frequency=1")
    deck_lines.append("*Energy Output")
    deck_lines.append("ALLSE, ALLIE, ALLWK, ALLFD, ALLCD, ALLVD, ALLPD, ALLAE, ETOTAL")
    deck_lines.append("*End Step\n")

    with open(inp_path, "w", encoding="utf-8") as f:
        f.write("\n".join(deck_lines))

    inp_sha = sha256_file(inp_path)
    print(f"  M1_C3_IRREV_CONTINUATION.inp created (SHA-256: {inp_sha})", flush=True)

    # Copy UEL source and notifications
    uel_dest = PACKAGE_DIR / "f42_experimental_irreversible_uel.for"
    shutil.copy2(EXP_UEL_SRC, uel_dest)
    uel_sha = sha256_file(uel_dest)

    notif_dest = PACKAGE_DIR / "job_notifications.sh"
    shutil.copy2(NOTIF_SRC, notif_dest)
    notif_sha = sha256_file(notif_dest)

    # PBS script
    pbs_path = PACKAGE_DIR / "submit_M1_C3_IRREV.pbs"
    pbs_content = f"""#PBS -N M1_C3_IRREV
#PBS -l nodes=1:ppn=1
#PBS -l mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -o pbs_execution.log
#PBS -e pbs_error.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

cd "$PBS_O_WORKDIR" || exit 1
source ./job_notifications.sh

JOB_NAME="M1_C3_IRREV_SOLVE"
INP_NAME="M1_C3_IRREV_CONTINUATION.inp"
USER_SUB="f42_experimental_irreversible_uel.for"

notify_start "$JOB_NAME" "$PBS_JOBID"
notification_install_terminal_trap "$JOB_NAME" "$PBS_JOBID"

export XDG_RUNTIME_DIR="${{XDG_RUNTIME_DIR:-/tmp/xdg_runtime_${{USER}}}}"
mkdir -p "$XDG_RUNTIME_DIR"

module load abaqus/2023 2>&1 || true

abaqus job="$JOB_NAME" input="$INP_NAME" user="$USER_SUB" double cpus=1 -interactive
EXIT_CODE=$?

exit $EXIT_CODE
"""
    with open(pbs_path, "w", encoding="utf-8") as f:
        f.write(pbs_content)
    pbs_sha = sha256_file(pbs_path)

    # Shell scripts
    dc_sh = PACKAGE_DIR / "run_datacheck.sh"
    with open(dc_sh, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\nset -euo pipefail\ncd \"$(dirname \"$0\")\" || exit 1\nexport XDG_RUNTIME_DIR=\"${XDG_RUNTIME_DIR:-/tmp/xdg_runtime_${USER}}\"\nmkdir -p \"${XDG_RUNTIME_DIR}\"\nmodule load abaqus/2023 2>&1 || true\nabaqus datacheck job=M1_C3_IRREV_DC input=M1_C3_IRREV_CONTINUATION.inp user=f42_experimental_irreversible_uel.for double -interactive\n")
    dc_sha = sha256_file(dc_sh)

    sol_sh = PACKAGE_DIR / "run_solve.sh"
    with open(sol_sh, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\nset -euo pipefail\ncd \"$(dirname \"$0\")\" || exit 1\nexport XDG_RUNTIME_DIR=\"${XDG_RUNTIME_DIR:-/tmp/xdg_runtime_${USER}}\"\nmkdir -p \"${XDG_RUNTIME_DIR}\"\nmodule load abaqus/2023 2>&1 || true\nabaqus job=M1_C3_IRREV_SOLVE input=M1_C3_IRREV_CONTINUATION.inp user=f42_experimental_irreversible_uel.for double -interactive\n")
    sol_sha = sha256_file(sol_sh)

    # Authorization manifest
    manifest_path = PACKAGE_DIR / "M1_C3_IRREV_AUTHORIZATION.json"
    manifest_data = {
        "schema": 1,
        "adapter": "mode1-experimental-irrev-v1",
        "scientific_scope": "MODE1",
        "technical_stage": "C1-1",
        "configuration": "EXPERIMENTAL_IRREVERSIBLE",
        "hypothesis": "Semi-smooth active-set penalty in UEL enforces damage irreversibility during C3 continuation without artificial crack-corridor pinning or wake clamping.",
        "automatic_retry": False,
        "max_submissions": 1,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c3_irreversible_continuation",
        "files": {
            "M1_C3_IRREV_CONTINUATION.inp": inp_sha.lower(),
            "d_lower_bounds.csv": d_bounds_sha.lower(),
            "f42_experimental_irreversible_uel.for": uel_sha.lower(),
            "submit_M1_C3_IRREV.pbs": pbs_sha.lower(),
            "job_notifications.sh": notif_sha.lower(),
            "run_datacheck.sh": dc_sha.lower(),
            "run_solve.sh": sol_sha.lower()
        },
        "jobs": [
            {
                "id": "M1_C3_IRREV_CONTINUATION",
                "purpose": "Abaqus 2023 Candidate C3 state reconstruction and +5 nm continuation with experimental irreversible UEL",
                "input": "M1_C3_IRREV_CONTINUATION.inp",
                "user_subroutine": "f42_experimental_irreversible_uel.for",
                "pbs": "submit_M1_C3_IRREV.pbs",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "command": 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c3_irreversible_continuation/submit_M1_C3_IRREV.pbs"',
                "command_sha256": hashlib.sha256('powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c3_irreversible_continuation/submit_M1_C3_IRREV.pbs"'.encode()).hexdigest(),
                "depends_on": []
            }
        ],
        "acceptance": {
            "stage_A_same_load": {
                "u_top_target_mm": 0.00196510735,
                "rf2_continuity_vs_c2_equil_pct_max": 5.0,
                "ef_continuity_vs_c2_equil_pct_max": 2.0,
                "healing_magnitude_max": 1.0e-8,
                "kkt_violations_max": 0
            },
            "stage_B_forward_continuation": {
                "delta_u_mm": 0.000005,
                "u_top_target_mm": 0.00197010735,
                "expected_rf2_N_approx": 179.3,
                "expected_ef_mJ_approx": 0.0624,
                "monotonic_softening_required": True,
                "monotonic_dissipation_required": True,
                "healing_magnitude_max": 1.0e-8
            }
        }
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print(f"  M1_C3_IRREV_AUTHORIZATION.json created.", flush=True)

    # Deliverables summary
    summary = {
        "status": "PACKAGE_GENERATION_COMPLETE",
        "package_dir": str(PACKAGE_DIR.relative_to(REPO_ROOT)),
        "files": {
            "M1_C3_IRREV_CONTINUATION.inp": inp_sha,
            "d_lower_bounds.csv": d_bounds_sha,
            "f42_experimental_irreversible_uel.for": uel_sha,
            "submit_M1_C3_IRREV.pbs": pbs_sha,
            "job_notifications.sh": notif_sha,
            "run_datacheck.sh": dc_sha,
            "run_solve.sh": sol_sha,
            "M1_C3_IRREV_AUTHORIZATION.json": sha256_file(manifest_path)
        },
        "candidate_c3_metrics": {
            "n_nodes": n_nodes_c3,
            "n_quads": n_elems_c3,
            "u_step1_mm": u_prescribed,
            "rf2_step1_N": res_equil["rf2_N"],
            "ef_step1_mJ": res_equil["e_frac_mJ"],
            "d_max_step1": res_equil["d_max"],
            "u_step2_mm": u_prescribed + 0.000005
        }
    }

    audit_out = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "turn113_c3_package_generation_audit.json"
    with open(audit_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nAudit deliverable saved to: {audit_out}", flush=True)
    return summary

if __name__ == "__main__":
    main()
