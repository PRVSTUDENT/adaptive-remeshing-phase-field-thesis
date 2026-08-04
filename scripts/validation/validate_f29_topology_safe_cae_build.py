#!/usr/bin/env python3
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F29_DIR = os.path.join(ROOT_DIR, 'runs', 'hpc', 'stage_f', 'f29_topology_safe_cae_build')
PACKAGE_DIR = os.path.join(ROOT_DIR, 'models', 'generated', 'mode_ii', 'f29_topology_safe_cae_build')

def main():
    failures = []
    
    # 1. Verify JSON evidence files in F29_DIR
    required_json = [
        'F28_INVALIDATION_AUDIT.json',
        'SOURCE_ENTITY_SPEC.json',
        'SOURCE_REGION_MAP.json',
        'SOURCE_OUTPUT_CONTRACT.json',
        'SOURCE_SLIT_TOPOLOGY_CONTRACT.json',
        'INSTANCE_REPLACEMENT_API_AUDIT.json',
        'MODEL_ENTITY_REBINDING_CONTRACT.json',
        'SLIT_TOPOLOGY_CONTRACT.json',
        'GENERATED_INPUT_CONTRACT.json',
        'PBS_EXECUTION_CONTRACT.json',
        'NOTIFICATION_CONTRACT.json',
        'EVIDENCE_RETENTION_CONTRACT.json',
        'F29_DECISION.json',
        'NO_EXECUTION_AUDIT.json',
        'PACKAGE_MANIFEST.json',
        'F29_RUNTIME_MANIFEST.json',
        'EXECUTION_COUNTERS.json',
        'STATUS.json'
    ]
    for item in required_json:
        path = os.path.join(F29_DIR, item)
        if not os.path.isfile(path):
            failures.append('missing JSON artifact: ' + item)
        else:
            try:
                with open(path, 'r', encoding='utf-8') as h:
                    data = json.load(h)
                if not isinstance(data, dict):
                    failures.append('invalid JSON format in ' + item)
            except Exception as e:
                failures.append('failed to parse JSON in ' + item + ': ' + str(e))
                
    # 2. F28 Invalidation Audit verification
    invalidation_path = os.path.join(F29_DIR, 'F28_INVALIDATION_AUDIT.json')
    if os.path.isfile(invalidation_path):
        with open(invalidation_path, 'r', encoding='utf-8') as h:
            inv = json.load(h)
        if not inv.get('f28_qualification_invalidated'):
            failures.append('f28_qualification_invalidated must be true')

    # 3. Builder Script API, Topology & Reconstruction verification
    builder_path = os.path.join(PACKAGE_DIR, 'runtime', 'build_f29_geometry_backed_model.py')
    if os.path.isfile(builder_path):
        with open(builder_path, 'r', encoding='utf-8') as h:
            b_text = h.read()
        if 'STANDARD' not in b_text:
            failures.append('builder missing STANDARD import')
        if "variables=('MISESERI',)" not in b_text:
            failures.append('builder missing variables=(\'MISESERI\',) signature')
        if 'assembly.renameFeature' in b_text:
            failures.append('builder contains prohibited assembly.renameFeature call')
        if 'orphan_instance.suppress()' in b_text:
            failures.append('builder contains prohibited orphan_instance.suppress() call')
        if 'assembly.deleteFeatures' not in b_text:
            failures.append('builder missing assembly.deleteFeatures call')
        if 'm.constraints' not in b_text:
            failures.append('builder missing m.constraints equation inventory')
        if 'pointOn[0][1]' not in b_text:
            failures.append('builder missing face centroid y-coordinate check for slit topology')
        if "assembly.Set(name='All_elem', elements=inst_ref.elements)" not in b_text:
            failures.append('builder missing explicit assembly All_elem set reconstruction')
        if 'FieldOutputRequest' not in b_text:
            failures.append('builder missing FieldOutputRequest explicit reconstruction')

    # 4. Runtime validators import check
    v1 = os.path.join(PACKAGE_DIR, 'runtime', 'validate_f29_runtime_audits.py')
    v2 = os.path.join(PACKAGE_DIR, 'runtime', 'generate_missing_evidence_report.py')
    v3 = os.path.join(PACKAGE_DIR, 'runtime', 'validate_generated_input.py')
    for v_path in [v1, v2, v3]:
        if not os.path.isfile(v_path):
            failures.append('missing runtime validation script: ' + os.path.basename(v_path))
        else:
            with open(v_path, 'r', encoding='utf-8') as h:
                vt = h.read()
            if 'import os' not in vt:
                failures.append(os.path.basename(v_path) + ' missing import os')

    # 5. F29 Decision Gate verification
    decision_path = os.path.join(F29_DIR, 'F29_DECISION.json')
    if os.path.isfile(decision_path):
        with open(decision_path, 'r', encoding='utf-8') as h:
            decision = json.load(h)
        if decision.get('final_classification') != 'f29_m2rmbuild4_static_clean_linux_qualified_not_authorized':
            failures.append('invalid final_classification')
        if decision.get('prepared_job') != 'M2RMBUILD4':
            failures.append('prepared_job must be M2RMBUILD4')
        if decision.get('execution_authorized') is not False:
            failures.append('execution_authorized must be false')

    # 6. Execution counters verification
    counters_path = os.path.join(F29_DIR, 'EXECUTION_COUNTERS.json')
    if os.path.isfile(counters_path):
        with open(counters_path, 'r', encoding='utf-8') as h:
            counters = json.load(h)
        if counters.get('cae_builder_calls') != 0:
            failures.append('cae_builder_calls must be 0 prior to execution')
        if counters.get('standard_solver_calls') != 0:
            failures.append('standard_solver_calls must be 0')

    # 7. Verify PBS script contents
    pbs_path = os.path.join(PACKAGE_DIR, 'M2RMBUILD4.pbs')
    if os.path.isfile(pbs_path):
        with open(pbs_path, 'r', encoding='utf-8') as h:
            pbs_text = h.read()
        if '/scratch/pr21vyci/' not in pbs_text:
            failures.append('M2RMBUILD4.pbs missing /scratch/pr21vyci/ root')
        if 'notifications.env' not in pbs_text:
            failures.append('M2RMBUILD4.pbs missing mandatory notifications.env check')
        if 'stat -c "%a"' not in pbs_text and 'stat -f "%Lp"' not in pbs_text:
            failures.append('M2RMBUILD4.pbs missing notification permissions check')
        if 'exit 15' not in pbs_text:
            failures.append('M2RMBUILD4.pbs missing exit 15 on START notification failure')
        if 'abaqus job=' in pbs_text:
            failures.append('M2RMBUILD4.pbs contains prohibited Abaqus/Standard solver call')
        if 'trap - EXIT' not in pbs_text:
            failures.append('M2RMBUILD4.pbs missing trap - EXIT')

    # 8. Orchestrator verification
    orch_path = os.path.join(ROOT_DIR, 'scripts', 'hpc', 'stage_f', 'submit_stage_f29_cae_build_qualification.sh')
    if os.path.isfile(orch_path):
        with open(orch_path, 'r', encoding='utf-8') as h:
            orch_text = h.read()
        if 'PACKAGE_PREP_SHA="b2a3535742a08961688ee5e65dbe4c8e412e4118"' not in orch_text:
            failures.append('submit_stage_f29_cae_build_qualification.sh missing exact PACKAGE_PREP_SHA')
        if 'git merge-base --is-ancestor' not in orch_text:
            failures.append('submit_stage_f29_cae_build_qualification.sh missing git merge-base check')
        if 'git diff --quiet' not in orch_text:
            failures.append('submit_stage_f29_cae_build_qualification.sh missing git diff --quiet check')
        if 'git ls-tree -r' not in orch_text:
            failures.append('submit_stage_f29_cae_build_qualification.sh missing git ls-tree blob comparison')

    result = {
        'classification': 'pass' if not failures else 'fail',
        'failures': failures
    }
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1

if __name__ == '__main__':
    sys.exit(main())
