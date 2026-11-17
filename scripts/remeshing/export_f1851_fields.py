"""Read-only native field/topology export; never computes or modifies an indicator."""
from __future__ import print_function
import sys,os,json,hashlib
from odbAccess import openOdb
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1048576),b''):h.update(c)
    return h.hexdigest()
src,step,idx,target=sys.argv[1:5];idx=int(idx)
assert os.path.isfile(src) and not os.path.exists(target)
o=openOdb(src,readOnly=True);fr=o.steps[step].frames[idx]
d={'source':src,'bytes':os.path.getsize(src),'sha256':sha(src),'step':step,'frame_index':idx,'frame_id':fr.frameId,'time':float(fr.frameValue),'step_frame_count':len(o.steps[step].frames),'instances':{},'fields':{}}
for name,inst in o.rootAssembly.instances.items():
    d['instances'][name]={'nodes':[[n.label]+[float(x) for x in n.coordinates] for n in inst.nodes],'elements':[[e.label,str(e.type),list(e.connectivity)] for e in inst.elements],'sets':{k:[e.label for e in v.elements] for k,v in inst.elementSets.items() if k.upper() in ('UMATELEM','ALL_ELEM','ALL_ELEMS','ALLELEM','UELMECH','UELPHASE')}}
for name in ('SDV1','S','MISESERI','MISESAVG','EVOL','IVOL'):
    if name not in fr.fieldOutputs:continue
    vals=[]
    for v in fr.fieldOutputs[name].values:
        try:data=[float(x) for x in v.data]
        except TypeError:data=float(v.data)
        vals.append({'instance':v.instance.name,'element':v.elementLabel,'ip':getattr(v,'integrationPoint',0),'position':str(v.position),'data':data,'mises':float(v.mises) if name=='S' else None})
    d['fields'][name]=vals
o.close()
with open(target,'w') as f:json.dump(d,f,separators=(',',':'),sort_keys=True)
print(json.dumps({'target':target,'bytes':os.path.getsize(target),'sha256':sha(target),'fields':{n:len(v) for n,v in d['fields'].items()}}))
