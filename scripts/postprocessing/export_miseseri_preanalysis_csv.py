# Abaqus Python: export MISESERI pre-analysis element table for Job 2 gate.
# Env:
#   MISESERI_ODB_PATH
#   MISESERI_OUTPUT_CSV
#   MISESERI_TECH_JSON (optional)

from __future__ import print_function

import csv
import json
import math
import os
import sys


def _env(name):
    v = os.environ.get(name)
    if not v:
        raise RuntimeError("Missing env %s" % name)
    return v


def _scalar(value):
    data = value.data
    try:
        return float(data[0])
    except Exception:
        return float(data)


def _von_mises(sdata):
    # plane stress-ish or 3D components from Abaqus S
    # data may be (s11,s22,s33,s12,...) or fewer
    try:
        comps = [float(x) for x in sdata]
    except TypeError:
        comps = [float(sdata)]
    while len(comps) < 4:
        comps.append(0.0)
    s11, s22, s33, s12 = comps[0], comps[1], comps[2] if len(comps) > 2 else 0.0, comps[3] if len(comps) > 3 else 0.0
    # standard VM
    return math.sqrt(
        0.5 * ((s11 - s22) ** 2 + (s22 - s33) ** 2 + (s33 - s11) ** 2) + 3.0 * (s12 ** 2)
    )


def main():
    odb_path = _env("MISESERI_ODB_PATH")
    out_csv = _env("MISESERI_OUTPUT_CSV")
    tech_json = os.environ.get("MISESERI_TECH_JSON", "")
    from odbAccess import openOdb

    odb = openOdb(path=odb_path, readOnly=True)
    step = list(odb.steps.values())[-1]
    frame = step.frames[-1]
    fields = frame.fieldOutputs
    keys = list(fields.keys())
    print("field_keys=", sorted(str(k) for k in keys))

    needed = ["MISESERI", "MISESAVG", "S", "EVOL", "U", "RF"]
    present = {}
    for k in needed:
        present[k] = k in keys
        print(k, "present=", present[k])

    # Final RP displacement
    u_final = None
    rf_final = None
    if "U" in keys:
        ufo = fields["U"]
        # try RP nset
        rp_set = None
        try:
            for name, ns in odb.rootAssembly.nodeSets.items():
                if str(name).upper().endswith("RP") or str(name).upper() == "RP":
                    rp_set = ns
                    break
        except Exception:
            rp_set = None
        if rp_set is not None:
            usub = ufo.getSubset(region=rp_set)
            for v in usub.values:
                try:
                    u_final = float(v.data[1])  # U2
                except Exception:
                    u_final = float(v.data[0])
                break
        if "RF" in keys and rp_set is not None:
            rfsub = fields["RF"].getSubset(region=rp_set)
            for v in rfsub.values:
                try:
                    rf_final = float(v.data[1])
                except Exception:
                    rf_final = float(v.data[0])
                break
    print("U2_final=", u_final)
    print("RF2_final=", rf_final)

    inst = list(odb.rootAssembly.instances.values())[0]
    n_inst_el = len(list(inst.elements))
    print("instance_elements=", n_inst_el)

    # element sets for umatelem
    elset = None
    try:
        for name, s in odb.rootAssembly.elementSets.items():
            up = str(name).upper()
            if up.endswith("UMATELEM") or up == "UMATELEM":
                elset = s
                break
    except Exception:
        elset = None

    def subset(name):
        fo = fields[name]
        if elset is not None:
            return fo.getSubset(region=elset)
        return fo

    miseseri_by = {}
    for v in subset("MISESERI").values:
        lab = int(v.element.label)
        miseseri_by[lab] = _scalar(v)
    misesavg_by = {}
    for v in subset("MISESAVG").values:
        misesavg_by[int(v.element.label)] = _scalar(v)
    evol_by = {}
    for v in subset("EVOL").values:
        evol_by[int(v.element.label)] = _scalar(v)
    vm_by = {}
    for v in subset("S").values:
        lab = int(v.element.label)
        try:
            vm_by[lab] = _von_mises(v.data)
        except Exception:
            vm_by[lab] = float("nan")

    sdv15_by = {}
    if "SDV15" in keys:
        for v in subset("SDV15").values:
            sdv15_by[int(v.element.label)] = _scalar(v)

    # geometry from instance; map CPS4 labels to physical = label - 2N
    # layered: U1 1..N, U2 N+1..2N, CPS4 2N+1..3N
    # From umatelem labels which are CPS4 range
    nodes = {}
    for node in inst.nodes:
        nodes[int(node.label)] = (float(node.coordinates[0]), float(node.coordinates[1]))
    elements = {}
    for el in inst.elements:
        conn = [int(n) for n in el.connectivity]
        if len(conn) >= 4:
            elements[int(el.label)] = conn[:4]

    # Determine N from umatelem count
    n_phys = len(miseseri_by)
    print("n_miseseri=", n_phys)

    rows = []
    for lab in sorted(miseseri_by.keys()):
        conn = elements.get(lab)
        if not conn:
            continue
        pts = [nodes[n] for n in conn]
        xc = sum(p[0] for p in pts) / 4.0
        yc = sum(p[1] for p in pts) / 4.0
        # physical label estimate
        phys = lab - 2 * n_phys if lab > 2 * n_phys else lab
        rows.append(
            {
                "physical_element_label": phys,
                "visualization_element_label": lab,
                "centroid_x": xc,
                "centroid_y": yc,
                "MISESERI": miseseri_by[lab],
                "MISESAVG": misesavg_by.get(lab, ""),
                "EVOL": evol_by.get(lab, ""),
                "von_mises": vm_by.get(lab, ""),
                "SDV15": sdv15_by.get(lab, ""),
                "n1": conn[0],
                "n2": conn[1],
                "n3": conn[2],
                "n4": conn[3],
            }
        )

    out_dir = os.path.dirname(out_csv)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with open(out_csv, "w") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "physical_element_label",
                "visualization_element_label",
                "centroid_x",
                "centroid_y",
                "MISESERI",
                "MISESAVG",
                "EVOL",
                "von_mises",
                "SDV15",
                "n1",
                "n2",
                "n3",
                "n4",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    tech = {
        "odb_path": odb_path,
        "step": step.name,
        "frame": len(step.frames) - 1,
        "field_present": present,
        "U2_final": u_final,
        "RF2_final": rf_final,
        "instance_elements": n_inst_el,
        "n_miseseri_values": n_phys,
        "n_csv_rows": len(rows),
        "u_pre_target": 0.00464,
        "u2_near_target": (u_final is not None and abs(u_final - 0.00464) <= 1.0e-4),
        "mapping_layered_ok": n_inst_el == 11790,
        "n_phys_ok": n_phys == 3930,
    }
    if tech_json:
        with open(tech_json, "w") as stream:
            json.dump(tech, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print("tech=", json.dumps(tech, sort_keys=True))
    odb.close()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("ERROR:", exc)
        sys.exit(12)
