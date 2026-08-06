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

    delta_path = os.path.join(target_dir, "F38_F39_INVOCATION_DELTA_AUDIT.json")
    if not os.path.exists(delta_path):
        errors.append("F38_F39_INVOCATION_DELTA_AUDIT.json missing")

    # 0. Parse and validate SCHEDULER_PROVENANCE.json
    prov_path = os.path.join(target_dir, "SCHEDULER_PROVENANCE.json")
    if not os.path.exists(prov_path):
        errors.append("SCHEDULER_PROVENANCE.json missing")
    else:
        try:
            with open(prov_path, "r") as f:
                prov = json.load(f)
                if prov.get("protocol_version") != 1:
                    errors.append("SCHEDULER_PROVENANCE.json protocol_version is not 1")
                if not prov.get("pbs_jobid"):
                    errors.append("SCHEDULER_PROVENANCE.json pbs_jobid is missing or empty")
                if prov.get("pbs_environment") != "PBS_BATCH":
                    errors.append("SCHEDULER_PROVENANCE.json pbs_environment is not PBS_BATCH")
                if not prov.get("hostname"):
                    errors.append("SCHEDULER_PROVENANCE.json hostname is missing or empty")
                nhosts = prov.get("nodefile_hosts", [])
                if not isinstance(nhosts, list) or len(nhosts) == 0:
                    errors.append("SCHEDULER_PROVENANCE.json nodefile_hosts is empty or missing")
                elif prov.get("hostname") not in nhosts and prov.get("hostname_short") not in nhosts:
                    errors.append("SCHEDULER_PROVENANCE.json hostname not in nodefile_hosts")
                abq_exe = prov.get("abaqus_executable", "")
                if not abq_exe or not os.path.isabs(abq_exe):
                    errors.append("SCHEDULER_PROVENANCE.json abaqus_executable is not an absolute path: {}".format(abq_exe))
                abq_rel = prov.get("abaqus_release", "")
                if "2023" not in abq_rel:
                    errors.append("SCHEDULER_PROVENANCE.json abaqus_release does not contain 2023: {}".format(abq_rel))
                if not prov.get("timestamp_utc"):
                    errors.append("SCHEDULER_PROVENANCE.json timestamp_utc is missing")
        except Exception as exc:
            errors.append("Error reading SCHEDULER_PROVENANCE.json: {}".format(exc))

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
                geom_rec = phase_map.get("geometry_conversion_observation", {})
                obs_res = geom_rec.get("observations", geom_rec.get("result", {}))
                cc_probes = obs_res.get("controlled_conversion_probes", {})
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
                            errors.append("F38 Phase '{}' attempted is not True".format(exp_phase))
                        if p_rec.get("passed") is not True:
                            errors.append("F38 Phase '{}' passed is not True".format(exp_phase))
                        if p_rec.get("dependency_blocked") is not False:
                            errors.append("F38 Phase '{}' dependency_blocked is not False".format(exp_phase))
                    else:
                        if confirmed_root_cause:
                            if exp_phase == "usable_geometry_validation":
                                if p_rec.get("attempted") is not True:
                                    errors.append("F38 Phase 'usable_geometry_validation' attempted is not True")
                            else:
                                if p_rec.get("passed") is not True and p_rec.get("dependency_blocked") is not True:
                                    errors.append("F38 Phase '{}' must be passed or dependency_blocked when root cause confirmed".format(exp_phase))
                        else:
                            if p_rec.get("attempted") is not True:
                                errors.append("F38 Phase '{}' attempted is not True".format(exp_phase))
                            if p_rec.get("passed") is not True:
                                errors.append("F38 Phase '{}' passed is not True".format(exp_phase))
                            if p_rec.get("dependency_blocked") is not False:
                                errors.append("F38 Phase '{}' dependency_blocked is not False".format(exp_phase))

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

    # Validate NOTIFICATION_AUDIT.json if present
    notif_audit_path = os.path.join(target_dir, "NOTIFICATION_AUDIT.json")
    if os.path.exists(notif_audit_path):
        try:
            with open(notif_audit_path, "r") as f:
                notif_recs = json.load(f)
                if not isinstance(notif_recs, list):
                    errors.append("NOTIFICATION_AUDIT.json must be a JSON array of records")
                else:
                    for nrec in notif_recs:
                        if not nrec.get("event_type") or not nrec.get("channel"):
                            errors.append("NOTIFICATION_AUDIT.json record missing event_type or channel")
                        recip = nrec.get("recipient_redacted", "")
                        if "bot" in recip.lower() or "token" in recip.lower() or len(recip) > 35:
                            errors.append("NOTIFICATION_AUDIT.json recipient field contains unredacted secret key or token")
        except Exception as exc:
            errors.append("Error reading NOTIFICATION_AUDIT.json: {}".format(exc))

    required_rc_files = [
        "bisection_runner.returncode",
        "delta_auditor.returncode",
        "f38_entrypoint.returncode",
        "f38_matrix_validator.returncode"
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

    if errors:
        print("RUNTIME_AUDIT_VALIDATION_FAILED:")
        for err in errors:
            print("  - " + err)
        return 1

    print("RUNTIME_AUDIT_VALIDATION_PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
