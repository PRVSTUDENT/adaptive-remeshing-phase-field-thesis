"""Read missing U/S fields once from the authentic hole ODB; no solver calls."""
from __future__ import print_function
import hashlib
import json
import math
import os
from odbAccess import openOdb

PATH = '/scratch9/pr21vyci/runs/mode1_hole_method_a_test/PK_HOLE_METHOD_A_PREANALYSIS.odb'
PIN = '0A108C6A8404F1AF9D8F5DDC03223E9D8D051AB08587F841D9F5799970AE93B1'


def digest(path):
    h = hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''):
            h.update(b)
    return h.hexdigest().upper()


if not os.path.isfile(PATH) or digest(PATH) != PIN:
    raise ValueError('Missing/changed authentic source ODB')
inp = PATH[:-4]+'.inp'
if not os.path.isfile(inp):
    raise ValueError('Missing exact source input for constitutive provenance')
with open(inp,'r') as stream:
    lines = stream.readlines()
elastic = []
for i,line in enumerate(lines):
    if line.strip().upper().split(',')[0] == '*ELASTIC':
        elastic.append([float(x) for x in lines[i+1].split(',') if x.strip()])
if len(elastic) != 1 or len(elastic[0]) != 2:
    raise ValueError('Ambiguous source elastic constants')
odb = openOdb(path=PATH,readOnly=True)
try:
    frame = odb.steps['Step-1'].frames[-1]
    if frame.frameValue != 1.:
        raise ValueError('Expected authentic final elastic frame')
    field_u,field_s = frame.fieldOutputs['U'],frame.fieldOutputs['S']
    u = {}
    for v in field_u.values:
        key = (v.instance.name,v.nodeLabel)
        data = [float(x) for x in v.data]
        if key in u and u[key] != data:
            raise ValueError('Unequal duplicate U')
        u[key] = data
    stresses = {}
    for v in field_s.values:
        key = (v.instance.name,v.elementLabel)
        data = [float(x) for x in v.data]
        if any(math.isnan(x) or math.isinf(x) for x in data):
            raise ValueError('Nonfinite stress')
        stresses.setdefault(key,[]).append(dict(data=data,integration_point=int(v.integrationPoint),
                                               position=str(v.position),section_point=str(v.sectionPoint)))
    nodes,elems = [],[]
    for name in odb.rootAssembly.instances.keys():
        inst = odb.rootAssembly.instances[name]
        for n in inst.nodes:
            if (name,n.label) not in u:
                raise ValueError('Missing nodal displacement')
            nodes.append(dict(instance=name,label=n.label,coordinates_mm=[float(x) for x in n.coordinates],
                              displacement_mm=u[(name,n.label)]))
        for e in inst.elements:
            if (name,e.label) not in stresses:
                raise ValueError('Missing element stress')
            elems.append(dict(instance=name,label=e.label,type=e.type,connectivity=list(e.connectivity),
                              stress_samples=stresses[(name,e.label)]))
    result = dict(schema=1,source_odb=PATH,source_sha256=PIN,source_bytes=os.path.getsize(PATH),
                  source_input_sha256=digest(inp),source_elastic_constants=elastic[0],
                  step='Step-1',frame=frame.frameValue,version=str(odb.jobData.version),
                  stress_components=list(field_s.componentLabels),displacement_components=list(field_u.componentLabels),
                  nodes=nodes,elements=elems,new_solver_runs=0,odb_modified=False)
finally:
    odb.close()
if digest(PATH) != PIN:
    raise ValueError('Source ODB changed during extraction')
print('F1641_MECHANICS='+json.dumps(result,sort_keys=True,allow_nan=False))
