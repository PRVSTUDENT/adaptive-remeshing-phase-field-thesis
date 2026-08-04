from __future__ import print_function
import hashlib, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
F23_DIR = os.path.join(ROOT, 'runs', 'hpc', 'stage_f', 'f23_offline_adaptive_region_investigation')

def read_text(rel):
    with open(os.path.join(ROOT, rel), 'rb') as h:
        return h.read().decode('utf-8')

def validate():
    failures = []
    
    # 1. Required JSON artifacts
    required_json = [
        'F20_F21_CONTRACT_COMPARISON.json',
        'ADAPTIVE_REGION_API_EVIDENCE.json',
        'ADAPTIVE_REGION_ASSOCIATION_DECISION.json',
        'PRECALL_RECOGNITION_AUDIT_SPEC.json',
        'EVIDENCE_RETENTION_REPAIR_AUDIT.json',
        'NO_EXECUTION_AUDIT.json'
    ]
    for item in required_json:
        path = os.path.join(F23_DIR, item)
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
                
    # 2. Decision gate validation
    decision_path = os.path.join(F23_DIR, 'ADAPTIVE_REGION_ASSOCIATION_DECISION.json')
    if os.path.isfile(decision_path):
        with open(decision_path, 'r', encoding='utf-8') as h:
            decision = json.load(h)
        if decision.get('selected_outcome') != 'Outcome B':
            failures.append('selected_outcome must be Outcome B when association is unresolved offline')
        if decision.get('decision_classification') != 'adaptive_region_association_unresolved_offline':
            failures.append('invalid decision_classification')
        if decision.get('final_classification') != 'f23_adaptive_region_association_unresolved_no_job_prepared':
            failures.append('invalid final_classification')
        if decision.get('m2rmexec2_prepared') is not False:
            failures.append('m2rmexec2_prepared must be false under Outcome B')

    # 3. No execution audit validation
    no_exec_path = os.path.join(F23_DIR, 'NO_EXECUTION_AUDIT.json')
    if os.path.isfile(no_exec_path):
        with open(no_exec_path, 'r', encoding='utf-8') as h:
            no_exec = json.load(h)
        for key in ('solver_executions', 'datacheck_executions', 'adaptivity_process_submissions',
                    'model_adaptiveRemesh_calls', 'native_remesh_calls', 'candidates_generated',
                    'refined_analyses', 'qsub_attempts', 'successful_submissions'):
            if no_exec.get(key) != 0:
                failures.append('NO_EXECUTION_AUDIT key %s must be 0, got %s' % (key, no_exec.get(key)))

    # 4. Required Documentation
    doc_dec = os.path.join(ROOT, 'docs', 'decisions', 'F23_ADAPTIVE_REGION_ASSOCIATION_DECISION.md')
    if not os.path.isfile(doc_dec):
        failures.append('missing docs/decisions/F23_ADAPTIVE_REGION_ASSOCIATION_DECISION.md')

    doc_exp = os.path.join(ROOT, 'docs', 'experiment_records', 'STAGE_F23_OFFLINE_ADAPTIVE_REGION_INVESTIGATION.md')
    if not os.path.isfile(doc_exp):
        failures.append('missing docs/experiment_records/STAGE_F23_OFFLINE_ADAPTIVE_REGION_INVESTIGATION.md')

    return failures

if __name__ == '__main__':
    errs = validate()
    result = {'classification': 'pass' if not errs else 'fail', 'failures': errs}
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(1 if errs else 0)
