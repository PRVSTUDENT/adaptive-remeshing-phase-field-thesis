"""Selectively commit this task's nonbulky evidence and record pinned image URLs."""
from pathlib import Path
import subprocess,json,csv,io,hashlib
ROOT=Path(__file__).resolve().parents[2]
d=json.loads((ROOT/'results/validation/f1849_damage_envelope_summary.json').read_text())
files=[ROOT/d['source']['path'],ROOT/'docs/validation/F1849_DAMAGE_ENVELOPE_FRAMEWORK_REPORT.md',ROOT/'results/validation/f1849_damage_envelope_summary.json']+[ROOT/i['path'] for i in d['images']]+[ROOT/c['audit']['physical_mesh'] for c in d['cases'] if 'audit' in c]
reg=ROOT/'project_coordination/ARTIFACT_REGISTRY.csv'
lines=reg.read_text(encoding='utf-8-sig').splitlines(keepends=True)
fields=next(csv.reader([lines[0]]));own=iter(files);out=[]
for line in lines:
    if line.startswith('F1849_'):
        row=next(csv.reader([line]));p=next(own)
        row[fields.index('canonical_path')]=p.relative_to(ROOT).as_posix()
        row[fields.index('stage')]='Method-A'
        row[fields.index('type')]='scientific_evidence'
        stream=io.StringIO(newline='');csv.writer(stream).writerow(row);out.append(stream.getvalue())
    else:out.append(line)
reg.write_text(''.join(out),encoding='utf-8',newline='')
allowed=[]
for pat in ['scripts/remeshing/*f1849*','tests/unit/test_f1849*','results/figures/fig_f1849*','results/validation/f1849*','docs/validation/F1849_DAMAGE_ENVELOPE_FRAMEWORK_REPORT.md','models/pandey_kumar_mode1/279_f1849_damage_envelope/**/*.json','models/pandey_kumar_mode1/279_f1849_damage_envelope/**/*.inp','project_coordination/sessions/2026-11-17_codex_f1849_damage_envelope.md']:
    allowed.extend(p.relative_to(ROOT).as_posix() for p in ROOT.glob(pat) if p.is_file())
allowed += ['project_coordination/ACTIVE_SESSION.json','project_coordination/ACTIVE_TASK.json','project_coordination/ARTIFACT_REGISTRY.csv','project_coordination/TASK_LEDGER.csv','project_coordination/CURRENT_STATE.md']
subprocess.run(['git','add','--']+sorted(set(allowed)),cwd=ROOT,check=True)
staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines()
unexpected=set(staged)-set(allowed)
if unexpected:raise RuntimeError('Unrelated staged paths preserved; cannot commit: '+str(unexpected))
subprocess.run(['git','commit','-m','F1849: qualify constructed-only damage framework and preserve partial regression failures'],cwd=ROOT,check=True)
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
for im in d['images']:im['commit']=commit;im['url']='https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/'+commit+'/'+im['path']
p=ROOT/'results/validation/f1849_image_manifest.json';p.write_text(json.dumps({'artifact_commit':commit,'images':d['images']},indent=2)+'\n')
subprocess.run(['git','push','origin','main'],cwd=ROOT,check=True)
print('Pushed artifact checkpoint',commit)
