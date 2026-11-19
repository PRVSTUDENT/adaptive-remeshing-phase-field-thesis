"""Read existing F1859 ODBs only; export four recorded damage states per case."""
from __future__ import print_function
import os,json,gzip,base64,csv,re,sys
from odbAccess import openOdb
BASE='/scratch9/pr21vyci/runs/f1859_suite'
out=[]
for case in (tuple(int(x) for x in sys.argv[1:]) if len(sys.argv)>1 else (1,2,3,5)):
    print('OPENING case',case);sys.stdout.flush()
    path=BASE+'/job2_adaptive_case%d/PK_F1859_J2_C%d.odb'%(case,case)
    odb=openOdb(path,readOnly=True);ra=odb.rootAssembly
    region=ra.nodeSets['N_RP'] if 'N_RP' in ra.nodeSets else None
    frames=[]
    with open(path.replace('.odb','_rf_u.csv')) as f:
        history=list(csv.DictReader(f))
    peakrow=max(history,key=lambda r:abs(float(r['rf2_kn'])))
    peak_u=float(peakrow['u2_mm'])
    with open(path.replace('.odb','.inp')) as f: deck=f.read()
    targets=[float(v) for v in re.findall(r'^N_RP,\s*2,\s*2,\s*([0-9.eE+-]+)',deck,re.M)]
    assert len(targets)==len(odb.steps.keys())
    prior=0.
    for si,sn in enumerate(odb.steps.keys()):
        st=odb.steps[sn]
        for fi,f in enumerate(st.frames):
            # Deck uses linear ramp over unit step time. Selection only; actual U/RF read below.
            frames.append((sn,fi,float(f.frameValue),prior+(targets[si]-prior)*float(f.frameValue),0.))
        prior=targets[si]
    peak=min(range(len(frames)),key=lambda j:abs(frames[j][3]-peak_u))
    # Explicit reproducible selection: near pre-peak, peak, post-peak, last converged.
    pre=min(range(peak+1),key=lambda j:abs(frames[j][3]-.9*frames[peak][3]))
    ids=[pre,peak,peak+int((len(frames)-1-peak)*.5),len(frames)-1]
    states=[];topology=None
    print('SELECTED case',case,'frames',ids);sys.stdout.flush()
    for idx in ids:
        print('READING case',case,'index',idx);sys.stdout.flush()
        sn,fi,t,u,rf=frames[idx];f=odb.steps[sn].frames[fi]
        def rp(var):
            field=f.fieldOutputs[var]
            vals=field.getSubset(region=region).values if region is not None else field.values
            for v in vals:
                if region is not None or v.nodeLabel==999999:return float(v.data[1])
            raise ValueError('Missing reference point '+var)
        u,rf=rp('U'),rp('RF')
        sums={};counts={}
        for v in f.fieldOutputs['SDV1'].values:
            key=(v.instance.name,int(v.elementLabel));sums[key]=sums.get(key,0.)+float(v.data);counts[key]=counts.get(key,0)+1
        keys=sorted(sums.keys())
        if topology is None:
            instnodes={};instelems={}
            for name in set(k[0] for k in keys):
                inst=ra.instances[name];instnodes[name]=dict((n.label,[float(x) for x in n.coordinates[:2]]) for n in inst.nodes)
                instelems[name]=dict((e.label,list(e.connectivity)) for e in inst.elements)
            topology=[{'instance':name,'label':label,'xy':[instnodes[name][n] for n in instelems[name][label]]} for name,label in keys]
        assert [(x['instance'],x['label']) for x in topology]==keys
        vals=[sums[k]/counts[k] for k in keys]
        states.append({'step':sn,'frame_index':fi,'frame_id':int(f.frameId),'time':t,'u2_mm':u,'rf2_kn':rf,'max_damage':max(vals),'damage':vals})
    out.append({'case':case,'odb':path,'odb_bytes':os.path.getsize(path),'aggregation':'Arithmetic mean of SDV1 integration-point values per companion element; no spatial smoothing','selection':'90% peak displacement pre-peak; peak load; halfway in recorded frames from peak to last; last converged frame','elements':topology,'states':states})
    odb.close()
    raw=json.dumps(out[-1],separators=(',',':')).encode('utf-8')
    with open(BASE+'/adaptive_damage_case%d.b64'%case,'wb') as f:
        f.write(base64.b64encode(__import__('zlib').compress(raw)))
    print('EXTRACTED case',case,'elements',len(topology),'frames',ids);sys.stdout.flush()
payload=json.dumps(out,separators=(',',':')).encode('utf-8')
encoded=base64.b64encode(gzip.compress(payload) if hasattr(gzip,'compress') else __import__('zlib').compress(payload))
with open(BASE+'/adaptive_damage_contours.b64','wb') as f:f.write(encoded)
print('EXPORT_COMPLETE')
