from __future__ import print_function
import os,json
from odbAccess import openOdb
root=os.environ['F1849_ROOT']
base=os.path.join(root,'models/pandey_kumar_mode1/279_f1849_damage_envelope')
with open(os.path.join(base,'inventory.json')) as f: inventory=json.load(f)
results=[]
for c in inventory['cases']:
    if c['status']!='READY':continue
    o=openOdb(os.path.join(root,c['donor']),readOnly=True)
    steps=[]
    for name in o.steps.keys():
        st=o.steps[name];fr=st.frames[-1]
        steps.append({'step':name,'frames':len(st.frames),'final_frame_id':fr.frameId,'description':str(fr.description),'time':fr.frameValue,'fields':list(fr.fieldOutputs.keys())})
    item={'case_id':c['case_id'],'steps':steps,'instances':list(o.rootAssembly.instances.keys())};results.append(item);print(json.dumps(item))
    o.close()
with open(os.path.join(base,'donor_inspection.json'),'w') as f:json.dump(results,f,indent=2)
