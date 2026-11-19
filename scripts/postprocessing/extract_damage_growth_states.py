"""Select real ODB frames by measured damage progression, not elapsed frame count.

Visualization only. No indicator, mesh, material or solver changes.
"""
from __future__ import print_function
import os,json,zlib,base64,sys,itertools
from odbAccess import openOdb
BASE='/scratch9/pr21vyci/runs/f1859_suite'
targets=(.10,.35,.65,.95)
for case in (tuple(int(x) for x in sys.argv[1:]) if len(sys.argv)>1 else (1,2,3,5)):
    with open(BASE+'/adaptive_damage_case%d.b64'%case,'rb') as f:
        original=json.loads(zlib.decompress(base64.b64decode(f.read())))
    topology=original['elements'];keys=[(e['instance'],e['label']) for e in topology]
    areas=[]
    for e in topology:
        pts=e['xy'];areas.append(abs(sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts))))*.5)
    odb=openOdb(str(original['odb']),readOnly=True);ra=odb.rootAssembly
    rp=ra.nodeSets['N_RP'] if 'N_RP' in ra.nodeSets else None;frames=[]
    for name in odb.steps.keys():
        for index in range(len(odb.steps[name].frames)):frames.append((name,index))
    cache={}
    def evaluate(index):
        if index in cache:return cache[index]
        name,fi=frames[index];f=odb.steps[name].frames[fi]
        sums={};counts={}
        if 'SDV1' in f.fieldOutputs:
            for v in f.fieldOutputs['SDV1'].values:
                key=(v.instance.name,int(v.elementLabel));sums[key]=sums.get(key,0.)+float(v.data);counts[key]=counts.get(key,0)+1
        if sums:
            assert sorted(sums.keys())==keys
            values=[sums[k]/counts[k] for k in keys]
        else:values=[0.]*len(keys)
        score=sum(a*max(d-.5,0.) for a,d in zip(areas,values))
        cache[index]=(score,values)
        print('AUDIT',case,index,score,max(values));sys.stdout.flush()
        return cache[index]
    end=len(frames)-1;final_score=evaluate(end)[0]
    if final_score<=0:raise ValueError('No damage above 0.5; cannot illustrate crack growth')
    pool=set()
    for fraction in targets:
        lo,hi=0,end
        while lo<hi:
            mid=(lo+hi)//2
            if evaluate(mid)[0]>=fraction*final_score:hi=mid
            else:lo=mid+1
        for index in range(max(0,lo-2),min(end,lo+2)+1):pool.add(index)
    ordered=sorted(pool)
    for index in ordered:evaluate(index)
    best=None
    for combo in itertools.combinations(ordered,4):
        scores=[evaluate(j)[0]/final_score for j in combo]
        if any(scores[j]>scores[j+1]+1e-6 for j in range(3)):continue
        loss=sum((v-t)**2 for v,t in zip(scores,targets))
        if best is None or loss<best[0]:best=(loss,combo,scores)
    if best is None:raise ValueError('No ordered observed progression found')
    states=[]
    for index,fraction in zip(best[1],best[2]):
        name,fi=frames[index];f=odb.steps[name].frames[fi];values=evaluate(index)[1]
        def read_rp(variable):
            field=f.fieldOutputs[variable]
            values=field.getSubset(region=rp).values if rp is not None else field.values
            return float(next(v for v in values if rp is not None or v.nodeLabel==999999).data[1])
        u=read_rp('U');rf=read_rp('RF')
        states.append({'step':name,'frame_index':fi,'frame_id':int(f.frameId),'time':float(f.frameValue),'u2_mm':u,'rf2_kn':rf,'max_damage':max(values),'damage':values,'progress_fraction':fraction,'selection_global_index':index})
    original['states']=states
    original['selection']='Four distinct recorded frames nearest 10/35/65/95% of final integral area*max(SDV1-0.5,0), using bracketed search and neighbouring-frame audit. No interpolation of fields or time.'
    original['selection_audit']={'metric':'sum(element area * max(mean SDV1 - 0.5, 0))','target_fractions':targets,'final_metric':final_score,'selected_global_indices':best[1],'achieved_fractions':best[2],'evaluated_frames':[{'global_index':j,'score':cache[j][0],'max_damage':max(cache[j][1])} for j in sorted(cache)],'distinct_progression':len(set(round(x,5) for x in best[2]))==4,'caveat':'Damage-content progression is a visualization measure, not a fracture error estimator or crack-length measurement.'}
    odb.close()
    raw=json.dumps(original,separators=(',',':')).encode('utf-8')
    with open(BASE+'/adaptive_damage_growth_case%d.b64'%case,'wb') as f:f.write(base64.b64encode(zlib.compress(raw)))
    print('COMPLETE',case,best[1],best[2]);sys.stdout.flush()
