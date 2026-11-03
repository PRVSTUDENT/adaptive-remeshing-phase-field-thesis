import hashlib, json
files = [
    'results/validation/c6_r5_independent_review_remediation_analysis.json',
    'results/validation/c6_r5_kkt_checkpoint_remediation_evidence.json',
    'project_coordination/candidate_definitions/execute_mode1_package171_r5_c6_coupled_reequilibration.json',
    'project_coordination/review_dispatch/execute_mode1_package171_r5_c6_coupled_reequilibration-FD98382477F364F829842ACD463312160D0891320A3C49829C14632F1E51FCE2.request.json',
    'project_coordination/review_dispatch/execute_mode1_package171_r5_c6_coupled_reequilibration-FD98382477F364F829842ACD463312160D0891320A3C49829C14632F1E51FCE2.response.json',
    'tests/unit/test_package171_r5_c6_coupled_driver_gates.py',
    'tests/unit/test_package171_r5_c6_coupled_driver_readiness.py',
    'tests/unit/test_package171_r5_c6_coupled_driver_integration.py',
    'scripts/state_transfer/driver_package171_r5_c6_coupled_pdas.py',
    'models/pandey_kumar_mode1/171_c6_package171_r5_c3_0_reequilibration/PACKAGE_MANIFEST.json',
    'models/pandey_kumar_mode1/171_c6_package171_r5_c3_0_reequilibration/M1_C6_PACKAGE171_R5_AUTHORIZATION.json',
    'models/pandey_kumar_mode1/171_c6_package171_r5_c3_0_reequilibration/EXECUTION_MANIFEST.json',
    'models/pandey_kumar_mode1/171_c6_package171_r5_c3_0_reequilibration/submit_M1_C6_P171_R5_C3_0.pbs'
]
res = {f: hashlib.sha256(open(f, 'rb').read()).hexdigest().upper() for f in files}
print(json.dumps(res, indent=2))
