"""Read-only, bounded R4 ODB diagnostics; Abaqus Python 2.7 compatible.

Exactly 21 named existing ODBs; never invokes solver or scheduler commands.
Exports observed visualizer H/IP values and element-average damage, not binaries.
"""
from __future__ import print_function
import hashlib
import json
import os
from odbAccess import openOdb

ROOT = '/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r4/coupled_1418902.mmaster02'


def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as stream:
        for data in iter(lambda:stream.read(1048576),b''):
            h.update(data)
    return h.hexdigest()


def scalar(value):
    try:
        return float(value.data)
    except (TypeError,ValueError):
        return float(value.data[0])


def main():
    result=[]
    for inner in range(21):
        name='P148_01_%02d_%s' % (inner,'phase' if inner else 'mechanical')
        path=os.path.join(ROOT,name,name+'.odb')
        if not os.path.isfile(path):
            raise RuntimeError('Missing exact ODB '+path)
        before=digest(path)
        endpoint_path=os.path.join(ROOT,name,'endpoint.json')
        with open(endpoint_path) as stream:
            expected=json.load(stream)['odb_sha256']
        if before != expected:
            raise RuntimeError('Changed ODB '+name)
        odb=openOdb(path,readOnly=True)
        try:
            frame=odb.steps['C1-1-ReEquil'].frames[-1]
            observed=[]
            for v in frame.fieldOutputs['SDV2'].values:
                observed.append([int(v.elementLabel)-14112,int(v.integrationPoint),scalar(v)])
            avg={}
            for v in frame.fieldOutputs['SDV1'].values:
                e=int(v.elementLabel)-14112
                value=scalar(v)
                if e in avg and abs(value-avg[e])>1e-12:
                    raise RuntimeError('Inconsistent repeated average damage')
                avg[e]=value
            if len(observed)!=28224 or len(avg)!=7056:
                raise RuntimeError('Incomplete visualizer coverage')
            result.append(dict(iteration=inner,odb_sha256=before,history=sorted(observed),
                               damage_average=sorted(avg.items()),
                               field_names=sorted(frame.fieldOutputs.keys())))
        finally:
            odb.close()
        if digest(path)!=before:
            raise RuntimeError('ODB mutated during read')
    print(json.dumps(dict(schema=1,read_only=True,solves=result),allow_nan=False))


if __name__=='__main__':
    main()
