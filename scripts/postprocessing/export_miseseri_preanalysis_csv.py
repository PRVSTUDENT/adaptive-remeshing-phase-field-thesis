# Abaqus Python: export MISESERI pre-analysis element table for Job 2 gate.
# Configurable Env:
#   MISESERI_ODB_PATH
#   MISESERI_OUTPUT_CSV
#   MISESERI_TECH_JSON (optional)
#   MISESERI_AUX_CONTINUUM (optional, default 1)
#   MISESERI_DISPLACEMENT_COMPONENT (optional, default 1 -> U1)
#   MISESERI_REACTION_COMPONENT (optional, default 1 -> RF1)
#   MISESERI_TARGET_DISPLACEMENT (optional, default 0.001 mm)
#   MISESERI_TARGET_TOLERANCE (optional, default 1.0e-4 mm)

from __future__ import print_function

import csv
import json
import math
import os
import sys


def _env(name, default=None):
    v = os.environ.get(name, default)
    if v is None:
        raise RuntimeError("Missing env %s" % name)
    return v


def _scalar(value):
    data = value.data
    try:
        return float(data[0])
    except Exception:
        return float(data)


def _von_mises(sdata):
    try:
        comps = [float(x) for x in sdata]
    except TypeError:
        comps = [float(sdata)]
    while len(comps) < 4:
        comps.append(0.0)
    s11, s22, s33, s12 = comps[0], comps[1], comps[2] if len(comps) > 2 else 0.0, comps[3] if len(comps) > 3 else 0.0
    return math.sqrt(
        0.5 * ((s11 - s22) ** 2 + (s22 - s33) ** 2 + (s33 - s11) ** 2) + 3.0 * (s12 ** 2)
    )


def percentile(sorted_list, p):
    if not sorted_list:
        return 0.0
    idx = (len(sorted_list) - 1) * (p / 100.0)
    lower = int(math.floor(idx))
    upper = int(math.ceil(idx))
    if lower == upper:
        return sorted_list[lower]
    weight = idx - lower
    return sorted_list[lower] * (1.0 - weight) + sorted_list[upper] * weight


def quantify_miseseri_field(rows, target_disp=0.001, target_tol=1e-4, disp_comp=1, rf_comp=1, u_final=None, rf_final=None, expected_elements=3930):
    n_rows = len(rows)
    if n_rows == 0:
        return {
            "n_csv_rows": 0,
            "n_phys_ok": False,
            "all_finite": False,
            "has_positive_nonzero": False,
            "u_near_target": False,
            "error": "Empty MISESERI element rows",
        }

    miseseri_vals = []
    for r in rows:
        val = r.get("MISESERI")
        if val is not None and val != "":
            miseseri_vals.append(float(val))
        else:
            miseseri_vals.append(float("nan"))

    all_finite = all(math.isfinite(v) for v in miseseri_vals)
    has_positive_nonzero = any(math.isfinite(v) and v > 0.0 for v in miseseri_vals)

    valid_vals = [v for v in miseseri_vals if math.isfinite(v)]
    if not valid_vals:
        return {
            "n_csv_rows": n_rows,
            "n_phys_ok": (n_rows == expected_elements),
            "all_finite": False,
            "has_positive_nonzero": False,
            "u_near_target": False,
            "error": "No finite MISESERI values found",
        }

    sorted_vals = sorted(valid_vals)
    min_val = sorted_vals[0]
    max_val = sorted_vals[-1]
    mean_val = sum(valid_vals) / float(len(valid_vals))
    median_val = percentile(sorted_vals, 50.0)
    p90 = percentile(sorted_vals, 90.0)
    p95 = percentile(sorted_vals, 95.0)
    p99 = percentile(sorted_vals, 99.0)

    # Max location
    max_row = max(rows, key=lambda r: float(r["MISESERI"]) if math.isfinite(float(r.get("MISESERI", float("-inf")))) else float("-inf"))
    max_phys_label = max_row["physical_element_label"]
    max_vis_label = max_row["visualization_element_label"]
    max_cx = float(max_row["centroid_x"])
    max_cy = float(max_row["centroid_y"])
    max_dist_notch = math.sqrt(max_cx ** 2 + max_cy ** 2)

    count_p90 = sum(1 for v in valid_vals if v >= p90)
    count_p95 = sum(1 for v in valid_vals if v >= p95)
    thresh_5pct = 0.05 * max_val
    count_5pct = sum(1 for v in valid_vals if v >= thresh_5pct)

    frac_p90 = count_p90 / float(len(valid_vals))
    frac_p95 = count_p95 / float(len(valid_vals))
    frac_5pct = count_5pct / float(len(valid_vals))

    u_near = (u_final is not None and abs(abs(u_final) - target_disp) <= target_tol)

    return {
        "n_csv_rows": n_rows,
        "n_phys_ok": (n_rows == expected_elements),
        "all_finite": all_finite,
        "has_positive_nonzero": has_positive_nonzero,
        "displacement_component": disp_comp,
        "reaction_component": rf_comp,
        "U_final": u_final,
        "U1_final": u_final if disp_comp == 1 else None,
        "RF_final": rf_final,
        "RF1_final": rf_final if rf_comp == 1 else None,
        "u_pre_target": target_disp,
        "u_target_tolerance": target_tol,
        "u_near_target": u_near,
        "miseseri_min": min_val,
        "miseseri_max": max_val,
        "miseseri_mean": mean_val,
        "miseseri_median": median_val,
        "miseseri_p90": p90,
        "miseseri_p95": p95,
        "miseseri_p99": p99,
        "max_element_physical": max_phys_label,
        "max_element_visualization": max_vis_label,
        "max_centroid_x": max_cx,
        "max_centroid_y": max_cy,
        "max_distance_from_notch_tip": max_dist_notch,
        "count_above_p90": count_p90,
        "fraction_above_p90": frac_p90,
        "count_above_p95": count_p95,
        "fraction_above_p95": frac_p95,
        "threshold_5pct_max": thresh_5pct,
        "count_above_5pct_max": count_5pct,
        "fraction_above_5pct_max": frac_5pct,
    }


def main():
    odb_path = _env("MISESERI_ODB_PATH")
    out_csv = _env("MISESERI_OUTPUT_CSV")
    tech_json = os.environ.get("MISESERI_TECH_JSON", "")

    disp_comp = int(os.environ.get("MISESERI_DISPLACEMENT_COMPONENT", "1"))
    rf_comp = int(os.environ.get("MISESERI_REACTION_COMPONENT", "1"))
    target_disp = float(os.environ.get("MISESERI_TARGET_DISPLACEMENT", "0.001"))
    target_tol = float(os.environ.get("MISESERI_TARGET_TOLERANCE", "1.0e-4"))

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

    u_idx = disp_comp - 1
    rf_idx = rf_comp - 1

    u_final = None
    rf_final = None
    if "U" in keys:
        ufo = fields["U"]
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
                    u_final = float(v.data[u_idx])
                except Exception:
                    u_final = float(v.data[0])
                break
        if "RF" in keys and rp_set is not None:
            rfsub = fields["RF"].getSubset(region=rp_set)
            for v in rfsub.values:
                try:
                    rf_final = float(v.data[rf_idx])
                except Exception:
                    rf_final = float(v.data[0])
                break
    print("U%d_final=" % disp_comp, u_final)
    print("RF%d_final=" % rf_comp, rf_final)

    inst = list(odb.rootAssembly.instances.values())[0]
    n_inst_el = len(list(inst.elements))
    print("instance_elements=", n_inst_el)

    elset = None
    try:
        items = list(odb.rootAssembly.elementSets.items())
        for name, s in items:
            up = str(name).upper()
            if up.endswith("PLATE") or up == "PLATE":
                elset = s
                break
        if elset is None:
            for name, s in items:
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

    def _elem_label(v):
        if hasattr(v, "elementLabel"):
            return int(v.elementLabel)
        if hasattr(v, "element") and v.element is not None:
            return int(v.element.label)
        if hasattr(v, "nodeLabel"):
            return int(v.nodeLabel)
        raise RuntimeError("Cannot resolve element label from field value")

    def _field_map(name, reduce_fn=None):
        if name not in keys:
            return {}
        fo = subset(name)
        out = {}
        try:
            blocks = fo.bulkDataBlocks
        except Exception:
            blocks = None
        if blocks:
            for block in blocks:
                try:
                    labels = block.elementLabels
                    data = block.data
                except Exception:
                    continue
                for i, lab in enumerate(labels):
                    lab = int(lab)
                    d = data[i]
                    if reduce_fn is not None:
                        out[lab] = reduce_fn(d)
                    else:
                        try:
                            out[lab] = float(d[0])
                        except Exception:
                            out[lab] = float(d)
            if out:
                return out
        for v in fo.values:
            lab = _elem_label(v)
            if reduce_fn is not None:
                out[lab] = reduce_fn(v.data)
            else:
                out[lab] = _scalar(v)
        return out

    miseseri_by = _field_map("MISESERI")
    misesavg_by = _field_map("MISESAVG")
    evol_by = _field_map("EVOL")
    vm_by = _field_map("S", reduce_fn=_von_mises)
    sdv15_by = _field_map("SDV15")

    nodes = {}
    for node in inst.nodes:
        nodes[int(node.label)] = (float(node.coordinates[0]), float(node.coordinates[1]))
    elements = {}
    for el in inst.elements:
        conn = [int(n) for n in el.connectivity]
        if len(conn) >= 4:
            elements[int(el.label)] = conn[:4]

    n_phys = len(miseseri_by)
    print("n_miseseri=", n_phys)
    aux_mode = bool(os.environ.get("MISESERI_AUX_CONTINUUM")) or (n_inst_el == n_phys)

    rows = []
    for lab in sorted(miseseri_by.keys()):
        conn = elements.get(lab)
        if not conn:
            continue
        pts = [nodes[n] for n in conn]
        xc = sum(p[0] for p in pts) / 4.0
        yc = sum(p[1] for p in pts) / 4.0
        if aux_mode:
            phys = lab
        else:
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

    metrics = quantify_miseseri_field(
        rows,
        target_disp=target_disp,
        target_tol=target_tol,
        disp_comp=disp_comp,
        rf_comp=rf_comp,
        u_final=u_final,
        rf_final=rf_final,
        expected_elements=3930,
    )

    tech = {
        "odb_path": odb_path,
        "step": step.name,
        "frame": len(step.frames) - 1,
        "field_present": present,
        "instance_elements": n_inst_el,
        "n_miseseri_values": n_phys,
        "mapping_layered_ok": (n_inst_el == 11790) or (n_inst_el == n_phys),
        "aux_continuum_mode": aux_mode,
    }
    tech.update(metrics)

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
