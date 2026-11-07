import odbAccess
import json

odb_rec = odbAccess.openOdb("PK_HOLE_COUPLED_RECOVERY.odb", readOnly=True)
inst_rec = odb_rec.rootAssembly.instances['PLATE-1']
nodes_rec = {n.label: (float(n.coordinates[0]), float(n.coordinates[1])) for n in inst_rec.nodes}

rec_elems = {}
for el in inst_rec.elements:
    rec_elems[el.label] = [int(lbl) for lbl in el.connectivity]

frame_rec = odb_rec.steps['Step-1'].frames[-1]

s_mises = {}
for v in frame_rec.fieldOutputs['S'].values:
    eid = v.elementLabel
    if eid not in s_mises:
        s_mises[eid] = []
    s_mises[eid].append(float(v.mises))
s_mises_avg = {eid: float(sum(vals)/len(vals)) for eid, vals in s_mises.items()}

miseseri = {}
for v in frame_rec.fieldOutputs['MISESERI'].values:
    if v.elementLabel not in miseseri:
        miseseri[v.elementLabel] = float(v.data)

misesavg = {}
for v in frame_rec.fieldOutputs['MISESAVG'].values:
    if v.elementLabel not in misesavg:
        misesavg[v.elementLabel] = float(v.data)

odb_rec.close()

data = {
    'nodes': nodes_rec,
    'elements': rec_elems,
    's_mises': s_mises_avg,
    'miseseri': miseseri,
    'misesavg': misesavg
}

with open("f1655_recovery_plot_data.json", "w") as fp:
    json.dump(data, fp)
print("Saved f1655_recovery_plot_data.json")
