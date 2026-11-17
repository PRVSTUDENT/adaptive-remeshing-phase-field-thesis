"""Topology/volume fidelity, field localization and unbiased area coverage."""
from pathlib import Path
import json,hashlib,math,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from scripts.remeshing.reusable_2d_adaptive_framework import MeshQualityAuditEngine,AdaptiveConfig,get_geometry_adapter
B=R/'models/pandey_kumar_mode1/281_f1851_native_diagnostics'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((B/n).read_text())
def area(pts):return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1])))/2
def aggregate(d,name):
    vals={}
    for v in d['fields'].get(name,[]):vals.setdefault(v['element'],[]).append(v['mises'] if name=='S' else v['data'])
    return {k:float(np.mean(v)) for k,v in vals.items()}
def topology(d):
    i=list(d['instances'].values())[0];return {n[0]:n[1:] for n in i['nodes']},{e[0]:e[2] for e in i['elements']}
def corridor2(x,y):return (.50<=x<=.65 and .45<=y<=.70) or (.65<=x<=1 and .55<=y<=.75)
cfg4=AdaptiveConfig.from_json(str(R/'configs/remeshing/f1728_case4_five_hole.json'));adapter4=get_geometry_adapter(cfg4)
def mask(cid,x,y):return corridor2(x,y) if cid==2 else adapter4.classify_region(x,y)!='FAR_FIELD'
summary={'task_id':'F1851-NATIVE-DIAGNOSTICS','master_goal_status':'OPEN','new_pbs':0,'cumulative_pbs':36,'mapping':[],'field_statistics':[],'coverage':{},'images':[],'inventory':[],'comparisons':{}}
for idx in (300,337):
    s=load('case2_original%d.json'%idx);t=load('case2_extracted%d.json'%idx);sn,se=topology(s);tn,te=topology(t);offset=min(aggregate(s,'MISESERI'))-1
    row={'frame':idx,'offset':offset,'node_labels_equal':set(sn)==set(tn),'maximum_coordinate_difference':max(abs(a-b) for n in tn for a,b in zip(sn[n],tn[n])),'connectivity_mismatches':sum(se[e+offset]!=v for e,v in te.items()),'source_EVOL_present':'EVOL' in s['fields'],'source_thickness_mm':1.0,'extracted_thickness_assessment':'EVOL/geometric area; source section thickness=1.0','scalar_differences':{}}
    for name in ('MISESERI','MISESAVG','SDV1'):
        sv=aggregate(s,name);tv=aggregate(t,name);row['scalar_differences'][name]=max(abs(v-sv[e+offset]) for e,v in tv.items())
    ev=aggregate(t,'EVOL');ratios=[ev[e]/area([tn[n] for n in te[e]]) for e in ev];row['EVOL_to_area_ratio_range']=[min(ratios),max(ratios)]
    row['source_ip_counts']=sorted(set(sum(1 for v in s['fields']['S'] if v['element']==e) for e in aggregate(s,'S')))
    row['extracted_damage_position']=t['fields']['SDV1'][0]['position'];summary['mapping'].append(row)
for filename,cid in [('case2_original300.json',2),('case2_original337.json',2),('f1720_step1_12.json',4),('f1720_step2_178.json',4)]:
    d=load(filename);nodes,elems=topology(d);eri=aggregate(d,'MISESERI');labels=sorted(eri);polys=[[nodes[n][:2] for n in elems[e]] for e in labels];ar=np.array([area(p) for p in polys]);cent=np.array([np.mean(p,axis=0) for p in polys]);inside=np.array([mask(cid,*c) for c in cent]);fields={n:aggregate(d,n) for n in ('SDV1','S','MISESERI','MISESAVG')};damage=np.array([fields['SDV1'].get(e,0.) for e in labels]);er=np.array([eri[e] for e in labels]);avg=np.array([fields['MISESAVG'][e] for e in labels])
    stat={'snapshot':filename,'case':cid,'frame':d['frame_index'],'time':d['time'],'total_area':float(ar.sum()),'mask':'F1840 union of notch-to-hole and distal windows' if cid==2 else 'Frozen FiveHolePlateAdapter three-l0 inter-hole segments; audit only','outside_area_pct':float(100*ar[~inside].sum()/ar.sum()),'outside_squared_error_area_proxy_pct':float(100*(er[~inside]**2*ar[~inside]).sum()/(er**2*ar).sum()),'outside_absolute_error_area_pct':float(100*(er[~inside]*ar[~inside]).sum()/(er*ar).sum()),'damage_max':float(damage.max()),'missing_stress_elements':len(labels)-len(fields['S']),'missing_damage_elements':len(labels)-len(fields['SDV1']),'zero_MISESAVG_elements':int(np.count_nonzero(avg==0)),'ERI_native_max':float(er.max()),'AVG_native_max':float(avg.max())}
    for cutoff in (.1,.5):
        active=damage>=cutoff;stat['damage_ge_%s_area_pct'%cutoff]=float(100*ar[active].sum()/ar.sum());stat['error_proxy_in_damage_ge_%s_pct'%cutoff]=float(100*(er[active]**2*ar[active]).sum()/(er**2*ar).sum())
    stat['maximum_IP_damage']=max(v['data'] for v in d['fields']['SDV1'])
    raw_elements=list(d['instances'].values())[0]['elements'];types={e[0]:e[1] for e in raw_elements};bytype={}
    for typ in sorted({types[e] for e in labels}):
        sel=np.array([types[e]==typ for e in labels]);g={n:np.array([f.get(e,np.nan) for e in labels]) for n,f in fields.items()}
        bytype[typ]={'elements':int(sel.sum()),'zero_stress':int(np.count_nonzero(sel & (g['S']==0))),'zero_base':int(np.count_nonzero(sel & (avg==0))),'error_proxy_share_pct':float(100*(er[sel]**2*ar[sel]).sum()/(er**2*ar).sum()),'outside_error_proxy_share_pct':float(100*(er[sel & ~inside]**2*ar[sel & ~inside]).sum()/(er[~inside]**2*ar[~inside]).sum())}
    stat['element_type_audit']=bytype
    if cid==4:
        ev=aggregate(d,'EVOL');ratios=np.array([ev[e]/a for e,a in zip(labels,ar)])
        stat['EVOL_to_area_ratio_range']=[float(ratios.min()),float(ratios.max())]
    summary['field_statistics'].append(stat)
    fig,axs=plt.subplots(1,4,figsize=(18,5),layout='constrained')
    for ax,name in zip(axs,('SDV1','S','MISESERI','MISESAVG')):
        f=fields[name];vals=np.array([f.get(e,np.nan) for e in labels]);scale=1 if name=='SDV1' else 1/(1e-11/210.)
        pc=PolyCollection(polys,array=vals*scale,cmap='viridis',edgecolors='none');ax.add_collection(pc);ax.autoscale();ax.set_aspect('equal');ax.set_title(name+(' (physical kN/mm²)' if name=='S' else ' (native / dummy scale)' if name!='SDV1' else ''));ax.set_xlabel('x [mm]');fig.colorbar(pc,ax=ax,shrink=.7)
    fig.suptitle('%s | original coarse mesh | %s frame %d, t=%.6f\nNative fields: display scaling only, no remesh transformation'%(filename,d['step'],d['frame_index'],d['time']))
    for ext in ('png','pdf'):
        p=R/('results/figures/fig_f1851_'+Path(filename).stem+'_fields.'+ext);fig.savefig(p,dpi=200);summary['images'].append({'case_id':cid,'path':p.relative_to(R).as_posix(),'sha256':sha(p),'source_odb_sha256':d['sha256']})
    plt.close(fig)
    source='/scratch9/pr21vyci/runs/f1838_case2_native_pilot/PK_HOLE_COARSE_F1838_PILOT.odb' if cid==2 else d['source']
    summary['inventory'].append({'snapshot':(B/filename).relative_to(R).as_posix(),'source':source,'bytes':d['bytes'],'sha256':d['sha256'],'step':d['step'],'frame_index':d['frame_index'],'time':d['time'],'step_frame_count':d['step_frame_count']})
def coverage(path,l0,cid):
    nodes,q,t=MeshQualityAuditEngine.parse_physical_inp(str(path));regions={k:[] for k in ('global','corridor','outside_corridor','distal_report','distal_F1812')}
    for conn in list(q.values())+list(t.values()):
        p=[nodes[n] for n in conn];a=area(p);x,y=np.mean(p,axis=0);inside=mask(cid,x,y);regions['global'].append(a);regions['corridor' if inside else 'outside_corridor'].append(a)
        if cid==2:
            if .65<=x<=1 and .55<=y<=.75:regions['distal_report'].append(a)
            if .55<=x<=1 and .55<=y<=.75:regions['distal_F1812'].append(a)
    out={}
    for name,vals in regions.items():
        if not vals:continue
        a=np.array(vals);out[name]={'count':len(a),'area':float(a.sum())}
        for label,h in [('l0',l0),('half_l0',l0/2)]:
            fine=a<=h*h;out[name]['count_pct_'+label]=float(100*np.mean(fine));out[name]['area_pct_'+label]=float(100*a[fine].sum()/a.sum());out[name]['fine_area_'+label]=float(a[fine].sum())
    out['outside_share_of_fine_area_l0_pct']=100*out['outside_corridor']['fine_area_l0']/out['global']['fine_area_l0'];return out
for tag,path in [('F1838','277_f1838_case2_native_pilot/PK_F1838_CASE_2_PILOT_PHYS.inp'),('F1840','278_f1840_final_frame_comparison/PK_F1840_CASE_2_FINAL_FRAME_PHYS.inp')]:summary['coverage'][tag]=coverage(R/'models/pandey_kumar_mode1'/path,.0075,2)
for p in B.glob('*/receipt.json'):
    v=json.loads(p.read_text());summary['comparisons'][p.parent.name]=v
    if p.parent.name.startswith('f1720') and v.get('status')=='GENERATED':summary['coverage'][p.parent.name]=coverage(R/v['inp'],.008,4)
summary['comparisons']['case2_original337']=load('original337_direct_receipt.json')
for idx in (300,337):
    p=B/('case2_extracted%d.json'%idx);d=load(p.name);summary['inventory'].append({'snapshot':p.relative_to(R).as_posix(),'source':d['source'],'bytes':d['bytes'],'sha256':d['sha256'],'step':d['step'],'frame_index':d['frame_index']})
(R/'results/validation/f1851_diagnostics_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'mapping':summary['mapping'],'fields':summary['field_statistics'],'coverage':summary['coverage']},indent=2))
