# Abaqus Python 2/3: check RF/U presence and SDV15 range on last frame.
# Pure ASCII. Usage: abaqus python check_odb_fields_abaqus.py --odb path --out json

from __future__ import print_function
import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--odb", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from odbAccess import openOdb

    odb = openOdb(path=str(args.odb), readOnly=True)
    step = list(odb.steps.values())[-1]
    fr = step.frames[-1]
    keys = list(fr.fieldOutputs.keys())
    out = {
        "step": str(step.name),
        "frame": int(fr.frameId),
        "fields": [str(k) for k in keys],
        "has_U": "U" in fr.fieldOutputs,
        "has_RF": "RF" in fr.fieldOutputs,
    }

    # Prefer SDV15 if present as separate field; else SDV component index 14
    sdv_key = None
    for k in keys:
        sk = str(k).upper()
        if sk == "SDV15":
            sdv_key = k
            break
    bad = 0
    n = 0
    mn = None
    mx = None
    n_ge_05 = 0
    n_ge_095 = 0
    if sdv_key is not None:
        for v in fr.fieldOutputs[sdv_key].values:
            data = v.data
            try:
                x = float(data)
            except Exception:
                x = float(data[0])
            n += 1
            if x != x or abs(x) == float("inf"):
                bad += 1
                continue
            if mn is None or x < mn:
                mn = x
            if mx is None or x > mx:
                mx = x
            if x >= 0.5:
                n_ge_05 += 1
            if x >= 0.95:
                n_ge_095 += 1
    out["sdv15"] = {
        "n": n,
        "bad": bad,
        "min": mn,
        "max": mx,
        "n_ge_0.5": n_ge_05,
        "n_ge_0.95": n_ge_095,
        "all_finite": bad == 0 and n > 0,
    }
    out["sdv_finite"] = bool(out["sdv15"]["all_finite"]) if n else None
    odb.close()

    fh = open(args.out, "w")
    fh.write(json.dumps(out, indent=2, sort_keys=True) + "\n")
    fh.close()
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
