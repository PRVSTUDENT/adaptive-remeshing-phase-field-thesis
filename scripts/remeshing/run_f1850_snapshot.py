"""Reconstruct a minimal donor from lossless text and run frozen F1849 CAE sizing."""
from __future__ import print_function
import os,sys,json,hashlib,time
from odbAccess import Odb,openOdb
from abaqusConstants import TWO_D_PLANAR,DEFORMABLE_BODY,TIME,SCALAR,WHOLE_ELEMENT
ROOT=os.environ['F1849_ROOT'];sys.path.insert(0,ROOT)
from scripts.remeshing.generalized_2d_adaptive_framework_damage_envelope_f1849 import AdaptiveConfig,AbaqusNativeRemeshingEngine,MeshQualityAuditEngine,get_geometry_adapter

def main():
    cid=int(sys.argv[-1]);base=os.path.join(ROOT,'models','pandey_kumar_mode1','280_f1850_donor_recovery')
    with open(os.path.join(base,'case%d_donor.json'%cid)) as f:d=json.load(f)
    # JSON float rendering differs between CAE Python 2 and standalone Python 3.
    # Validate the text hash externally; here verify numeric values after ODB roundtrip.
    p=d['mesh_fields'];assert len(d['mesh_fields_sha256'])==64
    out=os.path.join(base,'case%d'%cid)
    if not os.path.isdir(out):os.makedirs(out)
    path=os.path.join(out,'PK_F1850_TEXT_DONOR.odb')
    if not os.path.exists(path):
        odb=Odb(name='F1850',analysisTitle='Lossless constructed envelope snapshot',description='CONSTRUCTED_DAMAGE_ENVELOPE text reconstruction',path=path)
        part=odb.Part(name=d['part_name'],embeddedSpace=TWO_D_PLANAR,type=DEFORMABLE_BODY)
        part.addNodes(nodeData=tuple(tuple(n[:3]) for n in p['nodes']))
        for typ in sorted(set(e[1] for e in p['elements'])):
            part.addElements(elementData=tuple(tuple([e[0]]+e[2]) for e in p['elements'] if e[1]==typ),type=typ)
        inst=odb.rootAssembly.Instance(name=d['instance_name'],object=part)
        inst.ElementSetFromElementLabels(name='ALL_ELEM',elementLabels=tuple(e[0] for e in p['elements']))
        step=odb.Step(name='Step-2',description='Constructed envelope only',domain=TIME,timePeriod=1.0)
        frame=step.Frame(incrementNumber=9999,frameValue=1.0,description='CONSTRUCTED_DAMAGE_ENVELOPE lossless text envelope')
        for name,vals in p['fields'].items():
            field=frame.FieldOutput(name=name,description='Constructed sizing '+name,type=SCALAR)
            field.addData(position=WHOLE_ELEMENT,instance=inst,labels=tuple(v[0] for v in vals),data=tuple((v[1],) for v in vals))
        odb.save();odb.close()
    check=openOdb(path,readOnly=True);fr=check.steps['Step-2'].frames[-1]
    for name,vals in p['fields'].items():assert [[v.elementLabel,float(v.data)] for v in fr.fieldOutputs[name].values]==vals
    assert len(check.rootAssembly.instances[d['instance_name']].elements)==len(p['elements'])
    check.close()
    cfg=AdaptiveConfig.from_json(os.path.join(ROOT,'models','pandey_kumar_mode1','279_f1849_damage_envelope','case%d_config.json'%cid));cfg.output_frequency='LAST_INCREMENT';cfg.sizing_driver='CONSTRUCTED_DAMAGE_ENVELOPE'
    start=time.time();inp=AbaqusNativeRemeshingEngine.execute_native_remesh(cfg,path,out,model_name='F1850_CASE_%d'%cid)
    audit=MeshQualityAuditEngine.evaluate_mesh(inp,l0_mm=cfg.l0,adapter=get_geometry_adapter(cfg))
    audit.update(case_id=cid,remesh_seconds=time.time()-start,physical_mesh=os.path.relpath(inp,ROOT).replace('\\','/'),donor_logical_sha256=d['mesh_fields_sha256'],source_odb_sha256=d['source_odb_sha256'],field_roundtrip_exact=True,sizing_driver='CONSTRUCTED_DAMAGE_ENVELOPE',qualifies_native_miseseri=False)
    with open(os.path.join(out,'audit.json'),'w') as f:json.dump(audit,f,indent=2)
    print(json.dumps({'case':cid,'elements':audit['total_elements'],'field_roundtrip_exact':True}))
if __name__=='__main__':main()
