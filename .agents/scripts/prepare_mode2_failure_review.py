"""Prepare immutable local review metadata; never dispatch, sign or run a solver."""
from pathlib import Path
import hashlib
import json
import os
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.controller.review_dispatcher import packet

folder='models/pandey_kumar_mode2/294_method_c_mode2/'
evidence=[folder+'mode2_single_job_orchestrator.py',folder+'mode2_runtime.py',
          folder+'audit_cycle1_transfer.py',folder+'audit_frozen_split.py',
          'models/pandey_kumar_mode1/f42_mixed_uel.for',
          'docs/validation/METHOD_C_MODE2_RECOVERY_AUDIT.md',
          folder+'local_windows_full_run/PK_METHOD_C_MODE2_COARSE_JOB1_SUMMARY.json',
          folder+'local_windows_full_run/PK_METHOD_C_MODE2_CYCLE1_SUMMARY.json',
          folder+'local_windows_full_run/cycle1_offline_transfer_audit.json',
          folder+'local_windows_full_run/same_mesh_control_manifest.json',
          folder+'local_windows_full_run/image_manifest.json',
          'tests/unit/test_method_c_mode2_recovery.py']
contract={
    'goal_id':'METHOD_C_MODE2_LPANEL_V1','method':'METHOD_C',
    'operation':'method_c_mode2_lpanel_setup_and_validation',
    'numerical_uncertainty':'Why does fixed-load hold lose 32.28 percent force despite close bulk field integrals? Can an identical-mesh hold separate initialization from remeshing effects?',
    'expected_numerical_result':'Review failed cycle honestly and decide the prepared one-CPU hold-only identical-mesh control; no donor acceptance from failed Cycle 1.',
    'indicator_type':'DAMAGE_INFORMED_SIZING','indicator_role':'METHOD_C_DRIVER',
    'causal_evidence_status':'VERIFIED',
    'causal_evidence':{
        'donor_sha256':'424129D9EA1FD4A9C989A9E1069A4296DF4017F055D2504C51D3414DE976ED88',
        'donor_step':'Step-1','indicator_frame_range':'Coarse terminal increment 200',
        'held_out_later_solution':'Rejected Cycle 1 hold/advance: evaluation only, never sizing/transfer input',
        'uses_future_frames':False,'remesh_time':1.,'maximum_indicator_time':1.}}
definition={
    'operation_id':'method_c_mode2_cycle1_failure',
    'task_id':'METHOD-C-MODE2-CYCLE1-FAILURE',
    'title':'Review failed shear transfer and exact same-mesh hold-only control',
    'author':'codex','registration_status':'PROPOSED_FOR_INDEPENDENT_REVIEW',
    'operation_mode':'READ_ONLY_SCIENTIFIC_EVALUATION','research_contract':contract,
    'evidence_sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest().upper() for p in evidence},
    'source_differences':'Recovered incomplete AGY setup; frozen UEL unchanged; corrected inherited property order, DEPVAR and boundary syntax. New bounded runtime reuses unchanged Case 1 nearest-neighbour transfer. First transfer scientifically fails and stops; see exact report. User expressly accepted the frozen constitutive difference.',
    'review_questions':[
        'Inspect all authentic mesh/damage images through pinned manifest; no successful down-right trajectory is demonstrated.',
        'Do not approve failed cycle or master goal. Assess the exact prepared identical-mesh hold-only control.',
        'Global max-damage gate is not pointwise irreversibility; nearest-neighbour transfer is not bilinear.',
        'Broad measured-tip geometric refinement is used; no native MISESERI/F1852 selector qualification is claimed.',
        'The force gate is evaluated after the two-step job. Forward step ran but is rejected; hold-only control avoids this ambiguity.'],
    'proposed_control':json.loads((ROOT/(folder+'local_windows_full_run/same_mesh_control_manifest.json')).read_text()),
    'evidence_commit':'6ebc669c6','max_new_pbs_submissions':0,'master_goal_status':'OPEN'}
path=ROOT/'project_coordination/candidate_definitions/method_c_mode2_cycle1_failure.json'
path.parent.mkdir(exist_ok=True)
with path.open('x',encoding='utf-8') as stream:
    json.dump(definition,stream,indent=2)
request=packet(ROOT,'method_c_mode2_cycle1_failure')
request['correlation_id']='HND-MODE2-FAILURE-ADAPTER-DRYRUN-20261124'
test=Path(os.environ['TEMP'])/'mode2_dispatcher_packet_dryrun.json'
test.write_text(json.dumps(request,indent=2))
print('PACKET_READY',len(json.dumps(request)),test)
