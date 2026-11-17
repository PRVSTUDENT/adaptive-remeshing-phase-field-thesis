"""Lossless text export of an existing constructed donor, or explicit damage construction.
Runs under Abaqus Python; never invokes a solver. Original ODB is read-only.
"""
from __future__ import print_function
import os,sys,json,hashlib,math,struct
from odbAccess import openOdb

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()

def main():
    source,target,mode=sys.argv[1:4]
    l0,hbg,eta=map(float,sys.argv[4:7]) if len(sys.argv)>4 else (.0075,.02,.023)
    assert os.path.isfile(source) and not os.path.exists(target)
    o=openOdb(source,readOnly=True)
    assert len(o.rootAssembly.instances)==1,'Explicit instance selection needed'
    inst=list(o.rootAssembly.instances.values())[0]
    elems=list(inst.elementSets['UMATELEM'].elements) if 'UMATELEM' in inst.elementSets else list(inst.elements)
    labels=sorted(e.label for e in elems)
    nodes={int(n.label):[float(x) for x in n.coordinates] for n in inst.nodes}
    step=o.steps['Step-2'];frame=step.frames[-1]
    samples=[]
    if mode=='existing':
        assert frame.frameId==9999 and 'envelope' in str(frame.description).lower()
        fields={name:{v.elementLabel:float(v.data) for v in frame.fieldOutputs[name].values} for name in ['MISESERI','MISESAVG','EVOL']}
        assert all(set(fields[n])==set(labels) for n in fields),'Missing or extraneous field labels'
    elif mode=='damage':
        idx=list(range(0,len(step.frames),5))
        if len(step.frames)-1 not in idx:idx.append(len(step.frames)-1)
        dmax={el:0.0 for el in labels};seen=set()
        for i in idx:
            fr=step.frames[i]
            assert 'SDV1' in fr.fieldOutputs,'Missing damage frame'
            samples.append({'index':i,'frame_id':fr.frameId,'time':fr.frameValue})
            for v in fr.fieldOutputs['SDV1'].values:
                if v.elementLabel in dmax:
                    d=float(v.data);assert not math.isnan(d) and not math.isinf(d)
                    dmax[v.elementLabel]=max(dmax[v.elementLabel],d);seen.add(v.elementLabel)
        assert seen==set(labels)
        fields={n:{} for n in ['MISESERI','MISESAVG','EVOL']}
        f32=lambda x:struct.unpack('f',struct.pack('f',x))[0]
        for e in elems:
            pts=[nodes[n] for n in e.connectivity]
            a=abs(sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts))))/2.
            d=max(0.,min(1.,dmax[e.label]));core=l0/2.5;proc=l0/1.2
            h=core if d>=.5 else proc-(d-.1)/.4*(proc-core) if d>=.1 else hbg-(d-.01)/.09*(hbg-proc) if d>=.01 else hbg
            fields['MISESERI'][e.label]=f32(100.*eta*math.sqrt(a)/h)
            fields['MISESAVG'][e.label]=100.;fields['EVOL'][e.label]=f32(a)
    else:raise ValueError('Unknown export mode')
    payload={'nodes':[[n]+nodes[n] for n in sorted(nodes)],'elements':[[e.label,str(e.type),list(e.connectivity)] for e in sorted(elems,key=lambda x:x.label)],'fields':{name:[[el,vals[el]] for el in labels] for name,vals in fields.items()}}
    data={'schema':'F1850_CONSTRUCTED_DONOR_TEXT_V1','sizing_driver':'CONSTRUCTED_DAMAGE_ENVELOPE','qualifies_native_miseseri':False,'source_odb_path':source,'source_odb_bytes':os.path.getsize(source),'source_odb_sha256':digest(source),'source_step':'Step-2','source_frame_id':frame.frameId,'source_frame_time':frame.frameValue,'source_description':str(frame.description),'mode':mode,'sampled_frames':samples,'part_name':inst.part.name if hasattr(inst,'part') else list(o.parts.keys())[0],'instance_name':inst.name,'mesh_fields':payload}
    data['mesh_fields_sha256']=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
    o.close()
    with open(target,'w') as f:json.dump(data,f,sort_keys=True,separators=(',',':'))
    print(json.dumps({'snapshot':target,'bytes':os.path.getsize(target),'sha256':digest(target),'source_sha256':data['source_odb_sha256'],'elements':len(elems)}))
if __name__=='__main__':main()
