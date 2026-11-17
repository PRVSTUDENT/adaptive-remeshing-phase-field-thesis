"""Record essential coordination and register only this task's artifacts."""
from pathlib import Path
import csv,json,datetime,hashlib
ROOT=Path(__file__).resolve().parents[2]
now=datetime.datetime.now().astimezone().isoformat()
summary=json.loads((ROOT/'results/validation/f1849_damage_envelope_summary.json').read_text())
report=ROOT/'docs/validation/F1849_DAMAGE_ENVELOPE_FRAMEWORK_REPORT.md'
with report.open('a',encoding='utf-8') as f:
    f.write('\n## Offline checks\n\nFive meaningful tests passed: monotone/length-scaled sizing; explicit constructed-only driver; audit-region isolation from remeshing; generic-domain configuration; artifact hash/count integrity and explicit missing-case handling. Command: `py -3 -B -m pytest -q -p no:cacheprovider tests/unit/test_f1849_damage_envelope.py`.\n')
files=[ROOT/summary['source']['path'], report, ROOT/'results/validation/f1849_damage_envelope_summary.json']
files += [ROOT/i['path'] for i in summary['images']]
files += [ROOT/c['audit']['physical_mesh'] for c in summary['cases'] if 'audit' in c]
reg=ROOT/'project_coordination/ARTIFACT_REGISTRY.csv'
with reg.open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f);fields=reader.fieldnames;existing=list(reader)
known={x.get('path','') for x in existing}
with reg.open('a',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields)
    for p in files:
        rel=p.relative_to(ROOT).as_posix()
        # Registry schemas in historical rows vary; populate the canonical header.
        row={k:'' for k in fields}
        for k in fields:
            key=k.lower()
            if key in ('artifact_id','id'):row[k]='F1849_'+p.stem.upper()
            elif key in ('path','repo_path','artifact_path','canonical_path'):row[k]=rel
            elif key in ('sha256','hash','artifact_sha256'):row[k]=hashlib.sha256(p.read_bytes()).hexdigest()
            elif key in ('agent','owner','created_by'):row[k]='codex'
            elif key in ('method','lane'):row[k]='Method-A'
            elif key in ('status','classification'):row[k]='partial_comparison'
            elif key in ('description','notes'):row[k]='F1849 constructed damage comparison; cases 1/3 blocked; no native qualification'
        if rel not in known:writer.writerow(row)
session=ROOT/'project_coordination/sessions/2026-11-17_codex_f1849_damage_envelope.md'
with session.open('a',encoding='utf-8') as f:
    f.write('\nNumerical result: Case 2 regenerated 17,280 elements, Gate06 2.205x; Case5 constructed damage comparison 4,375 elements, Gate06 1.338x FAIL. Cases1/3 missing Job1/envelope donors. Five offline tests PASS. No PBS submissions. Frozen frameworks preserved. New framework '+summary['source']['sha256']+'.\n')
active=ROOT/'project_coordination/ACTIVE_TASK.json';d=json.loads(active.read_text())
d.update(task_status='PARTIAL_PENDING_REVIEW',status='PARTIAL_PENDING_REVIEW',review_verdict='PENDING',notes='Codex takeover authorized in chat. Fresh Case2=17280; Case5=4375 (not reproduction). Cases1/3 missing required local Job1/envelope donors. Five offline tests passed; 0 new PBS. Independent review pending; master OPEN.')
active.write_text(json.dumps(d,indent=2)+'\n')
state=ROOT/'project_coordination/CURRENT_STATE.md'
state.write_text('## F1849 Codex partial comparison — '+now+'\n\nConstructed damage-envelope framework: Case 2 regenerated 17,280 elements; Case 5 produced 4,375 (not F1779 reproduction, Gate06 FAIL). Cases1/3 blocked on missing local Job1/envelope ODBs. Five offline tests PASS; zero PBS. Pending guarded independent review; master OPEN. Prior task preserved below.\n\n'+state.read_text(encoding='utf-8-sig'),encoding='utf-8')
ledger=ROOT/'project_coordination/TASK_LEDGER.csv'
with ledger.open(encoding='utf-8-sig',newline='') as f:fields=next(csv.reader(f))
row={k:'' for k in fields}
for k in fields:
    key=k.lower()
    if key=='task_id':row[k]='F1849-DAMAGE-ENVELOPE-FRAMEWORK'
    elif key in ('agent','owner','assigned_agent'):row[k]='codex'
    elif key in ('status','task_status'):row[k]='partial_pending_review'
    elif key in ('description','title','summary'):row[k]='Constructed damage comparison: C2 17280; C5 4375 FAIL; C1/C3 missing donors; 5 tests PASS; 0 new PBS'
    elif 'correlation' in key:row[k]='HND-F1849-DAMAGE-ENVELOPE-FRAMEWORK-001'
    elif key in ('report_path','checkpoint_artifact','report'):row[k]='docs/validation/F1849_DAMAGE_ENVELOPE_FRAMEWORK_REPORT.md'
with ledger.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow(row)
print('Recorded partial scientific result and preserved failures.')
