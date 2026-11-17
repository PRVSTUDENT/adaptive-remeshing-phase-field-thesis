from pathlib import Path
import sys,json,hashlib,numpy as np
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from scripts.remeshing.generalized_2d_adaptive_framework_damage_envelope_f1849 import AdaptiveConfig,get_geometry_adapter
B=R/'models/pandey_kumar_mode1/282_f1852_driver_selection';p=B/'case5_original_final.json';d=json.loads(p.read_text())
cfg=AdaptiveConfig.from_json(str(R/'models/pandey_kumar_mode1/279_f1849_damage_envelope/case5_config.json'));adapter=get_geometry_adapter(cfg)
inst=next(iter(d['instances'].values()));nodes={n[0]:n[1:3] for n in inst['nodes']};elems={e[0]:e for e in inst['elements']};f={}
for name in ('S','MISESERI','MISESAVG'):
    q={}
    for v in d['fields'].get(name,[]):q.setdefault(v['element'],[]).append(v['data'])
    f[name]=q
required=all(f.get(n) for n in ('S','MISESERI','MISESAVG'));labels=sorted(f['MISESERI']);bytype={};tot=inside=tri_tot=tri_in=0.
for e in labels:
    typ=elems[e][1];pts=[nodes[n] for n in elems[e][2]];x,y=np.mean(pts,axis=0);a=abs(sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(pts,pts[1:]+pts[:1])))/2;reg=adapter.classify_region(x,y)!='FAR_FIELD';value=f['MISESERI'][e][0];proxy=value*value*a;tot+=proxy;inside+=proxy if reg else 0
    r=bytype.setdefault(typ,{'elements':0,'zero_stress_tensors':0,'zero_base':0,'missing_stress':0});r['elements']+=1;r['missing_stress']+=e not in f['S'];r['zero_stress_tensors']+=e in f['S'] and all(z==0 for ip in f['S'][e] for z in ip);r['zero_base']+=max(f['MISESAVG'][e])==0
    if typ=='CPE3':tri_tot+=proxy;tri_in+=proxy if reg else 0
anomaly=bytype.get('CPE3',{}).get('zero_stress_tensors',0)>0 or bytype.get('CPE3',{}).get('zero_base',0)>0
gate={'accepted':bool(required and not anomaly and tot>0),'step':d['step'],'frame_index':d['step_frame_count']-1,'frame_id':d['frame_id'],'time':d['time'],'source':d['source'],'source_sha256':d['sha256'],'source_bytes':d['bytes'],'native_fields_present':required,'element_type_audit':bytype,'triangle_total_error_proxy_pct':100*tri_tot/tot,'triangle_inside_error_proxy_pct':100*tri_in/inside,'triangle_outside_error_proxy_pct':100*(tri_tot-tri_in)/(tot-inside),'proxy':'sum(native MISESERI squared * element polygon area); NOT Abaqus internal norm','audit_region':'Frozen SevenHolePlateAdapter process segments; audit only','snapshot_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(B/'case5_native_gate.json').write_text(json.dumps(gate,indent=2)+'\n');print(json.dumps(gate,indent=2))
