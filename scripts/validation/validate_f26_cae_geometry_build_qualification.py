#!/usr/bin/env python3
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F26_DIR = os.path.join(ROOT_DIR, 'runs', 'hpc', 'stage_f', 'f26_cae_geometry_build_qualification')
PACKAGE_DIR = os.path.join(ROOT_DIR, 'models', 'generated', 'mode_ii', 'f26_cae_geometry_build_qualification')

def main():
    failures = []
    
    # 1. Verify JSON evidence files in F26_DIR
    required_json = [
        'F25_INVALIDATION_AUDIT.json',
        'CAE_BUILDER_CONTRACT.json',
        'PBS_EXECUTION_CONTRACT.json',
        'NOTIFICATION_CONTRACT.json',
        'EVIDENCE_RETENTION_CONTRACT.json',
        'F26_DECISION.json',
        'NO_EXECUTION_AUDIT.json',
        'PACKAGE_MANIFEST.json',
        'F26_RUNTIME_MANIFEST.json',
        'EXECUTION_COUNTERS.json',
        'STATUS.json'
    ]
    for item in required_json:
        path = os.path.join(F26_DIR, item)
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
                
    # 2. F25 Invalidation Audit verification
    invalidation_path = os.path.join(F26_DIR, 'F25_INVALIDATION_AUDIT.json')
    if os.path.isfile(invalidation_path):
        with open(invalidation_path, 'r', encoding='utf-8') as h:
            inv = json.load(h)
        if not inv.get('f25_qualification_invalidated'):
            failures.append('f25_qualification_invalidated must be true')

    # 3. Builder Contract verification
    contract_path = os.path.join(F26_DIR, 'CAE_BUILDER_CONTRACT.json')
    if os.path.isfile(contract_path):
        with open(contract_path, 'r', encoding='utf-8') as h:
            ctr = json.load(h)
        if ctr.get('standalone_python_fallback_allowed') is not False:
            failures.append('standalone_python_fallback_allowed must be false')
        if ctr.get('broad_exception_catching_allowed') is not False:
            failures.append('broad_exception_catching_allowed must be false')

    # 4. F26 Decision Gate verification
    decision_path = os.path.join(F26_DIR, 'F26_DECISION.json')
    if os.path.isfile(decision_path):
        with open(decision_path, 'r', encoding='utf-8') as h:
            decision = json.load(h)
        if decision.get('final_classification') != 'f26_m2rmbuild1_clean_linux_qualified_not_authorized':
            failures.append('invalid final_classification')
        if decision.get('prepared_job') != 'M2RMBUILD1':
            failures.append('prepared_job must be M2RMBUILD1')
        if decision.get('m2rmprov1_solver_prepared') is not False:
            failures.append('m2rmprov1_solver_prepared must be false')

    # 5. Execution counters verification
    counters_path = os.path.join(F26_DIR, 'EXECUTION_COUNTERS.json')
    if os.path.isfile(counters_path):
        with open(counters_path, 'r', encoding='utf-8') as h:
            counters = json.load(h)
        if counters.get('cae_builder_calls') != 1:
            failures.append('cae_builder_calls must be 1')
        if counters.get('standard_solver_calls') != 0:
            failures.append('standard_solver_calls must be 0')

    # 6. Verify PBS script contents
    pbs_path = os.path.join(PACKAGE_DIR, 'M2RMBUILD1.pbs')
    if os.path.isfile(pbs_path):
        with open(pbs_path, 'r', encoding='utf-8') as h:
            pbs_text = h.read()
        if 'module load abaqus/2023' not in pbs_text:
            failures.append('M2RMBUILD1.pbs missing module load abaqus/2023')
        if 'python3' in pbs_text and 'abaqus cae' not in pbs_text:
            failures.append('M2RMBUILD1.pbs contains prohibited standalone python3 call')
        if 'abaqus job=' in pbs_text:
            failures.append('M2RMBUILD1.pbs contains prohibited Abaqus/Standard solver call')
        if 'NOTIFICATION_START_TELEGRAM.json' not in pbs_text:
            failures.append('M2RMBUILD1.pbs missing START notification')
        if 'NOTIFICATION_TERMINAL_TELEGRAM.json' not in pbs_text:
            failures.append('M2RMBUILD1.pbs missing TERMINAL notification')
        if 'build_f26_geometry_backed_model.py' not in pbs_text:
            failures.append('M2RMBUILD1.pbs missing builder execution')

    result = {
        'classification': 'pass' if not failures else 'fail',
        'failures': failures
    }
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1

if __name__ == '__main__':
    sys.exit(main())
