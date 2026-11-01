"""Read-only exact-load Package160 ODB scalar extraction (Abaqus Python2/3)."""
from __future__ import print_function
import hashlib
import json
import math
import os
import sys
import struct


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):
            h.update(chunk)
    return h.hexdigest()


def data(value):
    from abaqusConstants import DOUBLE_PRECISION
    return value.dataDouble if value.precision==DOUBLE_PRECISION else value.data


def main(directory):
    from odbAccess import openOdb
    odb_path=os.path.join(directory,'M1_C4_EXACT_REF.odb')
    output=os.path.join(directory,'package160_recovery_endpoint.json')
    if os.path.exists(output):
        raise RuntimeError('Preserve existing extraction')
    before=sha(odb_path)
    odb=openOdb(path=odb_path,readOnly=True)
    try:
        step=odb.steps['Step-2'];frame=step.frames[-1]
        expected_time=struct.unpack('f',struct.pack('f',0.012))[0]
        if frame.frameValue!=step.timePeriod or step.timePeriod not in (0.012,expected_time):
            raise RuntimeError('Reference step metadata: frame=%.17g period=%.17g' % (frame.frameValue,step.timePeriod))
        rp={}
        for name,key in [('U','uy_mm'),('RF','reaction_force_kN')]:
            values=[v for v in frame.fieldOutputs[name].values if v.nodeLabel==999999]
            if len(values)!=1:
                raise RuntimeError('Ambiguous RP output')
            rp[key]=float(data(values[0])[1])
        regions=[r for r in step.historyRegions.values() if 'U2' in r.historyOutputs and 'RF2' in r.historyOutputs]
        if len(regions)!=1:
            raise RuntimeError('Unique RP history required for precise endpoint')
        region=regions[0]
        rp['field_uy_mm']=rp['uy_mm']
        rp['uy_mm']=float(region.historyOutputs['U2'].data[-1][1])
        rp['reaction_force_kN']=float(region.historyOutputs['RF2'].data[-1][1])
        target=0.0018603125442191958
        if rp['uy_mm'] not in (target,struct.unpack('f',struct.pack('f',target))[0]):
            raise RuntimeError('Reference load mismatch: %.17g' % rp['uy_mm'])
        rp['prescribed_uy_mm']=target
        expected=set((e,g) for e in range(14113,21169) for g in range(1,5))
        energies={}
        for field,key in [('SDV17','fracture_kNmm'),('SDV18','elastic_kNmm')]:
            values={}
            for value in frame.fieldOutputs[field].values:
                pair=(value.elementLabel,value.integrationPoint)
                x=float(data(value))
                if pair in values or math.isnan(x) or math.isinf(x) or x<0:
                    raise RuntimeError('Invalid/duplicate energy')
                values[pair]=x
            if set(values)!=expected:
                raise RuntimeError('Incomplete energy GP coverage')
            for e in range(14113,21169):
                if any(abs(values[e,g]-values[e,1])>max(1e-14,abs(values[e,1])*1e-6) for g in (2,3,4)):
                    raise RuntimeError('Repeated element-energy values disagree')
            energies[key]=sum(values[e,1] for e in range(14113,21169))
        result=dict(schema=1,pbs_job_id='1419305.mmaster02',step='Step-2',increment=frame.incrementNumber,
            step_time=frame.frameValue,step_time_period=step.timePeriod,odb_path=odb_path,
            odb_sha256=before,extractor_sha256=sha(__file__),units='kN, mm, kN*mm',
            energy_elements=7056,energy_integration_points=len(expected),**rp)
        result.update(energies)
        result['raw_total_energy_kNmm']=energies['elastic_kNmm']+energies['fracture_kNmm']
    finally:
        odb.close()
    if sha(odb_path)!=before:
        raise RuntimeError('ODB changed during read-only extraction')
    with open(output,'w') as stream:
        json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main(sys.argv[1])
