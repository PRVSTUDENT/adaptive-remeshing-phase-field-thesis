import odbAccess, json, sys
odb = odbAccess.openOdb(sys.argv[1], readOnly=True)
inst = list(odb.rootAssembly.instances.values())[0]
nphys = len(inst.elements) // 3
def state(frame):
    dgp = {}; hgp = {}; energies = {}
    for v in frame.fieldOutputs['SDV1'].values:
        dgp.setdefault((v.elementLabel - 1) % nphys + 1, []).append(float(v.data))
    for v in frame.fieldOutputs['SDV2'].values:
        hgp[str((v.elementLabel - 1) % nphys + 1) + '_' + str(v.integrationPoint)] = float(v.data)
    for key in ['SDV17', 'SDV18']:
        if key in frame.fieldOutputs:
            by = {}
            for v in frame.fieldOutputs[key].values:
                by[v.elementLabel] = float(v.data)
            energies[key] = sum(by.values())
    nd = {}
    for e in inst.elements:
        eid = (e.label - 1) % nphys + 1
        if eid in dgp:
            d = sum(dgp[eid]) / len(dgp[eid])
            for n in e.connectivity:
                nd.setdefault(n, []).append(d)
    damage = {str(n): sum(v) / len(v) for n, v in nd.items()}
    u_dict = {}
    if 'U' in frame.fieldOutputs:
        for v in frame.fieldOutputs['U'].values:
            if v.nodeLabel != 999999:
                u_dict[str(v.nodeLabel)] = [float(x) for x in v.data]
    def rp(key, comp=1):
        vals = [v for v in frame.fieldOutputs[key].values if v.nodeLabel == 999999]
        if not vals:
            raise ValueError('Missing RP ' + key)
        return float(vals[0].data[comp])
    return dict(damage=damage, history=hgp, displacements=u_dict, uy=rp('U', 1), rf2=rp('RF', 1),
                energies=energies, step_frame=frame.incrementNumber, frame_time=frame.frameValue)

steps = list(odb.steps.values())
result = {
    'hold': state(steps[0].frames[-1]),
    'terminal': state(steps[-1].frames[-1]),
    'steps': [s.name for s in steps]
}
result['peak_rf2'] = max(abs(float(v.data[1])) for s in steps for f in s.frames
                         for v in f.fieldOutputs['RF'].values if v.nodeLabel == 999999 and f.incrementNumber > 0)
with open(sys.argv[2], 'w') as f:
    json.dump(result, f)
odb.close()
