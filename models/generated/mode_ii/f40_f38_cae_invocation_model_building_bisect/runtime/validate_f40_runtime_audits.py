#!/usr/bin/env python3
import json
import os
import sys

EXPECTED_F38_PHASES = [
    "bootstrap",
    "abaqus_module_import",
    "source_deck_access",
    "model_import",
    "repository_inventory",
    "repository_resolution",
    "geometry_conversion_observation",
    "usable_geometry_validation",
    "element_type_assignment",
    "mesh_control_assignment",
    "mesh_generation",
    "assembly_feature_inventory",
    "instance_replacement",
    "crack_edge_method_inventory",
    "crack_edge_detection",
    "crack_mesh_topology",
    "assembly_set_inventory",
    "output_variable_probe",
    "output_request_rebinding",
    "input_write",
    "generated_input_presence"
]

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    errors = []

    status_path = os.path.join(target_dir, "STATUS.json")
    if not os.path.exists(status_path):
        errors.append("STATUS.json missing")

    delta_path = os.path.join(target_dir, "F38_F39_INVOCATION_DELTA_AUDIT.json")
    if not os.path.exists(delta_path):
        errors.append("F38_F39_INVOCATION_DELTA_AUDIT.json missing")

    # 1. Parse and validate CAE_INVOCATION_CONTEXT_AUDIT.json using the exact entrypoint output schema
    inv_audit_path = os.path.join(target_dir, "CAE_INVOCATION_CONTEXT_AUDIT.json")
    if not os.path.exists(inv_audit_path):
        errors.append("CAE_INVOCATION_CONTEXT_AUDIT.json missing")
    else:
        try:
            with open(inv_audit_path, "r") as f:
                inv_data = json.load(f)
                if inv_data.get("entrypoint") != "run_f38_cae_diagnostic.py":
                    errors.append("CAE_INVOCATION_CONTEXT_AUDIT.json entrypoint is not run_f38_cae_diagnostic.py (found: {})".format(inv_data.get("entrypoint")))
                if inv_data.get("runtime_dir_exists") is not True:
                    errors.append("CAE_INVOCATION_CONTEXT_AUDIT.json runtime_dir_exists is not True")
                if inv_data.get("runtime_dir_on_sys_path") is not True:
                    errors.append("CAE_INVOCATION_CONTEXT_AUDIT.json runtime_dir_on_sys_path is not True")
                if inv_data.get("bootstrap_passed") is not True:
                    errors.append("CAE_INVOCATION_CONTEXT_AUDIT.json bootstrap_passed is not True")
        except Exception as exc:
            errors.append("Error reading CAE_INVOCATION_CONTEXT_AUDIT.json: {}".format(exc))

    # 2. Parse and validate CAE_PHASE_DIAGNOSTIC_MATRIX.json
    matrix_audit_path = os.path.join(target_dir, "CAE_PHASE_DIAGNOSTIC_MATRIX.json")
    if not os.path.exists(matrix_audit_path):
        errors.append("CAE_PHASE_DIAGNOSTIC_MATRIX.json missing")
    else:
        try:
            with open(matrix_audit_path, "r") as f:
                mat_data = json.load(f)

                if mat_data.get("overall_passed") is not True:
                    errors.append("CAE_PHASE_DIAGNOSTIC_MATRIX.json overall_passed is not True")

                phases = mat_data.get("phases", [])
                if len(phases) != len(EXPECTED_F38_PHASES):
                    errors.append(
                        "CAE_PHASE_DIAGNOSTIC_MATRIX.json expected {} phases, found {}".format(
                            len(EXPECTED_F38_PHASES), len(phases)
                        )
                    )

                phase_map = {p.get("phase"): p for p in phases if isinstance(p, dict)}
                for exp_phase in EXPECTED_F38_PHASES:
                    p_rec = phase_map.get(exp_phase)
                    if p_rec is None:
                        errors.append("CAE_PHASE_DIAGNOSTIC_MATRIX.json missing phase record for '{}'".format(exp_phase))
                        continue

                    if p_rec.get("attempted") is not True:
                        errors.append("F38 Phase '{}' attempted is not True".format(exp_phase))
                    if p_rec.get("passed") is not True:
                        errors.append("F38 Phase '{}' passed is not True".format(exp_phase))
                    if p_rec.get("dependency_blocked") is not False:
                        errors.append("F38 Phase '{}' dependency_blocked is not False".format(exp_phase))
                    if p_rec.get("exception_type") is not None:
                        errors.append("F38 Phase '{}' reported exception_type: {}".format(exp_phase, p_rec.get("exception_type")))

        except Exception as exc:
            errors.append("Error reading CAE_PHASE_DIAGNOSTIC_MATRIX.json: {}".format(exc))

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
                    if data.get("return_code") != 0:
                        errors.append("{}_AUDIT.json return_code is non-zero ({})".format(pname, data.get("return_code")))
                    metrics = data.get("metrics")
                    if metrics is None:
                        errors.append("{}_AUDIT.json missing metrics dictionary".format(pname))
                    elif pname == "P02_MODULE_LOADING":
                        for key in ["entrypoint_exists", "helper_exists", "entrypoint_hash_matched", "helper_hash_matched", "module_imported", "main_callable"]:
                            if metrics.get(key) is not True:
                                errors.append("P02_MODULE_LOADING_AUDIT.json metrics {} is not True (found: {})".format(key, metrics.get(key)))
                        if metrics.get("main_executed_in_p02") is not False:
                            errors.append("P02_MODULE_LOADING_AUDIT.json metrics main_executed_in_p02 is not False")
            except Exception as exc:
                errors.append("Error reading {}_AUDIT.json: {}".format(pname, exc))

    required_rc_files = [
        "bisection_runner.returncode",
        "delta_auditor.returncode",
        "f38_entrypoint.returncode",
        "f38_matrix_validator.returncode",
        "collector.returncode"
    ]

    for rc_file in required_rc_files:
        rc_path = os.path.join(target_dir, rc_file)
        if not os.path.exists(rc_path):
            errors.append("{} missing".format(rc_file))
        else:
            try:
                with open(rc_path, "r") as f:
                    val = f.read().strip()
                    if val != "0":
                        errors.append("{} contains non-zero returncode: {}".format(rc_file, val))
            except Exception as exc:
                errors.append("Error reading {}: {}".format(rc_file, exc))

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
                if rep.get("missing_count") != 0:
                    errors.append("MISSING_EVIDENCE_REPORT.json missing_count is non-zero ({})".format(rep.get("missing_count")))
                if rep.get("status") != "complete":
                    errors.append("MISSING_EVIDENCE_REPORT.json status is not complete (found: {})".format(rep.get("status")))
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
