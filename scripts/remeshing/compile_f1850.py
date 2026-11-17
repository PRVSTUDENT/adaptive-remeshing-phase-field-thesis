"""Publish exact donor fields and measured four-case reconstruction results."""
from pathlib import Path
import json,hashlib,sys,csv,io,datetime
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.remeshing.compile_f1849 import plot
import matplotlib.pyplot as plt
B=ROOT/'models/pandey_kumar_mode1/280_f1850_donor_recovery'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=ROOT/'scripts/remeshing/generalized_2d_adaptive_framework_damage_envelope_f1849.py'
d={'task_id':'F1850-DONOR-RECOVERY','master_goal_status':'OPEN','new_pbs':0,'source_sha256':sha(source),'cases':[],'images':[]}
for cid,target in zip((1,2,3,5),(20232,17280,9975,15330)):
    snap=B/('case%d_donor.json'%cid);s=json.loads(snap.read_text())
    # Verify canonical snapshot hash under the exporter-compatible Python 3 runtime.
    assert hashlib.sha256(json.dumps(s['mesh_fields'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==s['mesh_fields_sha256']
    if s['source_odb_path'].startswith(str(ROOT)):
        s['source_odb_path']=Path(s['source_odb_path']).relative_to(ROOT).as_posix()
        snap.write_text(json.dumps(s,sort_keys=True,separators=(',',':')))
    a=json.loads((B/('case%d'%cid)/'audit.json').read_text());a['mesh_sha256']=sha(ROOT/a['physical_mesh'])
    c={'case_id':cid,'status':'GENERATED_COMPARISON_NOT_ACCEPTED','target_F1779':target,'audit':a,'snapshot':snap.relative_to(ROOT).as_posix(),'snapshot_sha256':sha(snap),'source_odb_path':s['source_odb_path'],'source_odb_sha256':s['source_odb_sha256'],'source_mode':s['mode'],'source_frame_id':s['source_frame_id'],'source_frame_time':s['source_frame_time'],'sampled_frames':s['sampled_frames'],'source_description':s['source_description']}
    d['cases'].append(c)
    fig,ax=plt.subplots(figsize=(7,8));plot(ax,c);fig.tight_layout()
    for ext in ('png','pdf'):
        p=ROOT/('results/figures/fig_f1850_case_%d_mesh.%s'%(cid,ext));fig.savefig(p,dpi=220);d['images'].append({'case_id':cid,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'mesh_sha256':a['mesh_sha256'],'source_sha256':sha(source)})
    plt.close(fig)
fig,axs=plt.subplots(2,2,figsize=(14,14),layout='constrained')
for ax,c in zip(axs.flat,d['cases']):plot(ax,c)
fig.suptitle('F1850: four fresh remeshes from recovered donor snapshots\nConstructed damage sizing; failures retained; no native-method qualification')
for ext in ('png','pdf'):
    p=ROOT/('results/figures/fig_f1850_four_case_composite.'+ext);fig.savefig(p,dpi=220);d['images'].append({'case_id':'composite','path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'source_sha256':sha(source)})
plt.close(fig)
(ROOT/'results/validation/f1850_donor_recovery_summary.json').write_text(json.dumps(d,indent=2)+'\n')
rows=['# F1850 existing-donor recovery and reconstruction','',
'Master OPEN. Zero new PBS; cumulative 36 unchanged. F1849 candidate source remains unchanged. Existing source ODBs opened read-only; no donor solve. This is offline CONSTRUCTED_DAMAGE_ENVELOPE comparison, not native MISESERI or causal prediction.',
'','|Case|F1779 count|Fresh count|Quads %|min detJ|max AR|far/core|','|---|---:|---:|---:|---:|---:|---:|']
for c in d['cases']:
    a=c['audit'];rows.append('|%d|%d|%d|%.2f|%.4g|%.3f|%.3f|'%(c['case_id'],c['target_F1779'],a['total_elements'],a['quad_fraction_pct'],a['min_det_j'],a['max_aspect_ratio'],a['refinement_ratio_far_to_core']))
rows+=['','Case2 and Case5 reproduce F1849 counts exactly (17,280 and 4,375). Case1 is 20,193 versus 20,232 (-0.19%); no exact reproduction claimed. Case3 is 45,009 versus 9,975 (+351.22%). A uniform damage strategy is therefore not qualified as reproducing F1779 across four benchmarks. Case3 F1779 used selected stress-recovery states, and Case5 used native stress-error fields, so their original counts are not damage-framework controls.',
'','## Accessible donor evidence',
'Four compact JSON snapshots contain every selected element connectivity, node coordinate, and MISESERI/MISESAVG/EVOL value used for remeshing, plus original ODB hash, size, step and frame metadata. Local reconstruction read-back confirmed exact scalar field equality before remeshing. These are lossless sizing-input snapshots, not complete ODB/physics histories. The repository forbids committing binary ODBs, so text snapshots provide a reviewable alternative to the requested reduced binary ODB. Reviewer must decide whether this evidence is sufficient.',
'Case1 reuses an existing envelope; Case2 reuses calibrated envelope v2. Their construction history is not newly reconstructed. Case3 is constructed from genuine existing Step-2 SDV1, every fifth frame plus final, with frozen damage thresholds. Case5 snapshot preserves the F1849 constructed envelope. All source hashes and sampled frames are in the summary and snapshots.',
'','## Preserved implementation failures',
'Initial export failed on numpy.float32 JSON coordinates; fixed by explicit float conversion before writing. Remote wrapper timed out after 60 s, but exact-target inspection proved both exports completed; no duplicate export or solver submission. First CAE reconstruction failed because 2D nodes need two coordinates; corrected. Python2/3 JSON float serialization hashes differ, so canonical text hashes are validated under Python3 and actual scalar values separately round-trip under CAE. Explicit constructed-driver flag restored. Failed incomplete ODB retained locally and excluded from Git.',
'','## Limitations',
'Element counts, geometric validity and visual localization do not establish fracture accuracy. No new fracture solves were run. Critical-region masks are inherited audits and are not future crack instructions. No parameter tuning or framework change was performed to hide negative cases. More complete per-donor provenance and generic performance remain subject to independent review.']
(ROOT/'docs/validation/F1850_DONOR_RECOVERY_REPORT.md').write_text('\n'.join(rows)+'\n')
print([(c['case_id'],c['audit']['total_elements']) for c in d['cases']])
