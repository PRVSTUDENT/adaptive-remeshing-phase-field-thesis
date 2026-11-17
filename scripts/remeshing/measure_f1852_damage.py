"""Measure full available donor damage history read-only, no solver invocation."""
from __future__ import print_function
import json,sys,os,hashlib
from odbAccess import openOdb
src,target=sys.argv[1:3];assert not os.path.exists(target)
h=hashlib.sha256()
with open(src,'rb') as f:
    for c in iter(lambda:f.read(1048576),b''):h.update(c)
o=openOdb(src,readOnly=True);dm={};frames=[]
for name,step in o.steps.items():
    for idx,fr in enumerate(step.frames):
        if 'SDV1' not in fr.fieldOutputs:continue
        frames.append({'step':name,'index':idx,'frame_id':fr.frameId,'time':float(fr.frameValue)})
        for v in fr.fieldOutputs['SDV1'].values:
            key=(v.instance.name,v.elementLabel);dm[key]=max(dm.get(key,0.),float(v.data))
o.close();assert dm
d={'source':src,'bytes':os.path.getsize(src),'sha256':h.hexdigest(),'frames_used':frames,'element_count':len(dm),'max_damage':max(dm.values()),'d_core':.5,'elements_ge_core':sum(v>=.5 for v in dm.values()),'fraction_ge_core':sum(v>=.5 for v in dm.values())/float(len(dm)),'uses_full_available_history':True,'online_causal_qualification':False}
with open(target,'w') as f:json.dump(d,f,indent=2)
print(json.dumps({k:v for k,v in d.items() if k!='frames_used'}))
