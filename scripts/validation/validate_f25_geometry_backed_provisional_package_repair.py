#!/usr/bin/env python3
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F25_DIR = os.path.join(ROOT_DIR, 'runs', 'hpc', 'stage_f', 'f25_geometry_backed_provisional_package_repair')
PACKAGE_DIR = os.path.join(ROOT_DIR, 'models', 'generated', 'mode_ii', 'f25_geometry_backed_provisional_package_repair')

def main():
    failures = []
    
    # 1. Verify JSON evidence files in F25_DIR
    required_json = [
        'F24_INVALIDATION_AUDIT.json',
        'REAL_GEOMETRY_BUILDER_AUDIT.json',
        'PBS_EXECUTION_CONTRACT.json',
        'NOTIFICATION_CONTRACT.json',
        'EVIDENCE_RETENTION_CONTRACT.json',
        'F25_DECISION.json',
        'NO_EXECUTION_AUDIT.json',
        'PACKAGE_MANIFEST.json',
        'F25_RUNTIME_MANIFEST.json',
        'STATUS.json',
        'GEOMETRY_BACKED_MODEL_AUDIT.json'
    ]
    for item in required_json:
        path = os.path.join(F25_DIR, item)
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
                
    # 2. F24 Invalidation Audit verification
    invalidation_path = os.path.join(F25_DIR, 'F24_INVALIDATION_AUDIT.json')
    if os.path.isfile(invalidation_path):
        with open(invalidation_path, 'r', encoding='utf-8') as h:
            inv = json.load(h)
        if not inv.get('f24_qualification_invalid'):
            failures.append('f24_qualification_invalid must be true')
            
    # 3. Geometry-backed model audit verification
    audit_path = os.path.join(PACKAGE_DIR, 'GEOMETRY_BACKED_MODEL_AUDIT.json')
    if os.path.isfile(audit_path):
        with open(audit_path, 'r', encoding='utf-8') as h:
            audit = json.load(h)
        if not audit.get('contract_pass'):
            failures.append('GEOMETRY_BACKED_MODEL_AUDIT contract_pass must be true')
        if not audit.get('generated_differs_from_source'):
            failures.append('generated_differs_from_source must be true')
        if audit.get('geometry_face_count', 0) <= 0:
            failures.append('geometry_face_count must be > 0')

    # 4. F25 Decision Gate verification
    decision_path = os.path.join(F25_DIR, 'F25_DECISION.json')
    if os.path.isfile(decision_path):
        with open(decision_path, 'r', encoding='utf-8') as h:
            decision = json.load(h)
        if decision.get('final_classification') != 'f25_m2rmprov1_real_geometry_builder_clean_linux_qualified_not_authorized':
            failures.append('invalid final_classification')
        if decision.get('prepared_job') != 'M2RMPROV1':
            failures.append('prepared_job must be M2RMPROV1')
        if decision.get('m2rmexec2_prepared') is not False:
            failures.append('m2rmexec2_prepared must be false')

    # 5. No execution audit verification
    no_exec_path = os.path.join(F25_DIR, 'NO_EXECUTION_AUDIT.json')
    if os.path.isfile(no_exec_path):
        with open(no_exec_path, 'r', encoding='utf-8') as h:
            no_exec = json.load(h)
        for key in ('solver_executions', 'datacheck_executions', 'model_adaptiveRemesh_calls',
                    'candidates_generated', 'refined_analyses', 'qsub_attempts', 'successful_submissions'):
            if no_exec.get(key) != 0:
                failures.append('NO_EXECUTION_AUDIT key %s must be 0, got %s' % (key, no_exec.get(key)))

    # 6. Verify PBS script contents
    pbs_path = os.path.join(PACKAGE_DIR, 'M2RMPROV1.pbs')
    if os.path.isfile(pbs_path):
        with open(pbs_path, 'r', encoding='utf-8') as h:
            pbs_text = h.read()
        if 'module load abaqus' not in pbs_text:
            failures.append('M2RMPROV1.pbs missing module load abaqus')
        if 'NOTIFICATION_START_TELEGRAM.json' not in pbs_text:
            failures.append('M2RMPROV1.pbs missing START notification')
        if 'NOTIFICATION_TERMINAL_TELEGRAM.json' not in pbs_text:
            failures.append('M2RMPROV1.pbs missing TERMINAL notification')
        if 'build_f25_geometry_backed_model.py' not in pbs_text:
            failures.append('M2RMPROV1.pbs missing builder execution')

    result = {
        'classification': 'pass' if not failures else 'fail',
        'failures': failures
    }
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1

if __name__ == '__main__':
    sys.exit(main())
