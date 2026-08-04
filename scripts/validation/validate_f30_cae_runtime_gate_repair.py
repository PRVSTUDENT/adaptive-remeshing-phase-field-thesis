# Python 2 and 3 compatible offline validator for F30
from __future__ import print_function
import sys
import os
import json

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return json.load(f)

def main():
    runs_dir = 'runs/hpc/stage_f/f30_cae_runtime_gate_repair'
    pkg_dir = 'models/generated/mode_ii/f30_cae_runtime_gate_repair'
    orch_script = 'scripts/hpc/stage_f/submit_stage_f30_cae_build_qualification.sh'

    failures = []

    # 1. Check required run artifacts
    f29_inv = load_json(os.path.join(runs_dir, 'F29_INVALIDATION_AUDIT.json'))
    topo_api = load_json(os.path.join(runs_dir, 'ABAQUS_TOPOLOGY_API_AUDIT.json'))
    mesh_conn = load_json(os.path.join(runs_dir, 'MESH_CONNECTIVITY_AUDIT_CONTRACT.json'))
    src_entity = load_json(os.path.join(runs_dir, 'SOURCE_ENTITY_SPEC.json'))
    src_out = load_json(os.path.join(runs_dir, 'SOURCE_OUTPUT_CONTRACT.json'))
    rebind_contract = load_json(os.path.join(runs_dir, 'MODEL_ENTITY_REBINDING_CONTRACT.json'))
    gen_contract = load_json(os.path.join(runs_dir, 'GENERATED_INPUT_CONTRACT.json'))
    pbs_contract = load_json(os.path.join(runs_dir, 'PBS_EXECUTION_CONTRACT.json'))
    notif_contract = load_json(os.path.join(runs_dir, 'NOTIFICATION_CONTRACT.json'))
    ev_contract = load_json(os.path.join(runs_dir, 'EVIDENCE_RETENTION_CONTRACT.json'))
    f30_dec = load_json(os.path.join(runs_dir, 'F30_DECISION.json'))
    no_exec = load_json(os.path.join(runs_dir, 'NO_EXECUTION_AUDIT.json'))

    if not f29_inv or f29_inv.get('corrected_classification') != 'f29_m2rmbuild4_package_invalid_no_submission_authorized':
        failures.append("F29_INVALIDATION_AUDIT missing or invalid")

    if not topo_api or not topo_api.get('edge_get_faces_returns_integer_ids', False):
        failures.append("ABAQUS_TOPOLOGY_API_AUDIT missing or invalid")

    if not mesh_conn or mesh_conn.get('required_bridge_element_count') != 0:
        failures.append("MESH_CONNECTIVITY_AUDIT_CONTRACT missing or invalid")

    if not src_out or 'node_output' not in src_out or 'element_output' not in src_out:
        failures.append("SOURCE_OUTPUT_CONTRACT does not contain separate node and element output requests")

    if not rebind_contract or rebind_contract.get('required_coverage') != 1.0:
        failures.append("MODEL_ENTITY_REBINDING_CONTRACT missing or invalid")

    if not gen_contract or not gen_contract.get('require_hash_inequality', False):
        failures.append("GENERATED_INPUT_CONTRACT missing or invalid")

    if not pbs_contract or pbs_contract.get('expected_counters', {}).get('standard_solver_calls') != 0:
        failures.append("PBS_EXECUTION_CONTRACT specifies non-zero solver calls")

    if not f30_dec or f30_dec.get('classification') != 'f30_m2rmbuild5_static_clean_linux_qualified_not_authorized':
        failures.append("F30_DECISION classification mismatch")

    if not no_exec or no_exec.get('execution_authorized', True):
        failures.append("NO_EXECUTION_AUDIT execution_authorized is true")

    # 2. Check Package Files
    pbs_file = os.path.join(pkg_dir, 'M2RMBUILD5.pbs')
    builder_file = os.path.join(pkg_dir, 'runtime', 'build_f30_geometry_backed_model.py')
    gen_val_file = os.path.join(pkg_dir, 'runtime', 'validate_generated_input.py')
    run_val_file = os.path.join(pkg_dir, 'runtime', 'validate_f30_runtime_audits.py')
    report_gen_file = os.path.join(pkg_dir, 'runtime', 'generate_missing_evidence_report.py')

    for pf in [pbs_file, builder_file, gen_val_file, run_val_file, report_gen_file, orch_script]:
        if not os.path.exists(pf):
            failures.append("Required file missing: " + str(pf))

    # 3. Check Builder Logic
    if os.path.exists(builder_file):
        with open(builder_file, 'r') as f:
            b_content = f.read()
        if "getFaces()" not in b_content or "geom_part.faces[i]" not in b_content:
            failures.append("builder script does not use geom_part.faces[i] face resolution")
        if "getNodes()" not in b_content or "elem.connectivity" in b_content and "set(n.label for n in nodes)" not in b_content:
            failures.append("builder script does not use elem.getNodes() for node labels")
        if "F-Output-1" not in b_content or "F-Output-2" not in b_content:
            failures.append("builder script does not reconstruct separate F-Output-1 and F-Output-2 requests")
        if "expected_source_entity_keys" not in b_content:
            failures.append("builder script does not compute set-based exact source coverage")

    # 4. Check Orchestrator Logic
    if os.path.exists(orch_script):
        with open(orch_script, 'r') as f:
            o_content = f.read()
        if "PACKAGE_REL_PATH" not in o_content:
            failures.append("Orchestrator does not use repository-relative package pathspec")

    # Output result
    if len(failures) == 0:
        result = {
            "classification": "pass",
            "failures": []
        }
        print(json.dumps(result, indent=2))
        sys.exit(0)
    else:
        result = {
            "classification": "fail",
            "failures": failures
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

if __name__ == '__main__':
    main()
