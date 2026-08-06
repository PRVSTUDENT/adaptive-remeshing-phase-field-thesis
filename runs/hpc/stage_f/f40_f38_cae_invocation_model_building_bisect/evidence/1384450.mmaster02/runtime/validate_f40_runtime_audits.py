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

    delta_path = os.path.join(target_dir, "F38_F39_INVOCATION_DELTA_AUDIT.json")
    if not os.path.exists(delta_path):
        errors.append("F38_F39_INVOCATION_DELTA_AUDIT.json missing")

    expected_phases = [
        "P00_KERNEL_STARTUP",
        "P01_IMPORTS",
        "P02_MODULE_LOADING",
        "P03_SOURCE_DECK_DISCOVERY",
        "P04_MODEL_FROM_INPUT_FILE",
        "P05_IMPORTED_MODEL_INVENTORY",
        "P06_GEOMETRY_CONVERSION",
        "P07_INDEPENDENT_MODEL_OWNERSHIP",
        "P08_ASSEMBLY_OPERATIONS",
        "P09_TOPOLOGY_MEASUREMENT",
        "P10_SETS_SURFACES_INVENTORY",
        "P11_STEP_OUTPUT_PROBING"
    ]

    for pname in expected_phases:
        pfpath = os.path.join(target_dir, "{}_AUDIT.json".format(pname))
        if not os.path.exists(pfpath):
            errors.append("{}_AUDIT.json missing".format(pname))
        else:
            try:
                with open(pfpath, "r") as f:
                    data = json.load(f)
                    if data.get("phase_name") != pname:
                        errors.append("{}_AUDIT.json invalid phase_name".format(pname))
                    metrics = data.get("metrics")
                    if metrics is None:
                        errors.append("{}_AUDIT.json missing metrics dictionary".format(pname))
            except Exception as exc:
                errors.append("Error reading {}_AUDIT.json: {}".format(pname, exc))

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
