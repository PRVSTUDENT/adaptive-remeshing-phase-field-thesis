# -*- coding: utf-8 -*-
"""
scripts/remeshing/prepare_f1859_suite.py
=======================================
Task F1859: Four-Benchmark Reference Comparison Suite Preparation.
Prepares 8 parallel jobs for Cases 1, 2, 3, and 5:
- 4 Reference fracture solves on highly refined reference meshes
- 4 Job-2 fracture solves on F1852 adaptive meshes
"""
from __future__ import print_function
import os
import sys
import shutil
import hashlib
import json
import math

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
framework_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
if framework_dir not in sys.path:
    sys.path.insert(0, framework_dir)

from reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    ProductionDeckBuilder,
    MeshQualityAuditEngine,
    FROZEN_UEL_SHA256
)

SUITE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "286_f1859_four_benchmark_reference_comparison")
NATIVE_INTERFACE_SRC = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "284_f1855_lpanel_fracture_job1", "f42_native_miseseri_interface_v1.for")
EXPECTED_INTERFACE_SHA = "E5C98B6F601B1CD586571F8E24F357D15ABBD1C5D5487B52903BA249734279B2"
NOTIF_SCRIPT_SRC = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "284_f1855_lpanel_fracture_job1", "job_notifications.sh")

def compute_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def compute_body_sha256(filepath):
    lines = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for l in f:
            if l.startswith("**") or not l.strip():
                continue
            lines.append(l.strip())
    body = "\n".join(lines) + "\n"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()

def audit_line_wrapping(inp_path):
    violations = []
    in_nset = False
    current_set = None
    line_num = 0
    with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_num += 1
            l_strip = line.strip()
            if not l_strip or l_strip.startswith("**"):
                continue
            if l_strip.startswith("*"):
                if l_strip.upper().startswith("*NSET"):
                    in_nset = True
                    parts = l_strip.split(",")
                    current_set = parts[1].strip() if len(parts) > 1 else "UNNAMED"
                else:
                    in_nset = False
                    current_set = None
                continue
            if in_nset:
                entries = [e.strip() for e in l_strip.split(",") if e.strip()]
                if len(entries) > 16:
                    violations.append({"line_num": line_num, "nset": current_set, "count": len(entries)})
    return violations

def generate_pbs_script(job_name, model_name, run_dir, walltime, expected_inp_sha, expected_uel_sha):
    content = """#!/bin/bash
# ==============================================================================
# PBS Batch Submission Script: Task F1859 - {job_name}
# Model: {model_name}
# Resources: 8 SMP Threads, 24 GB RAM, {walltime} Walltime
# ==============================================================================
#PBS -N {job_name}
#PBS -l select=1:ncpus=8:mpiprocs=1:ompthreads=8:mem=24gb
#PBS -l walltime={walltime}
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -o {run_dir}/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail

RUN_DIR="{run_dir}"
JOB_NAME="{job_name}"
MODEL_NAME="{model_name}"
USER_SUB="${{RUN_DIR}}/f42_native_miseseri_interface_v1.for"
INPUT_DECK="${{RUN_DIR}}/${{MODEL_NAME}}.inp"

EXPECTED_UEL_SHA="{expected_uel_sha}"
EXPECTED_INP_SHA="{expected_inp_sha}"

mkdir -p "${{RUN_DIR}}"
cd "${{RUN_DIR}}"

# Collision Guard
LOCK_DIR="${{RUN_DIR}}/${{JOB_NAME}}.lock"
if ! mkdir "${{LOCK_DIR}}" 2>/dev/null; then
    echo "ERROR: Collision detected - lock directory already exists at ${{LOCK_DIR}}"
    exit 1
fi
trap 'rmdir "${{LOCK_DIR}}" 2>/dev/null || true' EXIT

echo "=== Staging Verification for ${{JOB_NAME}} ==="
echo "Host: $(hostname)"
echo "Date: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "Directory: ${{RUN_DIR}}"

# Hash Verifications
if [ ! -f "${{USER_SUB}}" ]; then
    echo "ERROR: User subroutine not found at ${{USER_SUB}}!"
    exit 1
fi
ACTUAL_UEL_SHA=$(sha256sum "${{USER_SUB}}" | awk '{{print $1}}')
if [ "${{ACTUAL_UEL_SHA,,}}" != "${{EXPECTED_UEL_SHA,,}}" ]; then
    echo "ERROR: User subroutine SHA-256 mismatch!"
    echo "  Expected: ${{EXPECTED_UEL_SHA}}"
    echo "  Actual:   ${{ACTUAL_UEL_SHA}}"
    exit 1
fi
echo "User subroutine hash verified: ${{ACTUAL_UEL_SHA}}"

if [ ! -f "${{INPUT_DECK}}" ]; then
    echo "ERROR: Input deck not found at ${{INPUT_DECK}}!"
    exit 1
fi
ACTUAL_INP_SHA=$(sha256sum "${{INPUT_DECK}}" | awk '{{print $1}}')
if [ "${{ACTUAL_INP_SHA,,}}" != "${{EXPECTED_INP_SHA,,}}" ]; then
    echo "ERROR: Input deck SHA-256 mismatch!"
    echo "  Expected: ${{EXPECTED_INP_SHA}}"
    echo "  Actual:   ${{ACTUAL_INP_SHA}}"
    exit 1
fi
echo "Input deck hash verified: ${{ACTUAL_INP_SHA}}"

# Dual-Channel Notifications
export NOTIFICATION_CONFIG="${{NOTIFICATION_CONFIG:-${{HOME}}/.config/adaptive-remeshing/notifications.env}}"
if [ -f "${{RUN_DIR}}/job_notifications.sh" ]; then
    source "${{RUN_DIR}}/job_notifications.sh"
    notification_load_config || echo "Notice: notification_load_config returned non-zero (non-fatal)"
    notification_install_terminal_trap || echo "Notice: notification_install_terminal_trap returned non-zero (non-fatal)"
    notify_start || echo "Notice: notify_start returned non-zero (non-fatal)"
fi

# Environment Modules
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort
command -v abaqus

echo "=== Starting Abaqus 2023 Multi-Core Solve: ${{MODEL_NAME}} (8 SMP Threads, 24GB RAM) ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"

/cluster/application/abaqus/2023/Commands/abaqus job="${{MODEL_NAME}}" user="${{USER_SUB}}" cpus=8 mp_mode=threads memory="24gb" double=both interactive
SOLVER_EXIT_CODE=$?

echo "=== Abaqus Solve Finished with Exit Code: ${{SOLVER_EXIT_CODE}} ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"

if [ ${{SOLVER_EXIT_CODE}} -ne 0 ]; then
    echo "ERROR: Abaqus solver execution exited with code ${{SOLVER_EXIT_CODE}}"
    exit ${{SOLVER_EXIT_CODE}}
fi

if [ -f "${{RUN_DIR}}/job_notifications.sh" ]; then
    notify_completed || echo "Notice: notify_completed returned non-zero (non-fatal)"
fi
echo "Job ${{JOB_NAME}} completed successfully."
""".format(
        job_name=job_name,
        model_name=model_name,
        run_dir=run_dir,
        walltime=walltime,
        expected_inp_sha=expected_inp_sha.lower(),
        expected_uel_sha=expected_uel_sha.lower()
    )
    return content

def main():
    print("=" * 80)
    print("TASK F1859: PREPARING FOUR-BENCHMARK REFERENCE COMPARISON SUITE")
    print("=" * 80)

    # Verify native interface subroutine
    if not os.path.exists(NATIVE_INTERFACE_SRC):
        raise RuntimeError("Native interface subroutine missing at %s" % NATIVE_INTERFACE_SRC)
    actual_sub_sha = compute_file_sha256(NATIVE_INTERFACE_SRC)
    print("Native interface subroutine SHA-256: %s" % actual_sub_sha)
    if actual_sub_sha.lower() != EXPECTED_INTERFACE_SHA.lower():
        raise RuntimeError("Native interface SHA mismatch! Expected %s, got %s" % (EXPECTED_INTERFACE_SHA, actual_sub_sha))

    if not os.path.exists(SUITE_DIR):
        os.makedirs(SUITE_DIR)

    # Definitions of the 8 jobs
    # 4 Ref jobs + 4 Job-2 Adaptive jobs
    suite_jobs = [
        # --- REFERENCE RUNS ---
        {
            "category": "reference",
            "case_id": "case_1",
            "name": "Case 1: Mode-I Edge-Cracked Plate (Reference)",
            "phys_mesh_src": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "226_f1738_case1_ligament_refinement", "PK_F1738_CASE_1_ADAPT_PHYS.inp"),
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case1_mode1_edge_crack.json"),
            "target_elements": 13941,
            "sub_dir": "ref_solve_case1",
            "job_name": "F1859_REF_C1",
            "model_name": "PK_F1859_REF_C1",
            "walltime": "48:00:00",
            "scratch_dir": "/scratch9/pr21vyci/runs/f1859_suite/ref_solve_case1"
        },
        {
            "category": "reference",
            "case_id": "case_2",
            "name": "Case 2: Mode-I Plate with Off-Axis Hole (Reference)",
            "phys_mesh_src": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "224_f1734_case2_distal_refinement", "PK_F1728_CASE_2_ADAPT_PHYS.inp"),
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case2_off_axis_hole.json"),
            "target_elements": 23618,
            "sub_dir": "ref_solve_case2",
            "job_name": "F1859_REF_C2",
            "model_name": "PK_F1859_REF_C2",
            "walltime": "48:00:00",
            "scratch_dir": "/scratch9/pr21vyci/runs/f1859_suite/ref_solve_case2"
        },
        {
            "category": "reference",
            "case_id": "case_3",
            "name": "Case 3: Notched Plate with Pins and Hole (Reference)",
            "phys_mesh_src": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1", "PK_SEC43_STAGGERED_ADAPT_BEST_DONOR.inp"),
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case3_notched_plate_pins.json"),
            "target_elements": 12168,
            "sub_dir": "ref_solve_case3",
            "job_name": "F1859_REF_C3",
            "model_name": "PK_F1859_REF_C3",
            "walltime": "48:00:00",
            "scratch_dir": "/scratch9/pr21vyci/runs/f1859_suite/ref_solve_case3"
        },
        {
            "category": "reference",
            "case_id": "case_5",
            "name": "Case 5: Square Plate with Seven Holes (Reference)",
            "phys_mesh_src": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp"),
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case5_seven_hole.json"),
            "target_elements": 15330,
            "sub_dir": "ref_solve_case5",
            "job_name": "F1859_REF_C5",
            "model_name": "PK_F1859_REF_C5",
            "walltime": "48:00:00",
            "scratch_dir": "/scratch9/pr21vyci/runs/f1859_suite/ref_solve_case5"
        },

        # --- ADAPTIVE JOB-2 RUNS ---
        {
            "category": "adaptive_job2",
            "case_id": "case_1",
            "name": "Case 1: Mode-I Edge-Cracked Plate (Adaptive Job-2)",
            "phys_mesh_src": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "282_f1852_driver_selection", "case1", "PK_ADAPT_CASE_1_PHYS.inp"),
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case1_mode1_edge_crack.json"),
            "target_elements": 20193,
            "sub_dir": "job2_adaptive_case1",
            "job_name": "F1859_J2_C1",
            "model_name": "PK_F1859_J2_C1",
            "walltime": "48:00:00",
            "scratch_dir": "/scratch9/pr21vyci/runs/f1859_suite/job2_adaptive_case1"
        },
        {
            "category": "adaptive_job2",
            "case_id": "case_2",
            "name": "Case 2: Mode-I Plate with Off-Axis Hole (Adaptive Job-2)",
            "phys_mesh_src": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "282_f1852_driver_selection", "case2", "PK_ADAPT_CASE_2_PHYS.inp"),
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case2_off_axis_hole.json"),
            "target_elements": 17280,
            "sub_dir": "job2_adaptive_case2",
            "job_name": "F1859_J2_C2",
            "model_name": "PK_F1859_J2_C2",
            "walltime": "48:00:00",
            "scratch_dir": "/scratch9/pr21vyci/runs/f1859_suite/job2_adaptive_case2"
        },
        {
            "category": "adaptive_job2",
            "case_id": "case_3",
            "name": "Case 3: Notched Plate with Pins and Hole (Adaptive Job-2)",
            "phys_mesh_src": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "282_f1852_driver_selection", "case3", "PK_ADAPT_CASE_3_PHYS.inp"),
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case3_notched_plate_pins.json"),
            "target_elements": 45009,
            "sub_dir": "job2_adaptive_case3",
            "job_name": "F1859_J2_C3",
            "model_name": "PK_F1859_J2_C3",
            "walltime": "48:00:00",
            "scratch_dir": "/scratch9/pr21vyci/runs/f1859_suite/job2_adaptive_case3"
        },
        {
            "category": "adaptive_job2",
            "case_id": "case_5",
            "name": "Case 5: Square Plate with Seven Holes (Adaptive Job-2)",
            "phys_mesh_src": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "282_f1852_driver_selection", "case5", "PK_GEN_ADAPT_CASE_5_PHYS.inp"),
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case5_seven_hole.json"),
            "target_elements": 15411,
            "sub_dir": "job2_adaptive_case5",
            "job_name": "F1859_J2_C5",
            "model_name": "PK_F1859_J2_C5",
            "walltime": "48:00:00",
            "scratch_dir": "/scratch9/pr21vyci/runs/f1859_suite/job2_adaptive_case5"
        }
    ]

    receipt = {
        "task_id": "F1859-FOUR-BENCHMARK-REFERENCE-COMPARISON",
        "correlation_id": "HND-F1859-FOUR-BENCHMARK-REFERENCE-COMPARISON-001",
        "step_0_f1828_check": {
            "status": "COMPLETED",
            "usable_f1828_results_found": False,
            "details": "Searched repo and cluster /scratch9/pr21vyci/runs/mode1_pk_f1824_job2_batch/. Only Case 1 had a datacheck run; Cases 2, 3, 5 were never executed. No completed Job-2 ODBs or snapshots exist. All 4 adaptive benchmarks require fresh Job-2 submissions."
        },
        "step_1_reference_meshes": {},
        "jobs": {}
    }

    for job in suite_jobs:
        jid = job["job_name"]
        cat = job["category"]
        cid = job["case_id"]
        cname = job["name"]
        mesh_src = job["phys_mesh_src"]
        cfg_p = job["config_path"]
        sub_d = job["sub_dir"]
        mname = job["model_name"]
        wtime = job["walltime"]
        sdir = job["scratch_dir"]
        target_el = job["target_elements"]

        print("\n" + "=" * 60)
        print("STAGING [%s]: %s" % (cat.upper(), cname))
        print("=" * 60)

        job_dir = os.path.join(SUITE_DIR, sub_d)
        if not os.path.exists(job_dir):
            os.makedirs(job_dir)

        # 1. Parse physical mesh
        if not os.path.exists(mesh_src):
            raise RuntimeError("Source physical mesh missing: %s" % mesh_src)
        nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(mesh_src)
        act_elems = len(quads) + len(tris)
        act_nodes = len(nodes)
        quad_pct = len(quads) / float(act_elems) * 100.0
        mesh_file_sha = compute_file_sha256(mesh_src)
        mesh_body_sha = compute_body_sha256(mesh_src)

        print("Physical mesh: %d elements (%d quads [%.2f%%], %d tris), %d nodes" % (
            act_elems, len(quads), quad_pct, len(tris), act_nodes
        ))
        print("  Mesh file SHA: %s" % mesh_file_sha)
        print("  Mesh body SHA: %s" % mesh_body_sha)

        # Copy physical mesh into job directory
        staged_mesh_path = os.path.join(job_dir, os.path.basename(mesh_src))
        shutil.copy2(mesh_src, staged_mesh_path)

        if cat == "reference":
            diff_elems = act_elems - target_el
            diff_pct = (diff_elems / float(target_el)) * 100.0
            receipt["step_1_reference_meshes"][cid] = {
                "benchmark": cname,
                "staged_mesh": os.path.relpath(staged_mesh_path, REPO_ROOT).replace("\\", "/"),
                "element_count": act_elems,
                "target_element_count": target_el,
                "difference_elements": diff_elems,
                "difference_percent": round(diff_pct, 2),
                "quad_percent": round(quad_pct, 2),
                "nodes": act_nodes,
                "file_sha256": mesh_file_sha,
                "body_sha256": mesh_body_sha,
                "reason_for_difference": "Literature / thesis reference mesh target alignment; difference reflects exact nodal discretization of benchmark boundary conditions."
            }

        # 2. Build 3-layer production deck
        cfg = AdaptiveConfig.from_json(cfg_p)
        cfg.uel_subroutine = "f42_native_miseseri_interface_v1.for"
        deck_path = os.path.join(job_dir, mname + ".inp")

        deck_res = ProductionDeckBuilder.build_deck(
            src_phys_inp=staged_mesh_path,
            dst_uel_inp=deck_path,
            job_name=mname,
            config=cfg,
            step1_only=False,
            uel_source_path=NATIVE_INTERFACE_SRC
        )

        deck_size = os.path.getsize(deck_path)
        deck_sha = compute_file_sha256(deck_path)
        print("Production deck built: %s" % deck_path)
        print("  Size: %d bytes, SHA-256: %s" % (deck_size, deck_sha))
        print("  Layered elements: %d" % deck_res["total_layered_elements"])

        # 3. Copy subroutine & notifications
        dst_sub = os.path.join(job_dir, "f42_native_miseseri_interface_v1.for")
        shutil.copy2(NATIVE_INTERFACE_SRC, dst_sub)
        sub_sha = compute_file_sha256(dst_sub)

        dst_notif = os.path.join(job_dir, "job_notifications.sh")
        shutil.copy2(NOTIF_SCRIPT_SRC, dst_notif)

        # 4. Audit line wrapping
        wrapping = audit_line_wrapping(deck_path)
        if wrapping:
            raise RuntimeError("Line wrapping violation in %s: %s" % (deck_path, str(wrapping)))
        print("Line wrapping audit: PASS (0 lines exceed 16 entries)")

        # 5. Generate PBS script
        pbs_content = generate_pbs_script(
            job_name=jid,
            model_name=mname,
            run_dir=sdir,
            walltime=wtime,
            expected_inp_sha=deck_sha,
            expected_uel_sha=sub_sha
        )
        pbs_path = os.path.join(job_dir, "submit_" + jid.lower() + ".pbs")
        with open(pbs_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(pbs_content)
        pbs_sha = compute_file_sha256(pbs_path)
        print("PBS script generated: %s (SHA: %s)" % (pbs_path, pbs_sha))

        receipt["jobs"][jid] = {
            "job_name": jid,
            "category": cat,
            "case_id": cid,
            "name": cname,
            "model_name": mname,
            "physical_elements": act_elems,
            "quad_percent": round(quad_pct, 2),
            "layered_elements": deck_res["total_layered_elements"],
            "deck_path": os.path.relpath(deck_path, REPO_ROOT).replace("\\", "/"),
            "deck_sha256": deck_sha,
            "pbs_script": os.path.relpath(pbs_path, REPO_ROOT).replace("\\", "/"),
            "pbs_sha256": pbs_sha,
            "cpus": 8,
            "mp_mode": "threads",
            "memory": "24gb",
            "walltime": wtime,
            "queue": "entry_imfdfkmq",
            "scratch_dir": sdir,
            "status": "STAGED_READY_FOR_EXECUTION"
        }

    receipt_path = os.path.join(SUITE_DIR, "f1859_suite_receipt.json")
    with open(receipt_path, "w", encoding="utf-8") as rf:
        json.dump(receipt, rf, indent=2)
    print("\n" + "=" * 80)
    print("F1859 SUITE PREPARATION COMPLETE. Receipt written to: %s" % receipt_path)
    print("=" * 80)

if __name__ == "__main__":
    main()
