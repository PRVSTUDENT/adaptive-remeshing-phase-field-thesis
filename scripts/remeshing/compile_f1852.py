from pathlib import Path
import json,hashlib,sys,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from scripts.remeshing.generalized_2d_adaptive_framework_damage_envelope_f1849 import MeshQualityAuditEngine,AdaptiveConfig,get_geometry_adapter
B=R/'models/pandey_kumar_mode1/282_f1852_driver_selection';source=R/'scripts/remeshing/generalized_2d_adaptive_framework_driver_selection_f1852.py';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def body(p):return hashlib.sha256(''.join(x.strip()+'\n' for x in p.read_text().splitlines() if not x.strip().startswith('**')).encode()).hexdigest()
def metrics(p,cfg):
    ns,q,t=MeshQualityAuditEngine.parse_physical_inp(str(p));adapter=get_geometry_adapter(cfg);data=[]
    for co in list(q.values())+list(t.values()):
        pts=[ns[n] for n in co];a=abs(sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(pts,pts[1:]+pts[:1])))/2;x,y=np.mean(pts,axis=0);data.append((a,adapter.classify_region(x,y)!='FAR_FIELD'))
    out={}
    for region in ('global','process','far_field'):
        ar=np.array([a for a,proc in data if region=='global' or (proc if region=='process' else not proc)])
        if not len(ar):continue
        m={'count':len(ar),'area_mm2':float(ar.sum())}
        for name,h in [('l0',cfg.l0),('half_l0',cfg.l0/2)]:
            sel=ar<=h*h;m['count_pct_'+name]=float(100*np.mean(sel));m['area_pct_'+name]=float(100*ar[sel].sum()/ar.sum())
        out[region]=m
    return out
def plot(ax,c):
    a=c['audit'];ns,q,t=MeshQualityAuditEngine.parse_physical_inp(str(R/a['physical_mesh']));polys=[[ns[n] for n in co] for co in list(q.values())+list(t.values())];ax.add_collection(PolyCollection(polys,facecolors='white',edgecolors='#233044',linewidths=.13));ax.autoscale();ax.set_aspect('equal');ax.set_xlabel('x [mm]');ax.set_ylabel('y [mm]')
    ax.set_title('Case %d: %s elements | %.2f%% quads\n%s | Gate06 %.3fx %s'%(a['case_id'],format(a['total_elements'],','),a['quad_fraction_pct'],'DAMAGE ENVELOPE' if a['driver'].startswith('CONSTRUCTED') else 'NATIVE MISESERI FALLBACK',a['refinement_ratio_far_to_core'],'PASS' if a['refinement_ratio_far_to_core']>=2 else 'FAIL'),fontsize=11)
s={'task_id':'F1852-DRIVER-SELECTION','source':source.relative_to(R).as_posix(),'source_sha256':sha(source),'cases':[],'images':[],'new_pbs':0,'cumulative_pbs':36,'master_goal_status':'OPEN','native_gate':json.loads((B/'case5_native_gate.json').read_text()),'frozen_sources':{}}
for rel in ['scripts/remeshing/generalized_2d_adaptive_framework_damage_envelope_f1849.py','scripts/remeshing/generalized_2d_adaptive_framework_f1846.py','scripts/remeshing/reusable_2d_adaptive_framework.py','models/pandey_kumar_mode1/f42_mixed_uel.for']:s['frozen_sources'][rel]=sha(R/rel)
for cid,historical in zip((1,2,3,5),(20232,23965,28933,15330)):
    a=json.loads((B/('case%d'%cid)/'audit.json').read_text());assert a['framework_sha256']==s['source_sha256'];cfg=AdaptiveConfig.from_json(str(R/('models/pandey_kumar_mode1/279_f1849_damage_envelope/case%d_config.json'%cid)));prev=json.loads((R/('models/pandey_kumar_mode1/280_f1850_donor_recovery/case%d/audit.json'%cid)).read_text());old=R/prev['physical_mesh'];new=R/a['physical_mesh']
    c={'case_id':cid,'audit':a,'coverage':metrics(new,cfg),'previous_F1850':{'count':prev['total_elements'],'body_sha256':body(old),'coverage':metrics(old,cfg),'Gate06':prev['refinement_ratio_far_to_core']},'body_identical_F1850':body(old)==a['body_sha256'],'delta_count_F1850_pct':100*(a['total_elements']/prev['total_elements']-1),'F1774_reported_count':historical,'F1774_local_mesh_available':False,'historical_baseline_caveat':'F1774 published counts are historical report values, not fresh same-revision numerical evidence; baseline local meshes missing.'}
    if cid!=1:
        bp=R/('models/pandey_kumar_mode1/240_f1774_suite_regression/case%d/PK_F1728_CASE_%d_ADAPT_PHYS.inp'%(cid,cid));c['F1774_local_mesh_available']=bp.exists()
        if bp.exists():c['F1774_fresh_coverage']=metrics(bp,cfg)
    s['cases'].append(c)
    fig,ax=plt.subplots(figsize=(7,8));plot(ax,c);fig.tight_layout()
    for ext in ('png','pdf'):
        p=R/('results/figures/fig_f1852_case_%d_mesh.%s'%(cid,ext));fig.savefig(p,dpi=240);s['images'].append({'case_id':cid,'path':p.relative_to(R).as_posix(),'sha256':sha(p),'mesh_sha256':a['mesh_sha256'],'source_sha256':s['source_sha256']})
    plt.close(fig)
fig,axs=plt.subplots(2,2,figsize=(14,14),layout='constrained')
for ax,c in zip(axs.flat,s['cases']):plot(ax,c)
fig.suptitle('F1852: measured damage strength selects the shared sizing driver\nSame frozen revision; native fallback only below d_core=0.5; failures retained')
for ext in ('png','pdf'):
    p=R/('results/figures/fig_f1852_four_case_composite.'+ext);fig.savefig(p,dpi=240);s['images'].append({'case_id':'composite','path':p.relative_to(R).as_posix(),'sha256':sha(p),'source_sha256':s['source_sha256']})
plt.close(fig)
(R/'results/validation/f1852_driver_selection_summary.json').write_text(json.dumps(s,indent=2)+'\n')
lines=['# F1852 measured driver selection','', 'User directly requested the next operation in the pasted F1851 review. This is not a repair or fabrication of the unresolved F1850 transport provenance. Master OPEN; 0 new PBS, cumulative36. No new fracture solve, donor substitution, target tuning or frozen framework/UEL edit.',
'','## Numerical result','', '|Case|max damage|Core element fraction %|Selected driver|F1850 count|Fresh count|Body identical?|Gate06|','|---|---:|---:|---|---:|---:|---|---:|']
for c in s['cases']:
    a=c['audit'];d=a['damage_strength'];lines.append('|%d|%.6f|%.3f|%s|%d|%d|%s|%.3f %s|'%(c['case_id'],d['max_damage'],100*d['fraction_ge_core'],a['driver'],c['previous_F1850']['count'],a['total_elements'],c['body_identical_F1850'],a['refinement_ratio_far_to_core'],'PASS' if a['refinement_ratio_far_to_core']>=2 else 'FAIL'))
lines+=['','Cases1/2/3 are body-identical to F1850, preserving all their successes and failures, including Case3 diffuse refinement at45,009 elements. Case5 rises from4,375 to15,411, with selective inter-hole refinement. Gate06 improves from1.339 to1.939 but remains FAIL (<2.0). This is not four-case framework finalization or native method qualification. Native mesh count is not tuned to the historical15,330 target.',
'','## Selection and implementation',
'New separately versioned source composes immutable F1849 damage and F1846 native engines. No case IDs or coordinates occur in selection. Max donor SDV1 >=0.5 selects the unchanged damage envelope; below0.5 selects raw native fields only after the native gate passes. Core fraction is measured and recorded, not a second fitted cutoff. All native fallback input is from one last available frame, with no temporal maximum of stress errors, local error/stress division or synthetic relabeling.',
'Damage strength was measured from every available SDV1 frame in the exact existing source donor; frozen envelope meshes remain the F1850 inputs for strong signals. This is an offline full-history comparison, not proof of causal online prediction. Later held-out accuracy evaluation is not available here. Case1 measured overshoot1.0022 is retained; no clipping or threshold tuning was introduced. Native field inspection does not prove mechanical correctness or solve completion.',
'','## Case5 native gate',
'Original source: `%s`, %d bytes, SHA256 `%s`.'%(s['native_gate']['source'],s['native_gate']['source_bytes'],s['native_gate']['source_sha256']),
'Step2 index171, frameId341, t=0.778866. Native MISESERI/MISESAVG/EVOL/S present. All2465 quads and101 triangles have stress and positive MISESAVG; zero triangle tensors/base counts are0. Triangle share of squared-error area proxy: total0.935%, inside1.444%, outside0.812%. The F1851 Case2 zero-stress triangle anomaly is absent in this donor. Audit regions use the frozen SevenHolePlateAdapter and never enter sizing.',
'','## Resolution and quality','', '|Case|Global h<=l0 count %|Global h<=l0 area %|Global h<=l0/2 count %|Global h<=l0/2 area %|Quads %|min detJ|max AR|Remesh seconds|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for c in s['cases']:
    a=c['audit'];v=c['coverage']['global'];lines.append('|%d|%.3f|%.3f|%.3f|%.3f|%.3f|%.4g|%.3f|%.3f|'%(c['case_id'],v['count_pct_l0'],v['area_pct_l0'],v['count_pct_half_l0'],v['area_pct_half_l0'],a['quad_fraction_pct'],a['min_det_j'],a['max_aspect_ratio'],a['remesh_seconds']))
lines+=['','Area computed from polygon shoelace geometry; h=sqrt(area). Process/far-field coverage and prior-candidate values are in the summary. Critical-region classification is audit-only. Body equality preserves the full previous spatial resolution on Cases1/2/3; no count-only proxy is used to assert preservation.',
'','## Historical baseline and provenance limits',
'F1774 reported counts:20,232 /23,965 /28,933 /15,330. Its original local baseline mesh artifacts are unavailable for fresh common-metric evaluation; historical report values are explicitly not mixed-revision fresh regression. F1850 comparison is measured directly from its frozen mesh inputs. Source/damage-history hashes, exact frames, active mesh hashes and current source revision are recorded in the audit JSONs.',
'','## Preserved implementation evidence',
'An initial overly strict max-damage<=1 guard rejected Case1\'s authentic overshoot. The guard was corrected to require nonnegative finite damage, preserving the scientific0.5 selection rule. Initial Case5 result and Case1 failed-attempt folder remain under precheck directories; ALL four final meshes were regenerated after the correction and share the final source hash. A120s guarded SSH observation timed out during damage extraction; ps verified the same remote extraction still live, then exact output existence was checked and transferred. No extraction restart or duplicate job was made.',
'','## Publication and review',
'Genuine standalone and2x2 composite PNG/PDF images were regenerated from all four final same-revision meshes. Pinned image hashes/URLs are in results/validation/f1852_image_manifest.json after publication. Frozen F1849/F1846/production/UEL hashes are retained. No native-method acceptance or Job2 authorization. The unresolved F1850 transport transaction remains untouched.']
(R/'docs/validation/F1852_DRIVER_SELECTION_REPORT.md').write_text('\n'.join(lines)+'\n')
print([(c['case_id'],c['audit']['driver'],c['audit']['total_elements'],c['body_identical_F1850']) for c in s['cases']])
