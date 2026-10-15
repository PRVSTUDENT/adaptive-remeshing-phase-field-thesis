#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_mode1_stage_c1_0_package.py
====================================
Generates the authoritative Abaqus reproduction package for:
Stage C1-0: Mode-I Method C Identical-Mesh State Transfer & Continuation
- Donor: 2,906-element coarse mesh at u = 0.0050 mm (Job 1411891 / M1_PRE_1S)
- Recipient: Exact same 2,906-element mesh (identical mesh baseline)
- Ingests authentic donor state from coarse_donor_state_u0050.json
- Formulates:
  * Stage C1-0A: Instantaneous static equilibration at u = 0.0050 mm (Delta u = 0)
    to verify reaction force continuity (|Delta RF| < 0.1 N), energy conservation,
    and history non-negativity (H >= 0).
  * Stage C1-0B: Seamless continuation solve from u = 0.0050 mm to 0.0100 mm.
- Output directory: models/pandey_kumar_mode1/47_method_c_stage_c1_0_identical_mesh_continuation/
- Enforces production UEL invariant (SHA-256: CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6).

Task: F1482
Author: Gemini Antigravity
Date: 2026-10-15
"""

import os
import sys
import json
import math
import hashlib
from pathlib import Path

# Resolve repository root
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1] if str(SCRIPT_DIR.parents[1]) not in sys.path else SCRIPT_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.mode1_state_transfer_engine import (
    Mode1Mesh,
    Mode1State,
    Mode1StateTransferEngine,
    parse_mode1_input_deck,
)


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def generate_package_47(output_dir=None):
    if output_dir is None:
        output_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "47_method_c_stage_c1_0_identical_mesh_continuation"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    mesh_inp = REPO_ROOT / "models" / "pandey_kumar_mode1" / "method_b_inf_companion_decks" / "M1_MB_INF_1S.inp"
    donor_json = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "evidence_forward_audit" / "coarse_donor_state_u0050.json"
    frozen_uel = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"

    print("=== MODE-I METHOD C STAGE C1-0 PACKAGE GENERATOR ===", flush=True)
    print(f"Mesh Deck:    {mesh_inp}", flush=True)
    print(f"Donor State:  {donor_json}", flush=True)
    print(f"Frozen UEL:   {frozen_uel}", flush=True)
    print(f"Output Dir:   {output_dir}", flush=True)

    # 1. Parse mesh
    print("\n[1/6] Parsing canonical 2,906-element Mode-I mesh...", flush=True)
    mesh = parse_mode1_input_deck(str(mesh_inp))
    print(f"      Physical mesh: {mesh.num_elements} elements, {mesh.num_nodes} nodes", flush=True)

    # 2. Ingest authentic donor state
    print("\n[2/6] Ingesting authentic donor state from JSON...", flush=True)
    with open(donor_json, "r", encoding="utf-8") as f:
        donor_data = json.load(f)

    u_handoff = 0.0050
    donor_state = Mode1State()
    donor_state.u_rp = (0.0, float(donor_data.get("u_rp_mm", u_handoff)))

    d_nodal_raw = {int(k): float(v) for k, v in donor_data.get("d_nodal", {}).items()}
    h_gp_raw = {int(k): [float(x) for x in v] for k, v in donor_data.get("h_gp", {}).items()}

    for nid in mesh.nodes:
        donor_state.d_nodal[nid] = d_nodal_raw.get(nid, 0.0)

    for eid in mesh.elements_u1:
        if eid in h_gp_raw:
            donor_state.H_gp[eid] = h_gp_raw[eid]
        else:
            donor_state.H_gp[eid] = [0.0, 0.0, 0.0, 0.0]

    for nid, (x, y) in mesh.nodes.items():
        donor_state.u_nodal[nid] = (0.0, u_handoff * y)

    # 3. Assemble continuation deck
    out_inp = output_dir / "M1_MC_STAGE_C1_0_RECONSTRUCT.inp"
    print(f"\n[3/6] Assembling Stage C1-0 continuation deck: {out_inp.name}...", flush=True)

    engine = Mode1StateTransferEngine(mesh)
    engine.assemble_continuation_deck(
        mesh,
        donor_state,
        str(out_inp),
        u_handoff=u_handoff,
        u_final=0.0100,
        num_increments=5000,
        continuation_mode="equilibrate",
    )

    deck_size = os.path.getsize(out_inp)
    deck_sha = compute_sha256(out_inp)
    with open(out_inp, "r", encoding="utf-8") as f:
        line_count = sum(1 for _ in f)

    print(f"      Deck assembled: {out_inp.name} ({deck_size:,} bytes, {line_count:,} lines)", flush=True)
    print(f"      SHA-256: {deck_sha}", flush=True)

    # 4. Copy frozen UEL and verify invariant
    print("\n[4/6] Staging production UEL and notification assets...", flush=True)
    uel_dest = output_dir / "f42_mixed_uel.for"
    with open(frozen_uel, "rb") as f_src, open(uel_dest, "wb") as f_dst:
        f_dst.write(f_src.read())
    uel_sha = compute_sha256(uel_dest)
    expected_uel_sha = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert uel_sha == expected_uel_sha, f"UEL hash mismatch! Expected {expected_uel_sha}, got {uel_sha}"
    print(f"      Production UEL verified: {uel_dest.name} (SHA-256: {uel_sha})", flush=True)

    notif_src = REPO_ROOT / "scripts" / "hpc" / "notifications" / "job_notifications.sh"
    notif_dest = output_dir / "job_notifications.sh"
    if not notif_src.exists():
        notif_src = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "job_notifications.sh"
    with open(notif_src, "rb") as f_src, open(notif_dest, "wb") as f_dst:
        f_dst.write(f_src.read())
    notif_sha = compute_sha256(notif_dest)
    print(f"      Notification helper: {notif_dest.name} (SHA-256: {notif_sha})", flush=True)

    # 5. Generate PBS scripts
    print("\n[5/6] Generating PBS solver and datacheck execution scripts...", flush=True)
    pbs_solver = output_dir / "submit_M1_MC_STAGE_C1_0.pbs"
    pbs_solver_content = f"""#!/bin/bash
#PBS -N M1_MC_STAGE_C1_0
#PBS -q normal_imfdfkmq
#PBS -l nodes=1:ppn=1
#PBS -l mem=16gb
#PBS -l walltime=12:00:00
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -j oe
#PBS -o /scratch9/pr21vyci/runs/mode1_stage_c1_0_continuation/pbs_execution.log

set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_stage_c1_0_continuation"
cd "${{RUN_DIR}}"

# Storage compliance guard
if [[ "$(pwd -P)" =~ ^/home/ ]]; then
    echo "ERROR: Running under /home is strictly prohibited by HPC storage policy." >&2
    exit 2
fi

# Dual-channel notification trap installation
export JOB_NAME="M1_MC_STAGE_C1_0"
if [ -f "./job_notifications.sh" ]; then
    source ./job_notifications.sh
    notification_install_terminal_trap
    notify_start
fi

# Load Abaqus 2023 environment
module purge
module load abaqus/2023

# Execute solver in single-rank shared-memory mode
abaqus job=M1_MC_STAGE_C1_0_RECONSTRUCT input=M1_MC_STAGE_C1_0_RECONSTRUCT.inp user=f42_mixed_uel.for cpus=1 interactive
SOLVER_EXIT=$?

echo "Abaqus solver completed with exit code: ${{SOLVER_EXIT}}"
exit ${{SOLVER_EXIT}}
"""
    with open(pbs_solver, "w", encoding="utf-8") as f:
        f.write(pbs_solver_content)
    pbs_solver_sha = compute_sha256(pbs_solver)
    print(f"      Solver PBS: {pbs_solver.name} (SHA-256: {pbs_solver_sha})", flush=True)

    pbs_dc = output_dir / "submit_datacheck.pbs"
    pbs_dc_content = f"""#!/bin/bash
#PBS -N M1_MC_C1_0_DC
#PBS -q entry_imfdfkmq
#PBS -l nodes=1:ppn=1
#PBS -l mem=8gb
#PBS -l walltime=00:30:00
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -j oe
#PBS -o /scratch9/pr21vyci/runs/mode1_stage_c1_0_continuation/pbs_datacheck.log

set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_stage_c1_0_continuation"
cd "${{RUN_DIR}}"

# Storage compliance guard
if [[ "$(pwd -P)" =~ ^/home/ ]]; then
    echo "ERROR: Running under /home is strictly prohibited by HPC storage policy." >&2
    exit 2
fi

module purge
module load abaqus/2023

abaqus job=M1_MC_STAGE_C1_0_DC input=M1_MC_STAGE_C1_0_RECONSTRUCT.inp user=f42_mixed_uel.for datacheck interactive
DC_EXIT=$?

echo "Datacheck completed with exit code: ${{DC_EXIT}}"
exit ${{DC_EXIT}}
"""
    with open(pbs_dc, "w", encoding="utf-8") as f:
        f.write(pbs_dc_content)
    pbs_dc_sha = compute_sha256(pbs_dc)
    print(f"      Datacheck PBS: {pbs_dc.name} (SHA-256: {pbs_dc_sha})", flush=True)

    # 6. Generate Manifest and Anti-Deviation Card
    print("\n[6/6] Writing package manifest and anti-deviation card...", flush=True)
    manifest = {
        "package_name": "47_method_c_stage_c1_0_identical_mesh_continuation",
        "task_id": "F1482",
        "scientific_objective": "Stage C1-0: Mode-I Method C Identical-Mesh State Transfer & Continuation (Stage C1-0A State Reconstruction & Stage C1-0B Continuation)",
        "mesh_type": "canonical_2906_cpe4_cpe3_hybrid",
        "donor_source": {
            "job_name": "M1_PRE_1S",
            "job_id": "1411891.mmaster02",
            "u_handoff_mm": 0.0050,
            "rf_donor_n": 653.0885696411133,
            "e_tot_donor_mj": 1.6633838895357917,
            "donor_json": "models/pandey_kumar_mode1/41_method_c_genuine_continuation/evidence_forward_audit/coarse_donor_state_u0050.json",
        },
        "recipient_mesh": {
            "deck_path": "models/pandey_kumar_mode1/method_b_inf_companion_decks/M1_MB_INF_1S.inp",
            "elements_physical": mesh.num_elements,
            "nodes_total": mesh.num_nodes,
            "identical_mesh": True,
        },
        "files": {
            "input_deck": {
                "name": "M1_MC_STAGE_C1_0_RECONSTRUCT.inp",
                "sha256": deck_sha,
                "lines": line_count,
                "size_bytes": deck_size,
            },
            "user_subroutine": {
                "name": "f42_mixed_uel.for",
                "sha256": uel_sha,
                "production_invariant_verified": True,
            },
            "job_notifications": {
                "name": "job_notifications.sh",
                "sha256": notif_sha,
            },
            "solver_pbs": {
                "name": "submit_M1_MC_STAGE_C1_0.pbs",
                "sha256": pbs_solver_sha,
            },
            "datacheck_pbs": {
                "name": "submit_datacheck.pbs",
                "sha256": pbs_dc_sha,
            },
        },
        "execution_parameters": {
            "solver": "Abaqus/Standard 2023",
            "user_subroutine": "f42_mixed_uel.for",
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 12,
            "queue": "normal_imfdfkmq",
            "scratch_directory": "/scratch9/pr21vyci/runs/mode1_stage_c1_0_continuation",
        },
        "stage_c1_0_acceptance_criteria": {
            "criterion_1_rf_continuity": {
                "metric": "|RF_step1 - RF_donor|",
                "target_n": "<= 0.1 N",
                "donor_n": 653.0885696411133,
            },
            "criterion_2_energy_preservation": {
                "metric": "|E_int,step1 - E_int,donor| / E_int,donor",
                "target_pct": "<= 0.1%",
                "donor_mj": 1.6633838895357917,
            },
            "criterion_3_history_non_negativity": {
                "metric": "min(H)",
                "target": ">= 0.0",
            },
            "criterion_4_equilibrium_convergence": {
                "metric": "Step 1 Newton iterations",
                "target": "1 iteration (exact static equilibrium)",
            },
            "criterion_5_fracture_continuation": {
                "metric": "Step 2 completion to complete softening",
                "target": "Continuous monotonic crack propagation without divergence",
            },
        },
    }

    manifest_path = output_dir / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    manifest_sha = compute_sha256(manifest_path)
    print(f"      Manifest: {manifest_path.name} (SHA-256: {manifest_sha})", flush=True)

    card_path = output_dir / "PRE_JOB_ANTI_DEVIATION_CARD.md"
    card_content = f"""# Pre-Job Anti-Deviation Qualification Card: Package 47
## Stage C1-0: Mode-I Method C Identical-Mesh State Transfer & Continuation

- **Task ID:** F1482
- **Agent:** Gemini Antigravity
- **Date:** 2026-10-15
- **Input Deck:** `M1_MC_STAGE_C1_0_RECONSTRUCT.inp` (SHA-256: `{deck_sha}`)
- **User Subroutine:** `f42_mixed_uel.for` (SHA-256: `{uel_sha}`)
- **Discretization:** Canonical 2,906-element Mode-I mesh (identical-mesh control)
- **Handoff Point:** $u_{{handoff}} = 0.0050\\,\\text{{mm}}$ (from Job 1411891 / Package 40 Step 1)
- **Stage C1-0A (Equilibration):** Instantaneous static solve at $u = 0.0050\\,\\text{{mm}}$ ($\\Delta u = 0$)
- **Stage C1-0B (Continuation):** Fracture propagation solve from $u = 0.0050\\,\\text{{mm}}$ to $0.0100\\,\\text{{mm}}$
- **Expected Step 1 Reaction Force:** $653.0886\\,\\text{{N}}$ ($|\\Delta RF| < 0.1\\,\\text{{N}}$ target)
- **Expected Step 1 Internal Energy:** $1.66338\\,\\text{{mJ}}$ ($|\\Delta E_{{int}}| / E_{{int}} < 0.1\\%$ target)
- **Expected Step 1 Iterations:** 1 iteration (exact equilibrium)
- **HPC Configuration:** 1 CPU serial, 16 GB RAM, 12h walltime in `normal_imfdfkmq`
- **Execution Target:** `/scratch9/pr21vyci/runs/mode1_stage_c1_0_continuation/`
"""
    with open(card_path, "w", encoding="utf-8") as f:
        f.write(card_content)
    card_sha = compute_sha256(card_path)
    print(f"      Anti-Deviation Card: {card_path.name} (SHA-256: {card_sha})", flush=True)

    print("\nPackage 47 generation COMPLETE and verified!", flush=True)
    return manifest


if __name__ == "__main__":
    generate_package_47()
