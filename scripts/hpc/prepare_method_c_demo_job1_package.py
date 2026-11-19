# -*- coding: utf-8 -*-
"""
scripts/hpc/prepare_method_c_demo_job1_package.py
=================================================
Prepares the Job-1 baseline submission package for the Method C demonstration case:
- Computes SHA-256 for all package files
- Generates PACKAGE_MANIFEST.json
- Generates METHOD_C_DEMO_JOB1_AUTHORIZATION.json
- Preserves max_new_pbs_submissions = 0 (dry-run preparation only, no execution)
"""

from __future__ import print_function
import os
import sys
import json
import hashlib

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
PKG_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case")

def prepare_package():
    files = [
        "PK_METHOD_C_DEMO_COARSE_JOB1.inp",
        "PK_METHOD_C_DEMO_COARSE_PHYS.inp",
        "f42_mixed_uel.for",
        "submit_demo_coarse_job1.pbs",
        "job_notifications.sh"
    ]

    hashes = {}
    for fn in files:
        fp = os.path.join(PKG_DIR, fn)
        if not os.path.isfile(fp):
            raise IOError("Missing package file: %s" % fp)
        h = hashlib.sha256()
        with open(fp, "rb") as f:
            for chunk in iter(lambda: f.read(1048576), b""):
                h.update(chunk)
        hashes[fn] = h.hexdigest().lower()
        print("%-35s: %s" % (fn, hashes[fn]))

    manifest = {
        "package_name": "METHOD_C_DEMO_COARSE_JOB1_BASELINE",
        "files": hashes,
        "cpus": 16,
        "memory_gb": 48,
        "walltime_hours": 72,
        "queue": "normal_imfdfkmq"
    }

    manifest_path = os.path.join(PKG_DIR, "PACKAGE_MANIFEST.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    cmd_str = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q normal_imfdfkmq /scratch9/pr21vyci/runs/mode1_289_method_c_demo_case/submit_demo_coarse_job1.pbs"'
    cmd_sha = hashlib.sha256(cmd_str.encode("utf-8")).hexdigest().lower()

    auth = {
        "batch_name": "MODE1_METHOD_C_DEMO_JOB1",
        "max_submissions": 1,
        "hours_valid": 72,
        "automatic_retry": False,
        "files": hashes,
        "jobs": [
            {
                "id": "demo_coarse_job1",
                "pbs": "submit_demo_coarse_job1.pbs",
                "command": cmd_str,
                "command_sha256": cmd_sha,
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Method C Demo Case Step-1 baseline solve on coarse mesh (8,760 layered elements, u2=0.0050 mm, *RESTART WRITE)",
                "cpus": 16,
                "memory_gb": 48,
                "walltime_hours": 72,
                "queue": "normal_imfdfkmq",
                "execution": "16-cpu shared-memory SMP",
                "input": "PK_METHOD_C_DEMO_COARSE_JOB1.inp",
                "datacheck": "PK_METHOD_C_DEMO_COARSE_JOB1_DC.dat"
            }
        ]
    }

    auth_path = os.path.join(PKG_DIR, "METHOD_C_DEMO_JOB1_AUTHORIZATION.json")
    with open(auth_path, "w") as f:
        json.dump(auth, f, indent=2)

    print("Successfully generated package manifest and authorization deck:")
    print("  Manifest: %s" % manifest_path)
    print("  Auth:     %s" % auth_path)
    return manifest, auth

if __name__ == "__main__":
    prepare_package()
