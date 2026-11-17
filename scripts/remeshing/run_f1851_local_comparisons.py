"""CAE-only fidelity diagnostics; frozen production source; no solver execution."""
from __future__ import print_function
import os,sys,json,hashlib
from odbAccess import Odb,openOdb
from abaqusConstants import TWO_D_PLANAR,DEFORMABLE_BODY,TIME,SCALAR,WHOLE_ELEMENT
R=os.environ['F1851_ROOT'];sys.path.insert(0,os.path.join(R,'scripts','remeshing'))
from reusable_2d_adaptive_framework import AdaptiveConfig,AbaqusNativeRemeshingEngine,MeshQualityAuditEngine
B=os.path.join(R,'models','pandey_kumar_mode1','281_f1851_native_diagnostics')
def run(tag,cfg,donor):
    out=os.path.join(B,tag);assert not os.path.exists(out);os.makedirs(out)
    try:
        inp=AbaqusNativeRemeshingEngine.execute_native_remesh(cfg,donor,out,model_name=tag)
        h=hashlib.sha256()
        with open(inp) as f:
            for line in f:
                if not line.strip().startswith('**'):h.update((line.strip()+'\n').encode('utf-8'))
        d={'status':'GENERATED','body_sha256':h.hexdigest(),'inp':os.path.relpath(inp,R).replace('\\','/'),'audit':MeshQualityAuditEngine.evaluate_mesh(inp,l0_mm=cfg.l0)}
    except Exception as e:d={'status':'FAILED','error':str(e)}
    with open(os.path.join(out,'receipt.json'),'w') as f:json.dump(d,f,indent=2)
    print(tag,json.dumps(d))
for idx in (300,337):
    cfg=AdaptiveConfig.from_json(os.path.join(R,'configs','remeshing','f1840_case2_final_frame.json'))
    donor=os.path.join(R,'models','pandey_kumar_mode1','277_f1838_case2_native_pilot','PK_F1838_CASE2_FRAME300_DONOR.odb') if idx==300 else os.path.join(R,'models','pandey_kumar_mode1','278_f1840_final_frame_comparison','PK_F1840_CASE2_FINAL_FRAME_DONOR.odb')
    run('case2_extracted%d'%idx,cfg,donor)
for step,idx in [('Step-1',12),('Step-2',178)]:
    cfg=AdaptiveConfig.from_json(os.path.join(R,'configs','remeshing','f1728_case4_five_hole.json'))
    # Historical F1835 reference controls, fixed for both members of each pair.
    cfg.error_target=3.4;cfg.max_h=.020;cfg.step_name=step;cfg.output_frequency='LAST_INCREMENT'
    source=os.path.join(R,'models','pandey_kumar_mode1','213_f1720_coarse_coupled','PK_F1720_COARSE_COUPLED.odb')
    run('f1720_%s_original'%step,cfg,source)
    with open(os.path.join(B,'f1720_%s_%d.json'%(step.lower().replace('-',''),idx))) as f:d=json.load(f)
    inst=list(d['instances'].values())[0];labels=sorted({v['element'] for v in d['fields']['MISESERI']});es={e[0]:e for e in inst['elements']};offset=min(labels)-1
    path=os.path.join(B,'f1720_%s_extracted.odb'%step);assert not os.path.exists(path)
    odb=Odb(name='F1851',path=path);part=odb.Part(name='PART-1',embeddedSpace=TWO_D_PLANAR,type=DEFORMABLE_BODY)
    part.addNodes(nodeData=tuple(tuple(n[:3]) for n in inst['nodes']))
    for typ in sorted({es[e][1] for e in labels}):
        part.addElements(elementData=tuple(tuple([e-offset]+es[e][2]) for e in labels if es[e][1]==typ),type=typ)
    oi=odb.rootAssembly.Instance(name='PART-1-1',object=part);oi.ElementSetFromElementLabels(name='ALL_ELEM',elementLabels=tuple(e-offset for e in labels))
    st=odb.Step(name=step,description='Untouched single native frame',domain=TIME,timePeriod=1.0);fr=st.Frame(incrementNumber=idx,frameValue=d['time'],description='Native source frame, no indicator transformation')
    for name in ('EVOL','MISESERI','MISESAVG'):
        vals=sorted(d['fields'][name],key=lambda v:v['element']);fo=fr.FieldOutput(name=name,description='Unmodified native '+name,type=SCALAR)
        fo.addData(position=WHOLE_ELEMENT,instance=oi,labels=tuple(v['element']-offset for v in vals),data=tuple((v['data'],) for v in vals))
    odb.save();odb.close();run('f1720_%s_extracted'%step,cfg,path)
