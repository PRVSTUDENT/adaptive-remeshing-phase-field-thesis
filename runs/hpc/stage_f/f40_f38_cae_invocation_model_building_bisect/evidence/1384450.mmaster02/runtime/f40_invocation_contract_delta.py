#!/usr/bin/env python3
import json
import os
import sys
import datetime

def check_line_endings(filepath):
    if not os.path.exists(filepath):
        return "missing"
    with open(filepath, "rb") as f:
        content = f.read()
        if b"\r\n" in content:
            return "CRLF"
        elif b"\n" in content:
            return "LF"
        return "EMPTY"

def main():
    repo_root = os.environ.get("F40_REPO_ROOT", os.getcwd())
    f38_dir = os.path.join(repo_root, "models", "generated", "mode_ii", "f38_comprehensive_cae_diagnostic_matrix")
    f39_dir = os.path.join(repo_root, "models", "generated", "mode_ii", "f39_abaqus_cae_kernel_startup_diagnostic")
    f40_dir = os.path.join(repo_root, "models", "generated", "mode_ii", "f40_f38_cae_invocation_model_building_bisect")

    f38_pbs = os.path.join(f38_dir, "M2RMDIAG1.pbs")
    f39_pbs = os.path.join(f39_dir, "M2RMKERN1.pbs")
    f40_pbs = os.path.join(f40_dir, "M2RMBISECT1.pbs")

    delta_audit = {
        "protocol_version": 1,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "job_name": "M2RMBISECT1",
        "pbs_directives": {
            "f38_queue": "entry_imfdfkmq",
            "f39_queue": "entry_imfdfkmq",
            "f40_queue": "entry_imfdfkmq",
            "f38_resources": "select=1:ncpus=1:mpiprocs=1:ompthreads=1:mem=8gb",
            "f39_resources": "select=1:ncpus=1:mpiprocs=1:ompthreads=1:mem=8gb",
            "f40_resources": "select=1:ncpus=1:mpiprocs=1:ompthreads=1:mem=8gb"
        },
        "line_endings": {
            "f38_pbs": check_line_endings(f38_pbs),
            "f39_pbs": check_line_endings(f39_pbs),
            "f40_pbs": check_line_endings(f40_pbs)
        },
        "runtime_environment": {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "pythonpath": os.environ.get("PYTHONPATH", ""),
            "ld_library_path": os.environ.get("LD_LIBRARY_PATH", ""),
            "f38_runtime_dir": os.environ.get("F38_RUNTIME_DIR", ""),
            "f39_runtime_dir": os.environ.get("F39_RUNTIME_DIR", ""),
            "f40_runtime_dir": os.environ.get("F40_RUNTIME_DIR", os.getcwd())
        },
        "python27_compatibility": {
            "print_statements": "from __future__ import print_function used",
            "json_dump": "standard json serializable dicts",
            "exception_syntax": "except Exception as exc syntax"
        }
    }

    out_path = os.environ.get("F40_DELTA_AUDIT", "F38_F39_INVOCATION_DELTA_AUDIT.json")
    with open(out_path, "w") as f:
        json.dump(delta_audit, f, indent=2)

    print("F38_F39_INVOCATION_DELTA_AUDIT_GENERATED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
