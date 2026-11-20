# -*- coding: utf-8 -*-
"""
build_demo_cycle2_job4_manifest.py
==================================
Builds the qualified authorization manifest for Job 4:
models/pandey_kumar_mode1/289_method_c_demo_case/METHOD_C_DEMO_JOB4_AUTHORIZATION.json
"""

import os
import json
import hashlib

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case")

def get_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().lower()

inp_path = os.path.join(CASE_DIR, "PK_METHOD_C_CYCLE2_REFINED_JOB4.inp")
phys_path = os.path.join(CASE_DIR, "PK_METHOD_C_CYCLE2_PHYS.inp")
uel_path = os.path.join(CASE_DIR, "f42_mixed_uel.for")
pbs_path = os.path.join(CASE_DIR, "submit_demo_cycle2_job4.pbs")
notif_path = os.path.join(CASE_DIR, "job_notifications.sh")

inp_sha = get_sha256(inp_path)
phys_sha = get_sha256(phys_path)
uel_sha = get_sha256(uel_path)
pbs_sha = get_sha256(pbs_path)
notif_sha = get_sha256(notif_path)

cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_289_method_c_demo_job4_r1/submit_demo_cycle2_job4.pbs"'
cmd_sha = hashlib.sha256(cmd.encode("utf-8")).hexdigest().lower()

manifest = {
    "task_id": "METHOD-C-CYCLE2-JOB4-SOLVE",
    "batch_name": "MODE1_METHOD_C_DEMO_JOB4",
    "max_new_pbs_submissions": 1,
    "submissions_authorized": 1,
    "submissions_consumed": 0,
    "cumulative_pbs_submissions": 61,
    "max_submissions": 1,
    "hours_valid": 72,
    "automatic_retry": False,
    "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "resource_limits": {
        "ncpus": 16,
        "mem_gb": 48,
        "walltime_hours": 72,
        "queue": "entry_imfdfkmq",
        "execution_mode": "16-cpu shared-memory SMP"
    },
    "files": {
        "PK_METHOD_C_CYCLE2_REFINED_JOB4.inp": inp_sha,
        "PK_METHOD_C_CYCLE2_PHYS.inp": phys_sha,
        "f42_mixed_uel.for": uel_sha,
        "submit_demo_cycle2_job4.pbs": pbs_sha,
        "job_notifications.sh": notif_sha
    },
    "jobs": [
        {
            "id": "demo_cycle2_job4",
            "pbs": "submit_demo_cycle2_job4.pbs",
            "command": cmd,
            "command_sha256": cmd_sha,
            "max_submissions": 1,
            "depends_on": [],
            "purpose": "Method C Cycle 2 Job-4 re-equilibration at u2=0.008756 mm and forward crack propagation to u2=0.012000 mm on adapted receiver mesh (42,012 layered elements, frozen UEL CE8D5EDC)",
            "cpus": 16,
            "memory_gb": 48,
            "walltime_hours": 72,
            "queue": "entry_imfdfkmq",
            "execution": "16-cpu shared-memory SMP",
            "input": "PK_METHOD_C_CYCLE2_REFINED_JOB4.inp",
            "datacheck": "PK_METHOD_C_CYCLE2_REFINED_JOB4_DC.dat"
        }
    ],
    "candidate_jobs": [
        {
            "id": "demo_cycle2_job4",
            "input": "PK_METHOD_C_CYCLE2_REFINED_JOB4.inp",
            "purpose": "Method C Cycle 2 Job-4 re-equilibration at u2=0.008756 mm and forward crack propagation to u2=0.012000 mm on adapted receiver mesh (42,012 layered elements, frozen UEL CE8D5EDC)",
            "cpus": 16,
            "memory_gb": 48,
            "walltime_hours": 72,
            "queue": "entry_imfdfkmq",
            "execution": "16-cpu shared-memory SMP",
            "submission_authorized": True
        }
    ],
    "adapter": "mode1-qualified-batch-v2",
    "scientific_scope": "MODE1",
    "technical_stage": "C1-2",
    "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_289_method_c_demo_job4_r1",
    "acceptance": {
        "demo_cycle2_job4": "Method C Cycle 2 Job-4 re-equilibration at u2=0.008756 mm and forward crack propagation to u2=0.012000 mm completes with Exit 0; force and energy continuity in Step 1 (<5% delta vs Job-3); forward crack propagation across remaining ligament in Step 2; peak damage preserved (zero healing) and thermodynamic non-negativity maintained."
    }
}

out_path = os.path.join(CASE_DIR, "METHOD_C_DEMO_JOB4_AUTHORIZATION.json")
with open(out_path, "w") as f:
    json.dump(manifest, f, indent=2)

print("Generated manifest at: %s" % out_path)
print("Command SHA: %s" % cmd_sha)
