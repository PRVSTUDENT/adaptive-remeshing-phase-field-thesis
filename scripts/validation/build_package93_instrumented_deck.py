#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package93_instrumented_deck.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: b13e68ac-0d42-4db1-ae22-779415f0ae6e
Protocol Version: 2

Constructs Package 93: Faithful Instrumented C3 Control for Authentic Gauss-Point History Recovery.
1. Uses identical physical C3 mesh (2,650 quads, 2,769 nodes) and mapped state from Package 90-R1.
2. Incorporates Layer 3 companion visualization elements (IDs 5301..7950, CPE4, elset=UMATELEM)
   overlaying physical elements via the frozen f42_mixed_uel.for UMAT visualization bridge.
3. Sets companion UMAT material properties: E=210.0, nu=0.3, N_PHYS=2650.0, DEPVAR=20.
4. Preserves EXACT Package 90-R1 active-set boundary conditions in Step 4:
   Corridor: (0.035 <= x <= 0.075) and (|y - 0.050| <= 0.008) and (d >= 0.15)
   Yields exactly 548 free crack-band nodes and 2,221 clamped far-field nodes (0 healing nodes).
5. Adds *Element Output, elset=UMATELEM: SDV, S, E at frequency=1 in Steps 1-4,
   enabling direct export of solver-committed history H (SDV2/SDV16) at all 10,600 Gauss points.
6. Target horizon: u2 = 0.0020480 mm with 8 increments, reaching Frame 6 at t = 0.65625 (u = 0.0020367 mm).
"""

import os
import sys
import shutil
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG90_R1_DIR = REPO_ROOT / "models/pandey_kumar_mode1/90_r1_c3_active_set_transfer"
OUT_DIR = REPO_ROOT / "models/pandey_kumar_mode1/93_c3_package93_instrumented_control"

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
CONTINUATION_U = 0.00204800000

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Constructing Package 93 in:", OUT_DIR)

    # 1. Copy frozen UEL
    src_uel = PKG90_R1_DIR / "f42_mixed_uel.for"
    dst_uel = OUT_DIR / "f42_mixed_uel.for"
    shutil.copy2(src_uel, dst_uel)
    actual_uel_hash = sha256_file(dst_uel)
    assert actual_uel_hash == FROZEN_UEL_HASH, f"Frozen UEL hash mismatch: {actual_uel_hash} vs {FROZEN_UEL_HASH}"
    print(f"Verified Frozen UEL hash: {actual_uel_hash}")

    # 2. Copy job notifications script
    src_notif = PKG90_R1_DIR / "job_notifications.sh"
    dst_notif = OUT_DIR / "job_notifications.sh"
    shutil.copy2(src_notif, dst_notif)

    # 3. Copy candidate C3 mesh and mapped state table
    shutil.copy2(PKG90_R1_DIR / "candidate_crack_band_mesh_c3.inp", OUT_DIR / "candidate_crack_band_mesh_c3.inp")
    shutil.copy2(PKG90_R1_DIR / "candidate_c3_frame89_mapped_state_table.csv", OUT_DIR / "candidate_c3_frame89_mapped_state_table.csv")

    # 4. Parse C3 mesh element connectivity for 2,650 quads
    c3_mesh_path = OUT_DIR / "candidate_crack_band_mesh_c3.inp"
    mesh_text = c3_mesh_path.read_text(encoding="utf-8")

    # Extract element lines for Layer 1 (1..2650)
    l1_text = mesh_text.split("*Element, type=U1, elset=PHASE_QUADS\n")[1].split("** ==========================================================\n** LAYER 2")[0].strip()
    l1_lines = [l.strip() for l in l1_text.splitlines() if l.strip()]
    assert len(l1_lines) == 2650, f"Expected 2650 quads, got {len(l1_lines)}"

    # Generate Layer 3 Visualization Overlay (CPE4, IDs 5301..7950)
    l3_elem_lines = [
        "** ==========================================================",
        "** LAYER 3: Companion Visualization Elements (CPE4, 5301..7950)",
        "** Evaluated by frozen f42_mixed_uel.for UMAT visualization bridge",
        "** ==========================================================",
        "*Element, type=CPE4, elset=UMATELEM"
    ]
    for l in l1_lines:
        parts = [p.strip() for p in l.split(",")]
        eid = int(parts[0])
        l3_eid = eid + 5300
        l3_elem_lines.append(f"{l3_eid}, " + ", ".join(parts[1:]))

    # Add Companion Material definition
    companion_mat_lines = [
        "** ==========================================================",
        "** SOLID SECTION FOR COMPANION VISUALIZATION OVERLAY",
        "** Tangent stiffness 1.0E-11 adds zero load to physical solution",
        "** ==========================================================",
        "*Solid Section, elset=UMATELEM, material=DUMMY_MAT",
        "1.0,",
        "*Material, name=DUMMY_MAT",
        "*User Material, constants=3",
        "210.0, 0.3, 2650.0",
        "*Depvar",
        "20"
    ]

    # Load node coordinates and mapped damage
    nodes = {}
    reading = False
    for l in mesh_text.splitlines():
        t = l.strip()
        if t.startswith("*Node"):
            reading = True
            continue
        if t.startswith("*") and reading:
            break
        if reading and t:
            parts = [p.strip() for p in t.split(",")]
            if len(parts) >= 3 and parts[0].isdigit():
                nid = int(parts[0])
                if nid != 999999:
                    nodes[nid] = (float(parts[1]), float(parts[2]))

    d_mapped = {}
    with open(OUT_DIR / "candidate_c3_frame89_mapped_state_table.csv", "r", encoding="utf-8") as f:
        for row in f:
            parts = [p.strip() for p in row.split(",")]
            if parts and parts[0] == "NODE":
                d_mapped[int(parts[1])] = float(parts[4])

    phys_nodes = sorted(nodes.keys())
    assert len(phys_nodes) == 2769, f"Expected 2769 nodes, got {len(phys_nodes)}"

    # Parse base deck from Package 90-R1
    src_inp = PKG90_R1_DIR / "M1_C3_PACKAGE90_R1_TRANSFER.inp"
    src_lines = src_inp.read_text(encoding="utf-8").splitlines()

    # Find where LAYER 2 elements end in the base deck (before UEL PROPERTIES)
    insert_l3_idx = -1
    for i, line in enumerate(src_lines):
        if "** UEL PROPERTIES" in line or "** ==========================================================\n** UEL PROPERTIES" in line:
            insert_l3_idx = i
            break
    assert insert_l3_idx > 0, "Could not find UEL PROPERTIES in Package 90-R1 deck"

    # Search backward for header comment
    while insert_l3_idx > 0 and src_lines[insert_l3_idx - 1].strip().startswith("**"):
        insert_l3_idx -= 1

    part1_lines = src_lines[:insert_l3_idx]

    # Find Step 4 in Package 90-R1
    step4_idx = -1
    for i, line in enumerate(src_lines):
        if "*Step, name=FORWARD_CONTINUATION" in line:
            step4_idx = i
            break
    assert step4_idx > 0, "Could not find Step 4 in Package 90-R1 deck"

    cut_step4_idx = step4_idx
    while cut_step4_idx > 0 and src_lines[cut_step4_idx - 1].strip().startswith("**"):
        cut_step4_idx -= 1

    part2_lines = src_lines[insert_l3_idx:cut_step4_idx]

    # In Steps 1-3, ensure companion element output is requested
    modified_part2 = []
    i = 0
    while i < len(part2_lines):
        line = part2_lines[i]
        modified_part2.append(line)
        if line.strip() == "*Node Output" and i + 1 < len(part2_lines) and "U" in part2_lines[i + 1]:
            # Append the nodal output line (e.g. U, RF) first
            i += 1
            modified_part2.append(part2_lines[i])
            # Then append element output for companion visualizer overlay
            modified_part2.append("*Element Output, elset=UMATELEM")
            modified_part2.append("SDV, S, E")
        i += 1

    # Exact Package 90-R1 active set corridor:
    # 2,221 clamped far-field nodes, 548 free crack-band nodes
    step4_lines = [
        "** ==========================================================",
        f"** STEP 4: FORWARD_CONTINUATION (Loading to u = {CONTINUATION_U:.8f} mm)",
        "** Faithful Package 90-R1 Active-Set Irreversibility Preserved:",
        "** 2,221 far-field nodes clamped to d_mapped (zero healing guaranteed)",
        "** 548 crack-band nodes free to advance damage monotonically under tensile strain",
        "** Layer 3 companion elements output solver-committed SDVs at frequency=1",
        "** ==========================================================",
        "*Step, name=FORWARD_CONTINUATION, nlgeom=NO, inc=100",
        "*Static",
        "0.05, 1.0, 1e-8, 0.2",
        "*Boundary, OP=NEW",
        "N_BOTTOM, 2, 2, 0.0",
        "N_PIN, 1, 1, 0.0",
        "N_RP, 1, 1, 0.0",
        f"N_RP, 2, 2, {CONTINUATION_U:.10e}"
    ]

    active_count = 0
    inactive_count = 0
    for nid in phys_nodes:
        pt = nodes[nid]
        d = d_mapped[nid]
        dist_y = abs(pt[1] - 0.050)
        # Exact Package 90-R1 corridor
        in_band = (0.035 <= pt[0] <= 0.075) and (dist_y <= 0.008)
        if (not in_band) or (d < 0.15):
            # Inactive node: clamp DOF 3 to d_mapped
            step4_lines.append(f"{nid}, 3, 3, {d:.10e}")
            inactive_count += 1
        else:
            active_count += 1

    print(f"Package 93 Step 4: {inactive_count} nodes clamped, {active_count} nodes free in crack band.")
    assert inactive_count == 2221, f"Expected 2221 clamped nodes, got {inactive_count}"
    assert active_count == 548, f"Expected 548 free crack-band nodes, got {active_count}"

    step4_lines.extend([
        "*Output, field, frequency=1",
        "*Node Output",
        "U, RF",
        "*Element Output, elset=UMATELEM",
        "SDV, S, E",
        "*Output, history, frequency=1",
        "*Node Output, nset=N_RP",
        "RF2, U2",
        "*Energy Output",
        "ALLSE, ALLWK, ALLFD, ALLIE",
        "*End Step"
    ])

    pkg93_deck = part1_lines + l3_elem_lines + companion_mat_lines + modified_part2 + step4_lines
    dst_inp = OUT_DIR / "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.inp"
    dst_inp.write_text("\n".join(pkg93_deck) + "\n", encoding="utf-8")
    inp_sha = sha256_file(dst_inp)
    print(f"Generated Package 93 deck: {dst_inp} ({len(pkg93_deck)} lines, SHA256={inp_sha})")

    # 5. PBS Submission Script (pure LF)
    pbs_content = f"""#!/bin/bash
#PBS -N M1_C3_P93_INST
#PBS -l select=1:ncpus=1:mem=8gb
#PBS -l walltime=04:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_package93_c3_instrumented_control/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_package93_c3_instrumented_control"
cd "${{RUN_DIR}}"

export JOB_NAME="M1_C3_PACKAGE93_INSTRUMENTED_REPLAY"
export NOTIFICATION_CONFIG="${{NOTIFICATION_CONFIG:-${{HOME}}/.config/adaptive-remeshing/notifications.env}}"
source "${{RUN_DIR}}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

export XDG_RUNTIME_DIR="${{XDG_RUNTIME_DIR:-/tmp/xdg_runtime_${{USER}}}}"
mkdir -p "${{XDG_RUNTIME_DIR}}"
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

JOB_NAME="M1_C3_PACKAGE93_INSTRUMENTED_REPLAY"
INP_NAME="M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.inp"
USER_SUB="f42_mixed_uel.for"

test ! -e "${{JOB_NAME}}.lck"

echo "Starting Abaqus analysis ${{JOB_NAME}} at $(date)"
abaqus job="${{JOB_NAME}}" input="${{INP_NAME}}" user="${{USER_SUB}}" cpus=1 interactive
EXIT_CODE=$?
echo "Abaqus completed with exit code ${{EXIT_CODE}} at $(date)"

exit ${{EXIT_CODE}}
"""
    dst_pbs = OUT_DIR / "submit_M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.pbs"
    with open(dst_pbs, "wb") as f:
        f.write(pbs_content.replace("\r\n", "\n").encode("utf-8"))
    pbs_sha = sha256_file(dst_pbs)
    print(f"Generated PBS script: {dst_pbs} (SHA256={pbs_sha})")

    # 6. Datacheck Script (pure LF)
    dc_content = f"""#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_package93_c3_instrumented_control"
cd "${{RUN_DIR}}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

JOB_NAME="M1_C3_PACKAGE93_INSTRUMENTED_REPLAY_DC"
INP_NAME="M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.inp"
USER_SUB="f42_mixed_uel.for"

echo "Starting Datacheck ${{JOB_NAME}} at $(date)"
abaqus job="${{JOB_NAME}}" input="${{INP_NAME}}" user="${{USER_SUB}}" datacheck interactive
EXIT_CODE=$?
echo "Datacheck completed with exit code ${{EXIT_CODE}} at $(date)"
exit ${{EXIT_CODE}}
"""
    dst_dc = OUT_DIR / "run_pkg93_datacheck.sh"
    with open(dst_dc, "wb") as f:
        f.write(dc_content.replace("\r\n", "\n").encode("utf-8"))
    dc_sha = sha256_file(dst_dc)
    print(f"Generated Datacheck script: {dst_dc} (SHA256={dc_sha})")

    # 7. Package Manifest
    manifest = {
        "package_name": "93_c3_package93_instrumented_control",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "run_id": "b13e68ac-0d42-4db1-ae22-779415f0ae6e",
        "model_type": "Mode-I Phase-Field C3 Replay with Layer 3 Companion Overlay and Faithful Active Set",
        "job_name": "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY",
        "input_deck": "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.inp",
        "input_deck_sha256": inp_sha,
        "user_subroutine": "f42_mixed_uel.for",
        "user_subroutine_sha256": actual_uel_hash,
        "scratch_directory": "/scratch9/pr21vyci/runs/mode1_package93_c3_instrumented_control",
        "pbs_script": "submit_M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.pbs",
        "datacheck_script": "run_pkg93_datacheck.sh",
        "resources": {
            "cpus": 1,
            "memory_gb": 8,
            "walltime": "04:00:00",
            "queue": "entry_imfdfkmq"
        },
        "discretization": {
            "physical_quads": 2650,
            "physical_nodes": 2769,
            "layer_1_phase_elements": "1..2650 (U1)",
            "layer_2_mech_elements": "2651..5300 (U2)",
            "layer_3_companion_elements": "5301..7950 (CPE4, UMATELEM)",
            "total_gauss_points": 10600
        },
        "active_set_partition": {
            "clamped_far_field_nodes": 2221,
            "free_crack_band_nodes": 548,
            "corridor_definition": "0.035 <= x <= 0.075 and |y - 0.050| <= 0.008 and d >= 0.15"
        },
        "acceptance_criteria": {
            "gate1_force_parity_vs_pkg90_r1_pct": 0.05,
            "gate2_raw_uel_energy_parity_pct": 0.05,
            "gate3_damage_bounds_frame6": "d_max <= 1.00000 (0 overshoot nodes)",
            "gate4_zero_healing": "0 healing nodes (min delta_d >= 0 everywhere)",
            "gate5_authentic_history_recovery": "Export solver-committed STATEV(2)/STATEV(16) at all 10,600 Gauss points"
        }
    }
    manifest_path = OUT_DIR / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    manifest_sha = sha256_file(manifest_path)
    print(f"Generated Manifest: {manifest_path} (SHA256={manifest_sha})")

    # 8. Guarded SSH Command & Authorization JSON
    notif_sha = sha256_file(dst_notif)
    remote_pbs_path = "/scratch9/pr21vyci/runs/mode1_package93_c3_instrumented_control/submit_M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.pbs"
    guarded_cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {remote_pbs_path}"'
    cmd_sha = hashlib.sha256(guarded_cmd.encode("utf-8")).hexdigest().lower()

    auth_json = {
        "batch_name": "MODE1_PACKAGE_93_C3_INSTRUMENTED_CONTROL",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_package93_c3_instrumented_control",
        "files": {
            "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.inp": inp_sha.lower(),
            "f42_mixed_uel.for": actual_uel_hash.lower(),
            "job_notifications.sh": notif_sha.lower(),
            "submit_M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.pbs": pbs_sha.lower(),
            "PACKAGE_MANIFEST.json": manifest_sha.lower()
        },
        "jobs": [
            {
                "id": "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY",
                "pbs": "submit_M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.pbs",
                "command": guarded_cmd,
                "command_sha256": cmd_sha,
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Package 93: faithful instrumented C3 control with Layer 3 companion elements and exact Package 90-R1 active set for authentic Gauss-point history recovery",
                "cpus": 1,
                "memory_gb": 8,
                "walltime_hours": 4,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial",
                "input": "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.inp",
                "datacheck": "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY_DC.dat"
            }
        ],
        "acceptance": {
            "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY": "Exit code 0 across 4 steps; holding reaction force within 0.05% of Package 90-R1 (159.16 N); active set irreversibility preserved (0 healing nodes); authentic committed Gauss-point history H exported via Layer 3 companion overlay (10,600 Gauss points) into ODB SDV2/SDV16."
        }
    }
    auth_path = OUT_DIR / "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY_AUTHORIZATION.json"
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(auth_json, f, indent=2)
    auth_sha = sha256_file(auth_path)
    print(f"Generated Authorization: {auth_path} (SHA256={auth_sha})")
    print(f"Guarded Command SHA256: {cmd_sha}")

if __name__ == "__main__":
    main()
