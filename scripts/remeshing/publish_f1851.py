from pathlib import Path
import json,hashlib,subprocess,csv,datetime
R=Path(__file__).resolve().parents[2];B=R/'models/pandey_kumar_mode1/281_f1851_native_diagnostics'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'results/validation/f1851_diagnostics_summary.json';s=json.loads(p.read_text())
s['source_termination']={}
for tag,rel in [('case2','277_f1838_case2_native_pilot/PK_HOLE_COARSE_F1838_PILOT.sta'),('f1720','213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.sta')]:
    sta=R/'models/pandey_kumar_mode1'/rel;lines=sta.read_text().splitlines();assert 'THE ANALYSIS HAS NOT BEEN COMPLETED' in '\n'.join(lines[-15:]);s['source_termination'][tag]={'status_file':sta.relative_to(R).as_posix(),'sha256':sha(sta),'last_lines':lines[-12:]}
for step in ('Step-1','Step-2'):
    f=B/('f1720_%s_extracted.odb'%step);s['inventory'].append({'source':f.relative_to(R).as_posix(),'bytes':f.stat().st_size,'sha256':sha(f),'step':step,'frame_index':0,'role':'Generated single-frame native-copy diagnostic ODB; excluded from Git as solver binary'})
s['tests']='4 passed: tests/unit/test_f1851_diagnostics.py'
p.write_text(json.dumps(s,indent=2)+'\n')
report=R/'docs/validation/F1851_NATIVE_MISESERI_DIAGNOSTICS_REPORT.md'
with report.open('a',encoding='utf-8') as f:
    f.write('\n## Generated diagnostic ODB inventory\n\n')
    for i in s['inventory'][-2:]:f.write('- `%s`: %d bytes, SHA256 `%s`; locally generated native-copy donor, not committed as a solver binary.\n'%(i['source'],i['bytes'],i['sha256']))
    f.write('\nFour focused tests PASS. Source termination excerpts and status-file hashes are retained in the summary. No native-method acceptance or completed loading history is claimed.\n')
now=datetime.datetime.now().astimezone().isoformat()
session=R/'project_coordination/sessions/2026-11-18_codex_f1851_native_diagnostics.md';session.write_text('# F1851 user-directed native diagnostics\n\nUser attachment requested task directly while F1850 transport remains unverified. Existing ODBs only, zero PBS. Coordinate/connectivity/field mapping exact. Original Case2 direct remesh fails missing EVOL. F1720 native-copy pairs match count/bodySHA exactly at Step1 and Step2. Both original solves incomplete; F1720 maxd=.5252. Corrected count/area coverage; 4 tests PASS. Frozen framework untouched. Evidence pending review; master OPEN.\n')
task=R/'project_coordination/ACTIVE_TASK.json';t=json.loads(task.read_text());t.update(task_id='F1851-NATIVE-DIAGNOSTICS',title='Existing-donor native error and extraction diagnostics',status='COMPLETED_PENDING_REVIEW',task_status='COMPLETED_PENDING_REVIEW',review_verdict='PENDING',review_correlation_id='HND-F1851-NATIVE-DIAGNOSTICS-001',checkpoint_artifact=report.relative_to(R).as_posix(),notes='Direct user request; F1850 transport not authenticated. 0 new PBS. Both source analyses incomplete; original C2 missing EVOL; mapping exact; F1720 paired remesh hashes match.');task.write_text(json.dumps(t,indent=2)+'\n')
state=R/'project_coordination/CURRENT_STATE.md';state.write_text('## F1851 numerical diagnostics '+now+'\n\nDirect user-requested task completed, review pending. Original Case2 has no EVOL; direct original remesh FAILED as expected by Abaqus. Copied error/base/damage and mesh mapping exact. F1720 original/extracted pairs match count/body SHA (13738 Step1,13169 Step2). Both source status files explicitly incomplete; F1720 maxIPdamage .5252 contradicts historical terminal-severance description. F1840 distal half-l0 count coverage91.48%, area69.86%. Four tests PASS, no framework edits, zero PBS; master OPEN.\n\n'+state.read_text(encoding='utf-8-sig'),encoding='utf-8')
files=[]
for pat in ['scripts/remeshing/*f1851*','tests/unit/test_f1851*','models/pandey_kumar_mode1/281_f1851_native_diagnostics/**/*.json','models/pandey_kumar_mode1/281_f1851_native_diagnostics/**/*.inp','results/figures/fig_f1851*','results/validation/f1851*','docs/validation/F1851*','project_coordination/sessions/*f1851*']:
    files += [x.relative_to(R).as_posix() for x in R.glob(pat) if x.is_file()]
reg=R/'project_coordination/ARTIFACT_REGISTRY.csv'
with reg.open(encoding='utf-8-sig',newline='') as f:rr=csv.DictReader(f);fields=rr.fieldnames;known={row.get('canonical_path') for row in rr}
with reg.open('a',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields)
    for idx,path in enumerate(files):
        if path not in known:w.writerow({k:{'artifact_id':'F1851_%03d'%idx,'canonical_path':path,'stage':'Method-A','type':'diagnostic_evidence','status':'pending_review','notes':'Existing native donors only; no new PBS, no frozen-source edits'}.get(k,'') for k in fields})
ledger=R/'project_coordination/TASK_LEDGER.csv'
with ledger.open(encoding='utf-8-sig',newline='') as f:fields=next(csv.reader(f))
with ledger.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:{'task_id':'F1851-NATIVE-DIAGNOSTICS','agent':'codex','status':'COMPLETED_PENDING_REVIEW','title':'Native diagnostics: exact mapping, absent EVOL, incomplete sources','summary':'4 tests PASS, zero PBS, source termination corrected'}.get(k,'') for k in fields})
files+=['project_coordination/ACTIVE_SESSION.json','project_coordination/ACTIVE_TASK.json','project_coordination/CURRENT_STATE.md','project_coordination/ARTIFACT_REGISTRY.csv','project_coordination/TASK_LEDGER.csv']
subprocess.run(['git','add','--']+sorted(set(files)),cwd=R,check=True)
assert set(subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R,text=True).splitlines())<=set(files)
subprocess.run(['git','commit','-m','F1851: diagnose native field fidelity, missing volume and incomplete donors'],cwd=R,check=True)
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();subprocess.run(['git','push','origin','main'],cwd=R,check=True)
for im in s['images']:im.update(commit=commit,url='https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/'+commit+'/'+im['path'])
(R/'results/validation/f1851_image_manifest.json').write_text(json.dumps({'artifact_commit':commit,'images':s['images']},indent=2)+'\n')
print(commit)
