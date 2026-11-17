from __future__ import print_function
import sys,os,json
from odbAccess import openOdb
o=openOdb(sys.argv[1],readOnly=True)
d={'path':sys.argv[1],'bytes':os.path.getsize(sys.argv[1]),'instances':{k:{'nodes':len(v.nodes),'elements':len(v.elements),'sets':list(v.elementSets.keys())} for k,v in o.rootAssembly.instances.items()},'steps':{k:{'frames':len(v.frames),'last_time':v.frames[-1].frameValue,'last_id':v.frames[-1].frameId,'fields':{n:{'count':len(f.values),'position':str(f.locations[0].position) if f.locations else None,'first_labels':[x.elementLabel for x in list(f.values)[:4]] if f.values and hasattr(f.values[0],'elementLabel') else []} for n,f in v.frames[-1].fieldOutputs.items()}} for k,v in o.steps.items()}}
o.close();print(json.dumps(d))
