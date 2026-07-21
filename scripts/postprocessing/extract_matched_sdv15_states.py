# Abaqus Python: extract SDV15 + element centroids at matched U states.
# ASCII-only. Usage:
#   abaqus python extract_matched_sdv15_states.py --odb PATH --label TAG --out-dir DIR

import argparse
import csv
import json
import os
import sys


def nearest_frame(odb, u_target):
    best = None
    best_du = 1e99
    rp = None
    for name, ns in odb.rootAssembly.nodeSets.items():
        if "RP" in str(name).upper():
            rp = ns
            break
    for step in odb.steps.values():
        for fr in step.frames:
            if rp is None or "U" not in fr.fieldOutputs:
                continue
            u = fr.fieldOutputs["U"].getSubset(region=rp).values[0]
            try:
                u2 = float(u.data[1])
            except Exception:
                u2 = float(u.data[0])
            du = abs(u2 - u_target)
            if du < best_du:
                best_du = du
                best = (step, fr, u2)
    return best, best_du


def element_centroid(inst, label):
    try:
        el = inst.getElementFromLabel(label)
        # average nodal coordinates
        coords = []
        for n in el.connectivity:
            # connectivity may be node labels
            try:
                nd = inst.getNodeFromLabel(n)
                coords.append(nd.coordinates)
            except Exception:
                pass
        if not coords:
            return None, None
        x = sum(c[0] for c in coords) / float(len(coords))
        y = sum(c[1] for c in coords) / float(len(coords))
        return x, y
    except Exception:
        return None, None


def extract_state(odb, u_target, out_csv):
    from odbAccess import openOdb

    # odb already open
    hit, du = nearest_frame(odb, u_target)
    if hit is None:
        return None
    step, fr, u2 = hit
    sdv_key = None
    for k in fr.fieldOutputs.keys():
        if str(k).upper() == "SDV15":
            sdv_key = k
            break
    if sdv_key is None:
        return {"U2": u2, "du": du, "error": "no_SDV15"}

    # prefer Part-1-1
    inst = None
    for name, i in odb.rootAssembly.instances.items():
        inst = i
        if "PART-1" in str(name).upper():
            break

    evol_fo = fr.fieldOutputs["EVOL"] if "EVOL" in fr.fieldOutputs else None
    rows = []
    for v in fr.fieldOutputs[sdv_key].values:
        try:
            s = float(v.data)
        except Exception:
            s = float(v.data[0])
        lab = int(v.elementLabel)
        x, y = element_centroid(inst, lab) if inst is not None else (None, None)
        area = ""
        if evol_fo is not None:
            try:
                ev = evol_fo.getSubset(region=v.instance.getElementFromLabel(lab)).values
                if ev:
                    area = float(ev[0].data)
            except Exception:
                area = ""
        rows.append((lab, x, y, s, area, 1 if s >= 0.5 else 0, 1 if s >= 0.95 else 0))

    fh = open(out_csv, "w")
    fh.write("element_label,centroid_x,centroid_y,SDV15,EVOL,flag_d_ge_0.5,flag_d_ge_0.95\n")
    for r in rows:
        fh.write("%s,%s,%s,%s,%s,%s,%s\n" % r)
    fh.close()

    vals = [r[3] for r in rows]
    summary = {
        "U_target": u_target,
        "U2_frame": u2,
        "du": du,
        "step": str(step.name),
        "frame": int(fr.frameId),
        "n": len(vals),
        "min": min(vals) if vals else None,
        "max": max(vals) if vals else None,
        "n_ge_0.5": sum(1 for v in vals if v >= 0.5),
        "n_ge_0.95": sum(1 for v in vals if v >= 0.95),
        "csv": out_csv,
    }
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--odb", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--u-targets", default="0.0040,0.0050,0.0058,0.0062,0.0070")
    args = ap.parse_args()

    from odbAccess import openOdb

    targets = [float(x) for x in args.u_targets.split(",") if x.strip()]
    out_dir = args.out_dir
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    odb = openOdb(path=str(args.odb), readOnly=True)
    summaries = []
    for u in targets:
        csv_path = os.path.join(out_dir, "SDV15_U_%s.csv" % str(u).replace(".", "p"))
        s = extract_state(odb, u, csv_path)
        summaries.append(s)
    odb.close()

    status = {
        "label": args.label,
        "odb": args.odb,
        "states": summaries,
        "classification": "matched_state_extraction_ok",
    }
    fh = open(os.path.join(out_dir, "EXTRACTION_SUMMARY.json"), "w")
    fh.write(json.dumps(status, indent=2, sort_keys=True) + "\n")
    fh.close()
    print(json.dumps({"label": args.label, "n_states": len(summaries)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
