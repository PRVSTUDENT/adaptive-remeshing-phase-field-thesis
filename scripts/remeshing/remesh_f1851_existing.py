"""Unmodified production engine, existing donor only; no solver calls."""
from __future__ import print_function
import os,sys,json,hashlib,time
root=os.environ['F1851_HOME'];sys.path.insert(0,root)
from reusable_2d_adaptive_framework import AdaptiveConfig,AbaqusNativeRemeshingEngine,MeshQualityAuditEngine
config,donor,out,step=sys.argv[-4:];assert not os.path.exists(out)
os.makedirs(out);cfg=AdaptiveConfig.from_json(config);cfg.step_name=step
t=time.time()
try:
    inp=AbaqusNativeRemeshingEngine.execute_native_remesh(cfg,donor,out,model_name='F1851_DIAGNOSTIC')
    h=hashlib.sha256()
    with open(inp) as f:
        for line in f:
            if not line.strip().startswith('**'):h.update((line.strip()+'\n').encode('utf-8'))
    d={'status':'GENERATED','inp':inp,'body_sha256':h.hexdigest(),'audit':MeshQualityAuditEngine.evaluate_mesh(inp,l0_mm=cfg.l0),'seconds':time.time()-t}
except Exception as e:d={'status':'FAILED_SUPPORTED_PATH_TEST','error':str(e),'seconds':time.time()-t}
with open(os.path.join(out,'receipt.json'),'w') as f:json.dump(d,f,indent=2)
print(json.dumps(d))
