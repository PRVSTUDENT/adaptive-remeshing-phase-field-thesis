"""Run the same measured driver strategy for one supplied donor configuration."""
from __future__ import print_function
import os,sys,json,time,hashlib
R=os.environ['F1852_ROOT'];sys.path.insert(0,R)
from scripts.remeshing.generalized_2d_adaptive_framework_driver_selection_f1852 import remesh
from scripts.remeshing.generalized_2d_adaptive_framework_damage_envelope_f1849 import AdaptiveConfig,MeshQualityAuditEngine,get_geometry_adapter
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1048576),b''):h.update(c)
    return h.hexdigest()
cid=int(sys.argv[-1]);B=os.path.join(R,'models','pandey_kumar_mode1','282_f1852_driver_selection')
with open(os.path.join(B,'case%d_damage_strength.json'%cid)) as f:signal=json.load(f)
with open(os.path.join(B,'case5_native_gate.json')) as f:gate=json.load(f)
with open(os.path.join(R,'models','pandey_kumar_mode1','280_f1850_donor_recovery','case%d_donor.json'%cid)) as f:snapshot=json.load(f)
cfg=AdaptiveConfig.from_json(os.path.join(R,'models','pandey_kumar_mode1','279_f1849_damage_envelope','case%d_config.json'%cid))
if signal['max_damage']>=.5 and signal['sha256']!=snapshot['source_odb_sha256']:raise ValueError('Damage signal source differs from frozen input snapshot')
native_donor=os.path.join(R,gate['source']);assert sha(native_donor)==gate['source_sha256']
donor=os.path.join(R,'models','pandey_kumar_mode1','280_f1850_donor_recovery','case%d'%cid,'PK_F1850_TEXT_DONOR.odb')
out=os.path.join(B,'case%d'%cid);assert not os.path.exists(out);os.makedirs(out)
t=time.time();inp,driver=remesh(cfg,signal,gate,donor,native_donor,out,'F1852_CASE_%d'%cid)
audit=MeshQualityAuditEngine.evaluate_mesh(inp,l0_mm=cfg.l0,adapter=get_geometry_adapter(cfg))
audit.update(case_id=cid,driver=driver,provenance_classification=driver,indicator_type=driver,qualifies_native_miseseri=False,remesh_seconds=time.time()-t,physical_mesh=os.path.relpath(inp,R).replace('\\','/'),mesh_sha256=sha(inp),damage_strength=signal,native_gate=gate if driver.startswith('NATIVE') else None,framework_sha256=sha(os.path.join(R,'scripts','remeshing','generalized_2d_adaptive_framework_driver_selection_f1852.py')))
h=hashlib.sha256()
with open(inp) as f:
    for line in f:
        if not line.strip().startswith('**'):h.update((line.strip()+'\n').encode('utf-8'))
audit['body_sha256']=h.hexdigest()
with open(os.path.join(out,'audit.json'),'w') as f:json.dump(audit,f,indent=2)
print(json.dumps({'case':cid,'driver':driver,'elements':audit['total_elements']}))
