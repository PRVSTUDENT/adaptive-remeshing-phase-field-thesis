#!/usr/bin/env python3
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F24_DIR = os.path.join(ROOT_DIR, 'runs', 'hpc', 'stage_f', 'f24_geometry_and_odb_compatibility_gate')
PACKAGE_DIR = os.path.join(ROOT_DIR, 'models', 'generated', 'mode_ii', 'f24_geometry_and_odb_compatibility_gate')

def main():
    failures = []
    
    # 1. Verify JSON evidence files in F24_DIR
    required_json = [
        'OFFICIAL_ADAPTIVE_REMESH_CONTRACT.json',
        'GEOMETRY_BACKED_MODEL_CONTRACT.json',
        'SOURCE_ODB_COMPATIBILITY_AUDIT.json',
        'F24_DECISION.json',
        'PRECALL_RECOGNITION_AUDIT_SPEC.json',
        'EVIDENCE_RETENTION_CONTRACT.json',
        'NO_EXECUTION_AUDIT.json',
        'PACKAGE_MANIFEST.json',
        'F24_RUNTIME_MANIFEST.json',
        'STATUS.json'
    ]
    for item in required_json:
        path = os.path.join(F24_DIR, item)
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
                
    # 2. F24 Decision Gate verification
    decision_path = os.path.join(F24_DIR, 'F24_DECISION.json')
    if os.path.isfile(decision_path):
        with open(decision_path, 'r', encoding='utf-8') as h:
            decision = json.load(h)
        if decision.get('selected_outcome') != 'Outcome B':
            failures.append('selected_outcome must be Outcome B')
        if decision.get('decision_classification') != 'matching_geometry_backed_provisional_analysis_required':
            failures.append('invalid decision_classification')
        if decision.get('final_classification') != 'f24_m2rmprov1_clean_linux_qualified_not_authorized':
            failures.append('invalid final_classification')
        if decision.get('prepared_job') != 'M2RMPROV1':
            failures.append('prepared_job must be M2RMPROV1')
        if decision.get('m2rmexec2_prepared') is not False:
            failures.append('m2rmexec2_prepared must be false under Outcome B')

    # 3. No execution audit verification
    no_exec_path = os.path.join(F24_DIR, 'NO_EXECUTION_AUDIT.json')
    if os.path.isfile(no_exec_path):
        with open(no_exec_path, 'r', encoding='utf-8') as h:
            no_exec = json.load(h)
        for key in ('solver_executions', 'datacheck_executions', 'model_adaptiveRemesh_calls',
                    'candidates_generated', 'refined_analyses', 'qsub_attempts', 'successful_submissions'):
            if no_exec.get(key) != 0:
                failures.append('NO_EXECUTION_AUDIT key %s must be 0, got %s' % (key, no_exec.get(key)))
                
    # 4. Verify package files in PACKAGE_DIR
    required_package_files = ['M2RMPROV1.inp', 'M2RMPROV1.pbs', 'F24_CLEAN_LINUX_QUALIFICATION.json', 'F24_NO_EXECUTION_AUDIT.json']
    for pfile in required_package_files:
        path = os.path.join(PACKAGE_DIR, pfile)
        if not os.path.isfile(path):
            failures.append('missing package file: ' + pfile)
            
    # 5. Verify orchestrator script
    orchestrator = os.path.join(ROOT_DIR, 'scripts', 'hpc', 'stage_f', 'submit_stage_f24_provisional_analysis.sh')
    if not os.path.isfile(orchestrator):
        failures.append('missing orchestrator script: submit_stage_f24_provisional_analysis.sh')
        
    result = {
        'classification': 'pass' if not failures else 'fail',
        'failures': failures
    }
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1

if __name__ == '__main__':
    sys.exit(main())
