"""Local CAE-only construction/remeshing. No solver submission or fracture solve."""
from __future__ import print_function
import os
import sys
import json
import time
import hashlib

ROOT = os.path.abspath(os.environ['F1849_ROOT'])
sys.path.insert(0, ROOT)
from scripts.remeshing.generalized_2d_adaptive_framework_damage_envelope_f1849 import (
    AdaptiveConfig, prepare_damage_donor, AbaqusNativeRemeshingEngine,
    MeshQualityAuditEngine, get_geometry_adapter)

def sha(path):
    h = hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1048576), b''): h.update(chunk)
    return h.hexdigest()

def main():
    cid = int(sys.argv[-1])
    base = os.path.join(ROOT,'models','pandey_kumar_mode1','279_f1849_damage_envelope')
    with open(os.path.join(base,'inventory.json')) as f: manifest=json.load(f)
    case = next(c for c in manifest['cases'] if c['case_id']==cid)
    if case['status'] != 'READY': raise ValueError('Missing donor; no substitution allowed')
    out = os.path.join(base,'case%d'%cid)
    if not os.path.isdir(out): os.makedirs(out)
    cfg = AdaptiveConfig.from_json(os.path.join(ROOT,case['config']))
    source=os.path.join(ROOT,case['donor'])
    if sha(source)!=case['donor_sha256']: raise ValueError('Donor changed since inventory')
    t0=time.time()
    donor=prepare_damage_donor(cfg,source,os.path.join(out,'PK_F1849_DAMAGE_ENVELOPE.odb'),case['existing_envelope'])
    construct_time=time.time()-t0
    # Explicit synthetic final frame means there is no reason to request all increments.
    cfg.output_frequency='LAST_INCREMENT'
    t0=time.time()
    inp=AbaqusNativeRemeshingEngine.execute_native_remesh(cfg,donor,out,model_name='F1849_CASE_%d'%cid)
    elapsed=time.time()-t0
    audit=MeshQualityAuditEngine.evaluate_mesh(inp,l0_mm=cfg.l0,adapter=get_geometry_adapter(cfg))
    audit.update(task_id=manifest['task_id'],case_id=cid,sizing_driver='CONSTRUCTED_DAMAGE_ENVELOPE',
                 qualifies_native_miseseri=False,donor=os.path.relpath(source,ROOT).replace('\\','/'),
                 donor_sha256=sha(source),active_donor=os.path.relpath(donor,ROOT).replace('\\','/'),
                 active_donor_sha256=sha(donor),source_sha256=sha(__import__('scripts.remeshing.generalized_2d_adaptive_framework_damage_envelope_f1849',fromlist=['']).__file__),
                 physical_mesh=os.path.relpath(inp,ROOT).replace('\\','/'),mesh_sha256=sha(inp),
                 construction_seconds=construct_time,remesh_seconds=elapsed,target_F1779=case['target_F1779'])
    audit['delta_F1779_pct']=100.0*(audit['total_elements']/float(case['target_F1779'])-1)
    with open(os.path.join(out,'audit.json'),'w') as f:json.dump(audit,f,indent=2)
    print(json.dumps({'case':cid,'elements':audit['total_elements'],'delta_pct':audit['delta_F1779_pct'],'seconds':elapsed}))

if __name__=='__main__':main()
