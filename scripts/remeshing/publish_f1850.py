from pathlib import Path
import json,subprocess,csv,io,datetime
R=Path(__file__).resolve().parents[2]
d=json.loads((R/'results/validation/f1850_donor_recovery_summary.json').read_text())
files=[]
for pat in ['scripts/remeshing/*f1850*','tests/unit/test_f1850*','models/pandey_kumar_mode1/280_f1850_donor_recovery/**/*.json','models/pandey_kumar_mode1/280_f1850_donor_recovery/**/*.inp','results/figures/fig_f1850*','results/validation/f1850*','docs/validation/F1850*','project_coordination/sessions/*f1850*']:
    files += [p.relative_to(R).as_posix() for p in R.glob(pat) if p.is_file()]
now=datetime.datetime.now().astimezone().isoformat()
p=R/'project_coordination/CURRENT_STATE.md';p.write_text('## F1850 numerical result '+now+'\n\nF1849 delayed matching review validated: INSUFFICIENT_EVIDENCE, prior transport block RESOLVED. Codex recovered exact existing HPC donors. Four fresh F1849-source remeshes from lossless field snapshots: C1 20193, C2 17280, C3 45009, C5 4375. Eight tests PASS. C3/C5 historical performance not reproduced; master OPEN, zero new PBS. Independent review pending.\n\n'+p.read_text(encoding='utf-8-sig'),encoding='utf-8')
with (R/'project_coordination/sessions/2026-11-17_codex_f1850_donor_recovery.md').open('a') as f:f.write('\nRecovered donors, exact scalar read-back and four fresh meshes completed. C1=20193, C2=17280, C3=45009, C5=4375; 8 tests PASS. Inspected composite: C3 diffuse fine background, C5 insufficient selective band. No adoption or master success; review pending. Zero PBS.\n')
reg=R/'project_coordination/ARTIFACT_REGISTRY.csv'
with reg.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;known={r.get('canonical_path') for r in reader}
with reg.open('a',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fields)
    for i,path in enumerate(files):
        if path not in known:
            row={k:'' for k in fields};row.update({k:v for k,v in {'artifact_id':'F1850_%03d'%i,'canonical_path':path,'stage':'Method-A','type':'scientific_evidence','status':'comparison_not_accepted','notes':'Four existing donor snapshots; failures retained; zero PBS'}.items() if k in fields});w.writerow(row)
ledger=R/'project_coordination/TASK_LEDGER.csv'
with ledger.open(encoding='utf-8-sig',newline='') as f:fields=next(csv.reader(f))
with ledger.open('a',newline='',encoding='utf-8') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:({'task_id':'F1850-DONOR-RECOVERY','agent':'codex','status':'PENDING_REVIEW','summary':'C1 20193 C2 17280 C3 45009 C5 4375; exact field reconstruction; 8 tests; 0 PBS'}.get(k,'')) for k in fields})
files+=['project_coordination/ACTIVE_SESSION.json','project_coordination/ACTIVE_TASK.json','project_coordination/CURRENT_STATE.md','project_coordination/ARTIFACT_REGISTRY.csv','project_coordination/TASK_LEDGER.csv','.agents/scripts/reconcile_f1849_response.ps1','.agents/bridge_history/f1849_damage_envelope_validated_response.json']
subprocess.run(['git','add','--']+sorted(set(files)),cwd=R,check=True)
staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R,text=True).splitlines();assert not set(staged)-set(files)
subprocess.run(['git','commit','-m','F1850: recover exact donors and measure four-case damage-only reconstruction'],cwd=R,check=True)
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
subprocess.run(['git','push','origin','main'],cwd=R,check=True)
for im in d['images']:im.update(commit=commit,url='https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/'+commit+'/'+im['path'])
(R/'results/validation/f1850_image_manifest.json').write_text(json.dumps({'artifact_commit':commit,'images':d['images']},indent=2)+'\n')
print(commit)
