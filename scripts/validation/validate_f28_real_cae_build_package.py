#!/usr/bin/env python3
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F28_DIR = os.path.join(ROOT_DIR, 'runs', 'hpc', 'stage_f', 'f28_real_cae_build_package')
PACKAGE_DIR = os.path.join(ROOT_DIR, 'models', 'generated', 'mode_ii', 'f28_real_cae_build_package')

def main():
    failures = []
    
    # 1. Verify JSON evidence files in F28_DIR
    required_json = [
        'F27_INVALIDATION_AUDIT.json',
        'SOURCE_ENTITY_SPEC.json',
        'SOURCE_REGION_MAP.json',
        'INSTANCE_REPLACEMENT_API_AUDIT.json',
        'MODEL_ENTITY_REBINDING_CONTRACT.json',
        'PBS_EXECUTION_CONTRACT.json',
        'NOTIFICATION_CONTRACT.json',
        'EVIDENCE_RETENTION_CONTRACT.json',
        'F28_DECISION.json',
        'NO_EXECUTION_AUDIT.json',
        'PACKAGE_MANIFEST.json',
        'F28_RUNTIME_MANIFEST.json',
        'EXECUTION_COUNTERS.json',
        'STATUS.json'
    ]
    for item in required_json:
        path = os.path.join(F28_DIR, item)
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
                
    # 2. F27 Invalidation Audit verification
    invalidation_path = os.path.join(F28_DIR, 'F27_INVALIDATION_AUDIT.json')
    if os.path.isfile(invalidation_path):
        with open(invalidation_path, 'r', encoding='utf-8') as h:
            inv = json.load(h)
        if not inv.get('f27_qualification_invalidated'):
            failures.append('f27_qualification_invalidated must be true')

    # 3. Builder Script API & Reconstruction verification
    builder_path = os.path.join(PACKAGE_DIR, 'runtime', 'build_f28_geometry_backed_model.py')
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
        if 'geom_part.Set' not in b_text or 'assembly.Set' not in b_text:
            failures.append('builder missing actual Set reconstruction calls')
        if 'm.DisplacementBC' not in b_text:
            failures.append('builder missing m.DisplacementBC reconstruction call')
        if 'm.Equation' not in b_text:
            failures.append('builder missing m.Equation reconstruction call')

    # 4. F28 Decision Gate verification
    decision_path = os.path.join(F28_DIR, 'F28_DECISION.json')
    if os.path.isfile(decision_path):
        with open(decision_path, 'r', encoding='utf-8') as h:
            decision = json.load(h)
        if decision.get('final_classification') != 'f28_m2rmbuild3_static_clean_linux_qualified_not_authorized':
            failures.append('invalid final_classification')
        if decision.get('prepared_job') != 'M2RMBUILD3':
            failures.append('prepared_job must be M2RMBUILD3')
        if decision.get('execution_authorized') is not False:
            failures.append('execution_authorized must be false')

    # 5. Execution counters verification
    counters_path = os.path.join(F28_DIR, 'EXECUTION_COUNTERS.json')
    if os.path.isfile(counters_path):
        with open(counters_path, 'r', encoding='utf-8') as h:
            counters = json.load(h)
        if counters.get('cae_builder_calls') != 1:
            failures.append('cae_builder_calls must be 1')
        if counters.get('standard_solver_calls') != 0:
            failures.append('standard_solver_calls must be 0')

    # 6. Verify PBS script contents
    pbs_path = os.path.join(PACKAGE_DIR, 'M2RMBUILD3.pbs')
    if os.path.isfile(pbs_path):
        with open(pbs_path, 'r', encoding='utf-8') as h:
            pbs_text = h.read()
        if '/scratch/pr21vyci/' not in pbs_text:
            failures.append('M2RMBUILD3.pbs missing /scratch/pr21vyci/ root')
        if 'module load gcc/11.4.0' not in pbs_text or 'module load abaqus/2023' not in pbs_text:
            failures.append('M2RMBUILD3.pbs missing qualified module sequence')
        if 'abaqus job=' in pbs_text:
            failures.append('M2RMBUILD3.pbs contains prohibited Abaqus/Standard solver call')
        if 'trap - EXIT' not in pbs_text:
            failures.append('M2RMBUILD3.pbs missing trap - EXIT')
        if 'MISSING_EVIDENCE_REPORT.json' not in pbs_text:
            failures.append('M2RMBUILD3.pbs missing MISSING_EVIDENCE_REPORT.json')

    # 7. Orchestrator verification
    orch_path = os.path.join(ROOT_DIR, 'scripts', 'hpc', 'stage_f', 'submit_stage_f28_cae_build_qualification.sh')
    if os.path.isfile(orch_path):
        with open(orch_path, 'r', encoding='utf-8') as h:
            orch_text = h.read()
        if 'PACKAGE_PREP_SHA="7c2c680bad77301a2d2f8f13c4f001b80eb5827d"' not in orch_text:
            failures.append('submit_stage_f28_cae_build_qualification.sh missing exact PACKAGE_PREP_SHA')
        if 'git merge-base --is-ancestor' not in orch_text:
            failures.append('submit_stage_f28_cae_build_qualification.sh missing git merge-base check')

    result = {
        'classification': 'pass' if not failures else 'fail',
        'failures': failures
    }
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1

if __name__ == '__main__':
    sys.exit(main())
