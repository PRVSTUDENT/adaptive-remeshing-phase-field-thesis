from pathlib import Path
import json,hashlib,subprocess,csv,datetime
R=Path(__file__).resolve().parents[2];B=R/'models/pandey_kumar_mode1/282_f1852_driver_selection';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();now=datetime.datetime.now().astimezone().isoformat()
p=R/'results/validation/f1852_driver_selection_summary.json';s=json.loads(p.read_text());s['tests']='4 passed: tests/unit/test_f1852_driver_selection.py'
for c in s['cases']:
    i=c['case_id'];paths=[R/('models/pandey_kumar_mode1/279_f1849_damage_envelope/case%d_config.json'%i),B/('case%d_damage_strength.json'%i),R/('models/pandey_kumar_mode1/280_f1850_donor_recovery/case%d_donor.json'%i)]
    active=R/('models/pandey_kumar_mode1/280_f1850_donor_recovery/case%d/PK_F1850_TEXT_DONOR.odb'%i) if i!=5 else R/s['native_gate']['source'];paths.append(active)
    c['input_hashes']={x.relative_to(R).as_posix():{'bytes':x.stat().st_size,'sha256':sha(x)} for x in paths};c['timing_scope']='native remeshing plus mesh quality audit; excludes hash and strength extraction'
p.write_text(json.dumps(s,indent=2)+'\n')
report=R/'docs/validation/F1852_DRIVER_SELECTION_REPORT.md'
with report.open('a',encoding='utf-8') as f:f.write('\nInput manifests record exact config, damage measurement, logical donor snapshot and active ODB bytes/SHA for every case. Solver binaries remain local/HPC and are excluded from Git.\n')
session=R/'project_coordination/sessions/2026-11-18_codex_f1852_driver_selection.md';session.write_text('# F1852 measured driver selection\n\nDirect user request from pasted F1851 review. Native gate passes on exact original Case5 donor;101 triangles have no zero stress/base anomaly. Signal maxd=.476<.5 triggers native single-frame fallback. New composing framework leaves frozen files unchanged. Four final fresh meshes: C1=20193, C2=17280, C3=45009, C5=15411; first3body hashes unchanged. C5process area coverage17%->92% at l0;Gate06stillFAIL1.939. Four testsPASS. ZeroPBS/cumulative36. All failures preserved; masterOPEN.\n')
task=R/'project_coordination/ACTIVE_TASK.json';t=json.loads(task.read_text());t.update(task_id='F1852-DRIVER-SELECTION',title='Measured damage strength and native fallback selection',status='COMPLETED_PENDING_REVIEW',task_status='COMPLETED_PENDING_REVIEW',review_verdict='PENDING',review_correlation_id='HND-F1852-DRIVER-SELECTION-001',checkpoint_artifact=report.relative_to(R).as_posix(),notes='Direct user request. C1/2/3body-identical. C5native15411 improves process-area coverage,Gate06FAILretained.4testsPASS.0PBS.');task.write_text(json.dumps(t,indent=2)+'\n')
state=R/'project_coordination/CURRENT_STATE.md';state.write_text('## F1852 numerical result '+now+'\n\nNew separately versioned measured driver rule: maxSDV1>=.5 damage, otherwise audited native. Cases1/2/3 damage outputs body-identical20193/17280/45009. Case5 native15411 vs4375, process area h<=l0 coverage16.99->92.15%,Gate061.338->1.939FAIL. Four focused testsPASS, frozen assets unchanged, zeroPBS. Genuine same-revision images ready for independent review; masterOPEN.\n\n'+state.read_text(encoding='utf-8-sig'),encoding='utf-8')
files=[]
for pat in ['scripts/remeshing/*f1852*','tests/unit/test_f1852*','models/pandey_kumar_mode1/282_f1852_driver_selection/**/*.json','models/pandey_kumar_mode1/282_f1852_driver_selection/**/*.inp','results/figures/fig_f1852*','results/validation/f1852*','docs/validation/F1852*','project_coordination/sessions/*f1852*']:
    files += [x.relative_to(R).as_posix() for x in R.glob(pat) if x.is_file()]
reg=R/'project_coordination/ARTIFACT_REGISTRY.csv'
with reg.open(encoding='utf-8-sig',newline='') as f:rr=csv.DictReader(f);fields=rr.fieldnames;known={x.get('canonical_path') for x in rr}
with reg.open('a',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields)
    for idx,path in enumerate(files):
        if path not in known:w.writerow({k:{'artifact_id':'F1852_%03d'%idx,'canonical_path':path,'stage':'Method-A','type':'scientific_evidence','status':'pending_review','notes':'Measured driver; all4fresh; failures retained;zeroPBS'}.get(k,'') for k in fields})
ledger=R/'project_coordination/TASK_LEDGER.csv'
with ledger.open(encoding='utf-8-sig',newline='') as f:fields=next(csv.reader(f))
with ledger.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:{'task_id':'F1852-DRIVER-SELECTION','agent':'codex','status':'COMPLETED_PENDING_REVIEW','title':'Measured driver selection; Case5improvement; strong cases identical'}.get(k,'') for k in fields})
files+=['project_coordination/ACTIVE_SESSION.json','project_coordination/ACTIVE_TASK.json','project_coordination/CURRENT_STATE.md','project_coordination/ARTIFACT_REGISTRY.csv','project_coordination/TASK_LEDGER.csv']
subprocess.run(['git','add','--']+sorted(set(files)),cwd=R,check=True);assert set(subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R,text=True).splitlines())<=set(files)
subprocess.run(['git','commit','-m','F1852: select measured damage or audited native driver across four cases'],cwd=R,check=True)
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();subprocess.run(['git','push','origin','main'],cwd=R,check=True)
for im in s['images']:im.update(commit=commit,url='https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/'+commit+'/'+im['path'])
(R/'results/validation/f1852_image_manifest.json').write_text(json.dumps({'artifact_commit':commit,'images':s['images']},indent=2)+'\n');print(commit)
