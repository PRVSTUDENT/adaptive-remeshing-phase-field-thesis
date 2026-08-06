#!/usr/bin/env python3
import json
import os
import sys

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    errors = []

    status_path = os.path.join(target_dir, "STATUS.json")
    if not os.path.exists(status_path):
        errors.append("STATUS.json missing")

    launcher_audit_path = os.path.join(target_dir, "ABAQUS_LAUNCHER_ENVIRONMENT_AUDIT.json")
    if not os.path.exists(launcher_audit_path):
        errors.append("ABAQUS_LAUNCHER_ENVIRONMENT_AUDIT.json missing")

    py_rc_path = os.path.join(target_dir, "python_probe.returncode")
    if os.path.exists(py_rc_path):
        with open(py_rc_path, "r") as f:
            if f.read().strip() != "0":
                errors.append("python_probe.returncode is non-zero")

    cae_rc_path = os.path.join(target_dir, "cae_kernel.returncode")
    cae_rc = None
    if os.path.exists(cae_rc_path):
        with open(cae_rc_path, "r") as f:
            try:
                cae_rc = int(f.read().strip())
            except ValueError:
                cae_rc = -1

    if cae_rc == 0:
        kernel_audit_path = os.path.join(target_dir, "CAE_KERNEL_STARTUP_AUDIT.json")
        if not os.path.exists(kernel_audit_path):
            errors.append("cae_kernel succeeded but CAE_KERNEL_STARTUP_AUDIT.json is missing")
        else:
            try:
                with open(kernel_audit_path, "r") as f:
                    data = json.load(f)
                    if data.get("marker") != "CAE_KERNEL_STARTED":
                        errors.append("CAE_KERNEL_STARTUP_AUDIT.json missing marker CAE_KERNEL_STARTED")
            except Exception as exc:
                errors.append("Error reading CAE_KERNEL_STARTUP_AUDIT.json: {}".format(exc))
    elif cae_rc is not None and cae_rc != 0:
        failure_audit_path = os.path.join(target_dir, "RUNTIME_FAILURE_AUDIT.json")
        if not os.path.exists(failure_audit_path):
            errors.append("cae_kernel failed but RUNTIME_FAILURE_AUDIT.json is missing")

    report_path = os.path.join(target_dir, "MISSING_EVIDENCE_REPORT.json")
    if os.path.exists(report_path):
        try:
            with open(report_path, "r") as f:
                rep = json.load(f)
                missing = set(rep.get("missing_files", []))
                existing = set(rep.get("existing_files", []))
                overlap = missing.intersection(existing)
                if overlap:
                    errors.append("MISSING_EVIDENCE_REPORT.json has overlapping files: {}".format(overlap))
                if rep.get("missing_count") != len(missing):
                    errors.append("missing_count mismatch in MISSING_EVIDENCE_REPORT.json")
        except Exception as exc:
            errors.append("Error reading MISSING_EVIDENCE_REPORT.json: {}".format(exc))
    else:
        errors.append("MISSING_EVIDENCE_REPORT.json missing")

    if errors:
        print("RUNTIME_AUDIT_VALIDATION_FAILED:")
        for err in errors:
            print("  - " + err)
        return 1

    print("RUNTIME_AUDIT_VALIDATION_PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
