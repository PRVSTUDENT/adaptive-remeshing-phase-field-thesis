#!/usr/bin/env python3
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F27_DIR = os.path.join(ROOT_DIR, 'runs', 'hpc', 'stage_f', 'f27_cae_build_package_repair')
PACKAGE_DIR = os.path.join(ROOT_DIR, 'models', 'generated', 'mode_ii', 'f27_cae_build_package_repair')

def main():
    failures = []
    
    # 1. Verify JSON evidence files in F27_DIR
    required_json = [
        'F26_INVALIDATION_AUDIT.json',
        'ABAQUS_API_CORRECTION_AUDIT.json',
        'INSTANCE_REPLACEMENT_API_AUDIT.json',
        'MODEL_ENTITY_REBINDING_CONTRACT.json',
        'PBS_EXECUTION_CONTRACT.json',
        'NOTIFICATION_CONTRACT.json',
        'EVIDENCE_RETENTION_CONTRACT.json',
        'F27_DECISION.json',
        'NO_EXECUTION_AUDIT.json',
        'PACKAGE_MANIFEST.json',
        'F27_RUNTIME_MANIFEST.json',
        'EXECUTION_COUNTERS.json',
        'STATUS.json'
    ]
    for item in required_json:
        path = os.path.join(F27_DIR, item)
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
                
    # 2. F26 Invalidation Audit verification
    invalidation_path = os.path.join(F27_DIR, 'F26_INVALIDATION_AUDIT.json')
    if os.path.isfile(invalidation_path):
        with open(invalidation_path, 'r', encoding='utf-8') as h:
            inv = json.load(h)
        if not inv.get('f26_qualification_invalidated'):
            failures.append('f26_qualification_invalidated must be true')

    # 3. Builder Script API & Rebinding verification
    builder_path = os.path.join(PACKAGE_DIR, 'runtime', 'build_f27_geometry_backed_model.py')
    if os.path.isfile(builder_path):
        with open(builder_path, 'r', encoding='utf-8') as h:
            b_text = h.read()
        if 'STANDARD' not in b_text:
            failures.append('builder missing STANDARD import')
        if "variables=('MISESERI',)" not in b_text:
            failures.append('builder missing variables=(\'MISESERI\',) signature')
        if 'errorIndicator=' in b_text:
            failures.append('builder contains prohibited errorIndicator= argument')
        if 'orphan_instance.suppress()' in b_text:
            failures.append('builder contains prohibited orphan_instance.suppress() call')
        if 'assembly.suppressFeatures' not in b_text:
            failures.append('builder missing assembly.suppressFeatures call')
        if 'assembly.renameFeature' not in b_text:
            failures.append('builder missing assembly.renameFeature call')
        if 'MODEL_ENTITY_REBINDING_AUDIT.json' not in b_text:
            failures.append('builder missing MODEL_ENTITY_REBINDING_AUDIT.json generation')

    # 4. F27 Decision Gate verification
    decision_path = os.path.join(F27_DIR, 'F27_DECISION.json')
    if os.path.isfile(decision_path):
        with open(decision_path, 'r', encoding='utf-8') as h:
            decision = json.load(h)
        if decision.get('final_classification') != 'f27_m2rmbuild2_clean_linux_qualified_not_authorized':
            failures.append('invalid final_classification')
        if decision.get('prepared_job') != 'M2RMBUILD2':
            failures.append('prepared_job must be M2RMBUILD2')
        if decision.get('m2rmprov1_solver_prepared') is not False:
            failures.append('m2rmprov1_solver_prepared must be false')

    # 5. Execution counters verification
    counters_path = os.path.join(F27_DIR, 'EXECUTION_COUNTERS.json')
    if os.path.isfile(counters_path):
        with open(counters_path, 'r', encoding='utf-8') as h:
            counters = json.load(h)
        if counters.get('cae_builder_calls') != 1:
            failures.append('cae_builder_calls must be 1')
        if counters.get('standard_solver_calls') != 0:
            failures.append('standard_solver_calls must be 0')

    # 6. Verify PBS script contents
    pbs_path = os.path.join(PACKAGE_DIR, 'M2RMBUILD2.pbs')
    if os.path.isfile(pbs_path):
        with open(pbs_path, 'r', encoding='utf-8') as h:
            pbs_text = h.read()
        if '/scratch/pr21vyci/' not in pbs_text:
            failures.append('M2RMBUILD2.pbs missing /scratch/pr21vyci/ root')
        if 'module load gcc/11.4.0' not in pbs_text or 'module load abaqus/2023' not in pbs_text:
            failures.append('M2RMBUILD2.pbs missing qualified module sequence')
        if 'python3' in pbs_text and 'abaqus cae' not in pbs_text:
            failures.append('M2RMBUILD2.pbs contains prohibited standalone python3 call')
        if 'abaqus job=' in pbs_text:
            failures.append('M2RMBUILD2.pbs contains prohibited Abaqus/Standard solver call')
        if 'notifications.env' not in pbs_text:
            failures.append('M2RMBUILD2.pbs missing notifications.env loading')
        if '"ok":true' not in pbs_text and "'ok':true" not in pbs_text and r'\"ok\":true' not in pbs_text:
            failures.append('M2RMBUILD2.pbs missing Telegram API ok verification')
        if 'build_f27_geometry_backed_model.py' not in pbs_text:
            failures.append('M2RMBUILD2.pbs missing builder execution')

    result = {
        'classification': 'pass' if not failures else 'fail',
        'failures': failures
    }
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1

if __name__ == '__main__':
    sys.exit(main())
