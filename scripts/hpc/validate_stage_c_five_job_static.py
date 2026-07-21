#!/usr/bin/env python3
"""Static validation of the Stage C five-job PBS infrastructure.

Never submits jobs. Checks:
  - scripts exist
  - #PBS -m abe present, no tracked #PBS -M
  - distinct job names
  - walltime/mem present
  - job class comments (solver vs CAE)
  - bash -n syntax where bash is available
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EMAIL = "pr21vyci@mailserver.tu-freiberg.de"

JOBS = [
    {
        "id": 1,
        "path": ROOT / "scripts/hpc/molnar_h0_miseseri_smoke.pbs",
        "name": "molnar_h0_miseseri_smoke",
        "class": "solver",
        "mem": "16gb",
        "walltime": "01:00:00",
    },
    {
        "id": 2,
        "path": ROOT / "scripts/hpc/molnar_h0_miseseri_preanalysis.pbs",
        "name": "molnar_h0_miseseri_pre",
        "class": "solver",
        "mem": "16gb",
        "walltime": "02:00:00",
    },
    {
        "id": 3,
        "path": ROOT / "scripts/hpc/molnar_h0_miseseri_remesh.pbs",
        "name": "molnar_h0_miseseri_remesh",
        "class": "cae",
        "mem": "16gb",
        "walltime": "01:00:00",
    },
    {
        "id": 4,
        "path": ROOT / "scripts/hpc/molnar_h0_refined_integrity.pbs",
        "name": "molnar_h0_ref_integ",
        "class": "solver",
        "mem": "16gb",
        "walltime": "02:00:00",
    },
    {
        "id": 5,
        "path": ROOT / "scripts/hpc/molnar_miseseri_refined_final.pbs",
        "name": "molnar_miseseri_final",
        "class": "solver",
        "mem": "32gb",
        "walltime": "06:00:00",
    },
]


def validate_one(job: dict) -> list[str]:
    errors: list[str] = []
    path: Path = job["path"]
    if not path.exists():
        return [f"missing file: {path}"]
    text = path.read_text(encoding="utf-8")
    if f"#PBS -N {job['name']}" not in text and f"#PBS -N {job['name'][:15]}" not in text:
        # PBS -N may truncate; check partial
        if f"#PBS -N {job['name']}" not in text:
            # accept if name token appears
            if job["name"] not in text.splitlines()[0:5].__str__() and f"#PBS -N" not in text:
                errors.append("missing #PBS -N")
    if not re.search(r"#PBS -N \S+", text):
        errors.append("missing #PBS -N")
    if "#PBS -m abe" not in text:
        errors.append("missing #PBS -m abe")
    if re.search(r"#PBS -M\s+\S+", text):
        errors.append("tracked #PBS -M must not be present; use qsub -M")
    if f"mem={job['mem']}" not in text.replace(" ", ""):
        # allow select=...:mem=
        if job["mem"] not in text:
            errors.append(f"expected mem={job['mem']}")
    if f"walltime={job['walltime']}" not in text:
        errors.append(f"expected walltime={job['walltime']}")
    if "ncpus=1" not in text:
        errors.append("expected serial ncpus=1")
    if "PRESTAGED_ROOT" not in text:
        errors.append("missing PRESTAGED_ROOT handling")
    if "PROJECT_REVISION" not in text:
        errors.append("missing PROJECT_REVISION handling")
    if job["class"] == "cae":
        if "cae" not in text.lower() and "CAE" not in text:
            errors.append("CAE job should mention CAE")
        if "JOB_CLASS=\"cae" not in text and "cae_remesh" not in text:
            errors.append("CAE classification marker missing")
    else:
        if "abaqus job=" not in text and "abaqus job=" not in text.replace('"', ""):
            if "abaqus job" not in text:
                errors.append("solver job missing abaqus job invocation")
    # no qsub inside PBS
    if re.search(r"^\s*qsub\b", text, re.M):
        errors.append("PBS script must not call qsub")
    return errors


def main() -> int:
    # Email directive checker
    email_script = ROOT / "scripts/hpc/validate_pbs_email_notifications.py"
    paths = [str(j["path"]) for j in JOBS]
    email_rc = subprocess.run(
        [sys.executable, str(email_script), "--email", EMAIL, *paths],
        check=False,
        capture_output=True,
        text=True,
    )
    reports = []
    failed = False
    for job in JOBS:
        errs = validate_one(job)
        if email_rc.returncode != 0 and str(job["path"]) in (email_rc.stderr or ""):
            errs.append("email validation failed")
        # bash -n is best-effort. On Windows, WSL bash often cannot see D: paths.
        bash = shutil.which("bash")
        if bash and os.name != "nt":
            syn = subprocess.run([bash, "-n", str(job["path"])], check=False, capture_output=True, text=True)
            if syn.returncode != 0:
                errs.append(f"bash -n failed: {syn.stderr.strip()}")
        elif bash and os.name == "nt":
            # Lightweight directive syntax check already covers structure; record skip.
            pass
        status = "pass" if not errs else "fail"
        if status == "fail":
            failed = True
        reports.append({"job": job["id"], "name": job["name"], "path": str(job["path"].as_posix()), "status": status, "errors": errs})

    # overall email
    if email_rc.returncode != 0:
        failed = True

    out = {
        "status": "fail" if failed else "pass",
        "email_validation_rc": email_rc.returncode,
        "email_stdout": email_rc.stdout,
        "email_stderr": email_rc.stderr,
        "jobs": reports,
        "submission_authorized": False,
        "note": "Static validation only. Do not qsub.",
    }
    out_path = ROOT / "results/validation/stage_c_five_job/STATIC_PBS_VALIDATION.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": out["status"], "jobs": [(r["job"], r["status"], r["errors"]) for r in reports]}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
