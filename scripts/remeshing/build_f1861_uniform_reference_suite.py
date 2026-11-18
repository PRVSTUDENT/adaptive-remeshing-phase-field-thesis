# -*- coding: utf-8 -*-
"""
scripts/remeshing/build_f1861_uniform_reference_suite.py
=======================================================
Task F1861: Build 4 uniform highly refined reference meshes (Cases 1, 2, 3, 5),
convert to authoritative 3-layer Method A Abaqus input decks, and stage for PBS submission.
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

from abaqus import mdb, session
from abaqusConstants import *

from reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    StraightNotchMode1Adapter,
    OffAxisHoleMode1Adapter,
    NotchedPlateWithPinHolesAdapter,
    SevenHolePlateAdapter,
    AbaqusNativeRemeshingEngine,
    MeshQualityAuditEngine,
    ProductionDeckBuilder
)

SUITE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "288_f1861_uniform_reference")
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
    with open(filepath, "r") as f:
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
    with open(inp_path, "r") as f:
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

def generate_pbs_script(job_name, model_name, run_dir, walltime, cpus, mem, expected_inp_sha, expected_uel_sha):
    content = """#!/bin/bash
# ==============================================================================
# PBS Batch Submission Script: Task F1861 - {job_name}
# Model: {model_name}
# Resources: {cpus} SMP Threads, {mem} RAM, {walltime} Walltime
# ==============================================================================
#PBS -N {job_name}
#PBS -l select=1:ncpus={cpus}:mpiprocs=1:ompthreads={cpus}:mem={mem}
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

echo "=== Starting Abaqus 2023 Multi-Core Solve: ${{MODEL_NAME}} ({cpus} SMP Threads, {mem} RAM) ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"

/cluster/application/abaqus/2023/Commands/abaqus job="${{MODEL_NAME}}" user="${{USER_SUB}}" cpus={cpus} mp_mode=threads memory="{mem}" double=both interactive
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
        cpus=cpus,
        mem=mem,
        expected_inp_sha=expected_inp_sha.lower(),
        expected_uel_sha=expected_uel_sha.lower()
    )
    return content

def main():
    print("=" * 80)
    print("TASK F1861: BUILDING TRUE UNIFORM HIGHLY REFINED REFERENCE SUITE")
    print("=" * 80)

    # 1. Verify user subroutine
    if not os.path.exists(NATIVE_INTERFACE_SRC):
        raise RuntimeError("Native interface subroutine missing at %s" % NATIVE_INTERFACE_SRC)
    sub_sha = compute_file_sha256(NATIVE_INTERFACE_SRC)
    print("Native interface subroutine SHA-256: %s" % sub_sha)
    if sub_sha.lower() != EXPECTED_INTERFACE_SHA.lower():
        raise RuntimeError("Subroutine hash mismatch!")

    if not os.path.exists(SUITE_DIR):
        os.makedirs(SUITE_DIR)

    case_definitions = [
        {
            "case_id": "case_1",
            "name": "Case 1: Mode-I Edge-Cracked Plate (Uniform Reference)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case1_mode1_edge_crack.json"),
            "adapter_cls": StraightNotchMode1Adapter,
            "seed_size": 0.00375,  # h = l0 / 2 = 0.0075 / 2 = 0.00375 mm
            "job_name": "F1861_REF_C1",
            "model_name": "PK_F1861_REF_C1",
            "sub_dir": "case1",
            "target_description": "Uniform h <= l0/2 = 0.00375 mm everywhere"
        },
        {
            "case_id": "case_2",
            "name": "Case 2: Mode-I Plate with Off-Axis Hole (Uniform Reference)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case2_off_axis_hole.json"),
            "adapter_cls": OffAxisHoleMode1Adapter,
            "seed_size": 0.00375,  # h = l0 / 2 = 0.0075 / 2 = 0.00375 mm
            "job_name": "F1861_REF_C2",
            "model_name": "PK_F1861_REF_C2",
            "sub_dir": "case2",
            "target_description": "Uniform h <= l0/2 = 0.00375 mm everywhere"
        },
        {
            "case_id": "case_3",
            "name": "Case 3: Notched Plate with Pins and Hole (Uniform Reference)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case3_notched_plate_pins.json"),
            "adapter_cls": NotchedPlateWithPinHolesAdapter,
            "seed_size": 0.358,  # Yields ~85,800 elements, matching paper Standard (~86,000 el)
            "job_name": "F1861_REF_C3",
            "model_name": "PK_F1861_REF_C3",
            "sub_dir": "case3",
            "target_description": "Paper Standard ~86,000 elements"
        },
        {
            "case_id": "case_5",
            "name": "Case 5: Square Plate with Seven Holes (Uniform Reference)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case5_seven_hole.json"),
            "adapter_cls": SevenHolePlateAdapter,
            "seed_size": 0.00363,  # Yields ~81,090 elements, matching paper Standard (81,090 el, h <= 0.004 mm)
            "job_name": "F1861_REF_C5",
            "model_name": "PK_F1861_REF_C5",
            "sub_dir": "case5",
            "target_description": "Paper Standard 81,090 elements (h <= 0.004 mm)"
        }
    ]

    receipt = {
        "task_id": "F1861-UNIFORM-HIGHLY-REFINED-REFERENCE",
        "correlation_id": "HND-F1861-UNIFORM-REFERENCE-001",
        "operation": "coupled_fracture_validation",
        "max_new_pbs": 4,
        "pbs_accounting": {
            "authorized_new_submissions": 4,
            "predecessor_cumulative": 53,
            "current_cumulative": 57,
            "queue": "entry_imfdfkmq",
            "cpus_per_job": 16,
            "threads_per_job": 16,
            "memory_per_job": "48gb",
            "walltime_per_job": "72:00:00"
        },
        "meshes": {},
        "jobs": {}
    }

    for item in case_definitions:
        cid = item["case_id"]
        cname = item["name"]
        cfg_p = item["config_path"]
        ad_cls = item["adapter_cls"]
        seed_size = item["seed_size"]
        jid = item["job_name"]
        mname = item["model_name"]
        sub_d = item["sub_dir"]
        target_desc = item["target_description"]

        print("\n" + "=" * 60)
        print("BUILDING UNIFORM MESH: %s" % cname)
        print("  Seed size: %.5f mm (%s)" % (seed_size, target_desc))
        print("=" * 60)

        case_dir = os.path.join(SUITE_DIR, sub_d)
        if not os.path.exists(case_dir):
            os.makedirs(case_dir)

        # 1. Build Abaqus CAE geometry and mesh uniformly
        cfg = AdaptiveConfig.from_json(cfg_p)
        model_name = "Model_F1861_" + cid
        if model_name in mdb.models:
            del mdb.models[model_name]
        m = mdb.Model(name=model_name)
        adapter = ad_cls(cfg)

        p, a, inst = AbaqusNativeRemeshingEngine.build_cae_geometry(
            m=m, adapter=adapter, config=cfg, seed_size=seed_size
        )

        # Export physical mesh .inp
        phys_inp_path = os.path.join(case_dir, "PK_F1861_REF_%s_PHYS.inp" % cid.upper())
        job_cae_name = "JOB_EXPORT_PHYS_" + cid
        if job_cae_name in mdb.jobs:
            del mdb.jobs[job_cae_name]
        j_export = mdb.Job(name=job_cae_name, model=model_name, type=ANALYSIS)
        j_export.writeInput(consistencyChecking=OFF)

        # Move/copy exported .inp from root/scratch to phys_inp_path
        exported_inp = job_cae_name + ".inp"
        if not os.path.exists(exported_inp):
            # Check in current dir or repo root
            if os.path.exists(os.path.join(REPO_ROOT, exported_inp)):
                exported_inp = os.path.join(REPO_ROOT, exported_inp)
            else:
                raise RuntimeError("Exported physical inp not found: %s" % exported_inp)
        
        # Clean the physical mesh into standalone format
        nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(exported_inp)
        act_elems = len(quads) + len(tris)
        act_nodes = len(nodes)
        quad_pct = len(quads) / float(act_elems) * 100.0 if act_elems > 0 else 0.0

        with open(phys_inp_path, "w") as f:
            f.write("** F1861 Uniform Reference Physical Mesh - %s\n" % cname)
            f.write("** Target: %s, Seed: %.5f mm\n" % (target_desc, seed_size))
            f.write("*HEADING\n")
            f.write(" %s Physical Mesh\n" % cname)
            f.write("*NODE\n")
            for nid in sorted(nodes.keys()):
                x, y = nodes[nid]
                f.write("%d, %.9e, %.9e\n" % (nid, x, y))
            if quads:
                f.write("*ELEMENT, TYPE=CPE4, ELSET=ALL_ELEM\n")
                for eid in sorted(quads.keys()):
                    conn = quads[eid]
                    f.write("%d, %d, %d, %d, %d\n" % (eid, conn[0], conn[1], conn[2], conn[3]))
            if tris:
                f.write("*ELEMENT, TYPE=CPE3, ELSET=ALL_ELEM\n")
                for eid in sorted(tris.keys()):
                    conn = tris[eid]
                    f.write("%d, %d, %d, %d\n" % (eid, conn[0], conn[1], conn[2]))

        # Remove temporary CAE job export file
        if os.path.exists(exported_inp):
            try:
                os.remove(exported_inp)
            except Exception:
                pass

        phys_file_sha = compute_file_sha256(phys_inp_path)
        phys_body_sha = compute_body_sha256(phys_inp_path)
        print("Physical mesh written: %s" % phys_inp_path)
        print("  Elements: %d (%d quads [%.2f%%], %d tris), Nodes: %d" % (
            act_elems, len(quads), quad_pct, len(tris), act_nodes
        ))
        print("  File SHA: %s" % phys_file_sha)
        print("  Body SHA: %s" % phys_body_sha)

        # 2. Build 3-Layer Method A Production Deck
        cfg.uel_subroutine = "f42_native_miseseri_interface_v1.for"
        deck_path = os.path.join(case_dir, mname + ".inp")

        deck_res = ProductionDeckBuilder.build_deck(
            src_phys_inp=phys_inp_path,
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

        # 3. Copy user subroutine and notifications
        dst_sub = os.path.join(case_dir, "f42_native_miseseri_interface_v1.for")
        shutil.copy2(NATIVE_INTERFACE_SRC, dst_sub)

        dst_notif = os.path.join(case_dir, "job_notifications.sh")
        shutil.copy2(NOTIF_SCRIPT_SRC, dst_notif)

        # 4. Audit line wrapping (<= 16 entries per line)
        wrapping = audit_line_wrapping(deck_path)
        if wrapping:
            raise RuntimeError("Line wrapping violation in %s: %s" % (deck_path, str(wrapping)))
        print("Line wrapping audit: PASS (0 lines exceed 16 entries)")

        # 5. Generate PBS submission script (16 CPUs, 48GB, 72:00:00)
        sdir = "/scratch9/pr21vyci/runs/f1861_uniform_reference/" + sub_d
        pbs_content = generate_pbs_script(
            job_name=jid,
            model_name=mname,
            run_dir=sdir,
            walltime="72:00:00",
            cpus=16,
            mem="48gb",
            expected_inp_sha=deck_sha,
            expected_uel_sha=sub_sha
        )
        pbs_path = os.path.join(case_dir, "submit_" + jid.lower() + ".pbs")
        with open(pbs_path, "w") as f:
            f.write(pbs_content.replace("\r\n", "\n"))
        pbs_sha = compute_file_sha256(pbs_path)
        print("PBS script generated: %s (SHA: %s)" % (pbs_path, pbs_sha))

        receipt["meshes"][cid] = {
            "case_id": cid,
            "name": cname,
            "target_description": target_desc,
            "seed_size_mm": seed_size,
            "physical_mesh_path": os.path.relpath(phys_inp_path, REPO_ROOT).replace("\\", "/"),
            "element_count": act_elems,
            "quad_percent": round(quad_pct, 2),
            "nodes": act_nodes,
            "file_sha256": phys_file_sha,
            "body_sha256": phys_body_sha
        }

        receipt["jobs"][jid] = {
            "job_name": jid,
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
            "cpus": 16,
            "mp_mode": "threads",
            "memory": "48gb",
            "walltime": "72:00:00",
            "queue": "entry_imfdfkmq",
            "scratch_dir": sdir,
            "status": "STAGED_READY_FOR_EXECUTION"
        }

    receipt_path = os.path.join(SUITE_DIR, "f1861_suite_receipt.json")
    with open(receipt_path, "w") as rf:
        json.dump(receipt, rf, indent=2)
    print("\n" + "=" * 80)
    print("F1861 UNIFORM REFERENCE SUITE BUILT SUCCESSFULLY.")
    print("Receipt written to: %s" % receipt_path)
    print("=" * 80)

if __name__ == "__main__":
    main()
