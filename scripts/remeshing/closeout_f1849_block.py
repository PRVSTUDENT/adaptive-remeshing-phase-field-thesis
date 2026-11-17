"""Preserve the pending bridge transaction and release repository ownership."""
from pathlib import Path
import json,datetime,hashlib,subprocess,csv,io
ROOT=Path(__file__).resolve().parents[2]
now=datetime.datetime.now().astimezone().isoformat()
bridge=Path.home()/'OpenClawPAD/ChatGPTBridge'
request=bridge/'bridge_request.ready';response=bridge/'bridge_response.ready'
state={'task_id':'F1849-DAMAGE-ENVELOPE-FRAMEWORK','correlation_id':'HND-F1849-DAMAGE-ENVELOPE-FRAMEWORK-001','master_goal_status':'OPEN','status':'TRANSPORT_TIMEOUT_PENDING_ORIGINAL_TRANSACTION','request_preserved':request.exists(),'response_exists':response.exists(),'paste_send_verified':False,'timeout_minutes':3,'ui_error':'Computer Use native pipe unavailable; browser access host unavailable','resume_condition':'Restore the existing PAD/browser bridge runtime; process the preserved ORIGINAL request. Validate the matching response using .agents/scripts/reconcile_f1849_response.ps1. Do not republish or start a duplicate flow. Cases1/3 additionally require the exact missing Job1/envelope artifacts.','recorded_at':now}
if request.exists():state['final_request_sha256']=hashlib.sha256(request.read_bytes()).hexdigest()
p=ROOT/'project_coordination/f1849_bridge_block.json';p.write_text(json.dumps(state,indent=2)+'\n')
session=ROOT/'project_coordination/sessions/2026-11-17_codex_f1849_damage_envelope.md'
with session.open('a',encoding='utf-8') as f:
    f.write('\nBridge '+state['correlation_id']+' published through guarded wrapper, exactly one trigger header verified; existing PAD runtime PID24288 reused. Three-minute timeout, no response; native/browser UI host unavailable, so actual paste/send NOT VERIFIED. Original ready request preserved. No resend. Resume with existing transaction and validator. MASTER_GOAL_OPEN; releasing session on genuine transport and donor blocks.\n')
report=ROOT/'docs/validation/F1849_DAMAGE_ENVELOPE_FRAMEWORK_REPORT.md'
with report.open('a',encoding='utf-8') as f:
    f.write('\n## Guarded review transport block\n\nArtifacts pushed at `92815645952ddf56272c43e78c0272f1849f2f43`; image links resolve. Guarded transaction `'+state['correlation_id']+'` timed out after three minutes without a response. Existing PAD flow reused; actual paste/send unverified because native and browser UI hosts are unavailable. Request preserved, no duplicate dispatch, no scientific approval. Exact state/resume condition: `project_coordination/f1849_bridge_block.json`. Master goal OPEN.\n')
task=ROOT/'project_coordination/ACTIVE_TASK.json';d=json.loads(task.read_text());d.update(status='BLOCKED_TRANSPORT_AND_MISSING_DONORS',task_status='BLOCKED_TRANSPORT_AND_MISSING_DONORS',review_verdict='PENDING',master_goal_status='OPEN',notes=state['resume_condition']);task.write_text(json.dumps(d,indent=2)+'\n')
lock=ROOT/'project_coordination/ACTIVE_SESSION.json';d=json.loads(lock.read_text());assert d['agent']=='codex';d.update(active=False,completed_at=now,notes='User-authorized Codex execution preserved as partial. Guarded review timed out; original transaction remains pending. Zero PBS; master OPEN.');lock.write_text(json.dumps(d,indent=2)+'\n')
ledger=ROOT/'project_coordination/TASK_LEDGER.csv'
lines=ledger.read_text(encoding='utf-8-sig').splitlines(keepends=True);fields=next(csv.reader([lines[0]]));out=[]
for line in lines:
    if line.startswith('F1849-DAMAGE-ENVELOPE-FRAMEWORK,'):
        row=next(csv.reader([line]));row[fields.index('status')]='blocked_transport_and_missing_donors';row[fields.index('updated_at')]=now
        buf=io.StringIO(newline='');csv.writer(buf).writerow(row);out.append(buf.getvalue())
    else:out.append(line)
ledger.write_text(''.join(out),encoding='utf-8',newline='')
current=ROOT/'project_coordination/CURRENT_STATE.md'
current.write_text('## F1849 transport block — '+now+'\n\nOriginal guarded request HND-F1849-DAMAGE-ENVELOPE-FRAMEWORK-001 preserved; no response after 3 minutes, paste/send unverified, native/browser UI host unavailable. Resume same transaction; no duplicate dispatch. Cases1/3 missing donors. Codex session released; master OPEN.\n\n'+current.read_text(encoding='utf-8-sig'),encoding='utf-8')
files=['scripts/remeshing/closeout_f1849_block.py','.agents/scripts/reconcile_f1849_response.ps1','project_coordination/f1849_bridge_block.json','project_coordination/ACTIVE_SESSION.json','project_coordination/ACTIVE_TASK.json','project_coordination/TASK_LEDGER.csv','project_coordination/CURRENT_STATE.md','project_coordination/sessions/2026-11-17_codex_f1849_damage_envelope.md','docs/validation/F1849_DAMAGE_ENVELOPE_FRAMEWORK_REPORT.md']
subprocess.run(['git','add','--']+files,cwd=ROOT,check=True)
subprocess.run(['git','commit','-m','F1849: preserve timed-out review transaction and release Codex ownership'],cwd=ROOT,check=True)
subprocess.run(['git','push','origin','main'],cwd=ROOT,check=True)
print(json.dumps(state))
