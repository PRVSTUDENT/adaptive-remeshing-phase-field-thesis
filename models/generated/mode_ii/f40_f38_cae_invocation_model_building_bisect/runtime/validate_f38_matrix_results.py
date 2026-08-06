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

def validate_probe_record(name, rec, errors):
    if not isinstance(rec, dict):
        errors.append("Probe '{}' record missing or not a dict".format(name))
        return
    if rec.get("attempted") is not True:
        errors.append("Probe '{}' attempted is not True".format(name))
    comp = rec.get("completed")
    exc_t = rec.get("exception_type")
    exc_m = rec.get("exception_message")
    if comp is True:
        if exc_t is not None or exc_m is not None:
            errors.append("Probe '{}' completed is True but reported non-null exception".format(name))
    elif comp is False:
        if exc_t is None or exc_m is None:
            errors.append("Probe '{}' completed is False but missing exception type or message".format(name))
    else:
        errors.append("Probe '{}' completed must be boolean True or False".format(name))

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

                phases = mat_data.get("phases", [])
                if len(phases) != len(EXPECTED_F38_PHASES):
                    errors.append(
                        "CAE_PHASE_DIAGNOSTIC_MATRIX.json expected {} phases, found {}".format(
                            len(EXPECTED_F38_PHASES), len(phases)
                        )
                    )

                phase_map = {p.get("phase"): p for p in phases if isinstance(p, dict)}

                # Inspect geometry_conversion_observation for probe evidence
                geom_rec = phase_map.get("geometry_conversion_observation", {})
                obs_res = geom_rec.get("observations", geom_rec.get("result", {}))
                cc_probes = obs_res.get("controlled_conversion_probes", {})

                if not cc_probes:
                    errors.append("Phase 'geometry_conversion_observation' missing controlled_conversion_probes in observations")
                else:
                    ctrl_a = cc_probes.get("control_a", {})
                    ctrl_b = cc_probes.get("control_b", {})
                    ang_probes = cc_probes.get("angle_probes", {})

                    validate_probe_record("control_a", ctrl_a, errors)
                    validate_probe_record("control_b", ctrl_b, errors)

                    if ctrl_a.get("completed") is True:
                        if ctrl_a.get("coincident_pairs_before") != 15:
                            errors.append("control_a coincident_pairs_before expected 15, actual {}".format(ctrl_a.get("coincident_pairs_before")))
                        if ctrl_a.get("node_reduction") != 15:
                            errors.append("control_a node_reduction expected 15, actual {}".format(ctrl_a.get("node_reduction")))
                        if ctrl_a.get("coincident_pairs_after") != 0:
                            errors.append("control_a coincident_pairs_after expected 0, actual {}".format(ctrl_a.get("coincident_pairs_after")))

                    for fa in [15, 30, 45, 60, 90]:
                        fa_k = "angle_{}deg".format(fa)
                        validate_probe_record(fa_k, ang_probes.get(fa_k, {}), errors)

                confirmed_root_cause = cc_probes.get("coincident_crack_nodes_confirmed_root_cause") is True

                if not mat_data.get("overall_passed") and not confirmed_root_cause:
                    errors.append("CAE_PHASE_DIAGNOSTIC_MATRIX.json overall_passed is not True and root cause is not confirmed")

                for exp_phase in EXPECTED_F38_PHASES:
                    p_rec = phase_map.get(exp_phase)
                    if p_rec is None:
                        errors.append("CAE_PHASE_DIAGNOSTIC_MATRIX.json missing phase record for '{}'".format(exp_phase))
                        continue

                    if exp_phase in ["bootstrap", "abaqus_module_import", "source_deck_access", "model_import", "repository_inventory", "repository_resolution", "geometry_conversion_observation"]:
                        if p_rec.get("attempted") is not True:
                            errors.append("Phase '{}' attempted is not True".format(exp_phase))
                        if p_rec.get("passed") is not True:
                            errors.append("Phase '{}' passed is not True".format(exp_phase))
                        if p_rec.get("dependency_blocked") is not False:
                            errors.append("Phase '{}' dependency_blocked is not False".format(exp_phase))
                    else:
                        if confirmed_root_cause:
                            if exp_phase == "usable_geometry_validation":
                                if p_rec.get("attempted") is not True:
                                    errors.append("Phase 'usable_geometry_validation' attempted is not True")
                            else:
                                if p_rec.get("passed") is not True and p_rec.get("dependency_blocked") is not True:
                                    errors.append("Phase '{}' must be passed or dependency_blocked when root cause confirmed".format(exp_phase))
                        else:
                            if p_rec.get("attempted") is not True:
                                errors.append("Phase '{}' attempted is not True".format(exp_phase))
                            if p_rec.get("passed") is not True:
                                errors.append("Phase '{}' passed is not True".format(exp_phase))
                            if p_rec.get("dependency_blocked") is not False:
                                errors.append("Phase '{}' dependency_blocked is not False".format(exp_phase))

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
