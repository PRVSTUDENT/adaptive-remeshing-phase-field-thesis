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
    "geometry_conversion",
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

    # 1. Parse and validate CAE_INVOCATION_CONTEXT_AUDIT.json using the exact entrypoint output schema
    inv_path = os.path.join(target_dir, "CAE_INVOCATION_CONTEXT_AUDIT.json")
    if not os.path.exists(inv_path):
        errors.append("CAE_INVOCATION_CONTEXT_AUDIT.json missing")
    else:
        try:
            with open(inv_path, "r") as f:
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
    matrix_path = os.path.join(target_dir, "CAE_PHASE_DIAGNOSTIC_MATRIX.json")
    if not os.path.exists(matrix_path):
        errors.append("CAE_PHASE_DIAGNOSTIC_MATRIX.json missing")
    else:
        try:
            with open(matrix_path, "r") as f:
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
                        errors.append("Phase '{}' attempted is not True".format(exp_phase))
                    if p_rec.get("passed") is not True:
                        errors.append("Phase '{}' passed is not True".format(exp_phase))
                    if p_rec.get("dependency_blocked") is not False:
                        errors.append("Phase '{}' dependency_blocked is not False".format(exp_phase))

                    if p_rec.get("exception_type") is not None:
                        errors.append("Phase '{}' reported exception_type: {}".format(exp_phase, p_rec.get("exception_type")))
                    if p_rec.get("exception_message") is not None:
                        errors.append("Phase '{}' reported exception_message: {}".format(exp_phase, p_rec.get("exception_message")))
                    if p_rec.get("traceback") is not None:
                        errors.append("Phase '{}' reported non-null traceback".format(exp_phase))

        except Exception as exc:
            errors.append("Error reading CAE_PHASE_DIAGNOSTIC_MATRIX.json: {}".format(exc))

    if errors:
        print("F38_MATRIX_VALIDATION_FAILED:")
        for err in errors:
            print("  - " + err)
        return 1

    print("F38_MATRIX_VALIDATION_PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
