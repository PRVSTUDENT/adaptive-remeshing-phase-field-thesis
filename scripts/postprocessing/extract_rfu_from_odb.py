# Abaqus Python (2/3): extract RP RF2-U2 history from an ODB to plain CSV.
# Usage:
#   abaqus python extract_rfu_from_odb.py --odb path.odb --out path.csv
#
# No comparison logic. No newline= keyword (Abaqus-Python safe).
# Keep this file pure ASCII for Abaqus embedded Python 2.

from __future__ import print_function

import argparse
import sys


def extract_rfu(odb_path):
    from odbAccess import openOdb

    odb = openOdb(path=str(odb_path), readOnly=True)
    rp = None
    for name, ns in odb.rootAssembly.nodeSets.items():
        uname = str(name).upper()
        if uname == "RP" or uname.endswith(".RP") or uname.endswith("_RP"):
            rp = ns
            break
    if rp is None:
        # fallback: any set containing RP
        for name, ns in odb.rootAssembly.nodeSets.items():
            if "RP" in str(name).upper():
                rp = ns
                break
    if rp is None:
        odb.close()
        raise RuntimeError("RP node set not found in ODB")

    rows = []
    for step in odb.steps.values():
        for fr in step.frames:
            u_fo = fr.fieldOutputs["U"].getSubset(region=rp)
            rf_fo = fr.fieldOutputs["RF"].getSubset(region=rp)
            u = u_fo.values[0]
            rf = rf_fo.values[0]
            try:
                u2 = float(u.data[1])
                rf2 = float(rf.data[1])
            except Exception:
                u2 = float(u.data[0])
                rf2 = float(rf.data[0])
            rows.append((u2, abs(rf2)))
    odb.close()

    # unique, sorted by U
    seen = {}
    for u, f in rows:
        key = round(u, 12)
        seen[key] = f
    out = sorted(seen.items(), key=lambda t: t[0])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extract RP RF-U from ODB (Abaqus Python)")
    ap.add_argument("--odb", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    rows = extract_rfu(args.odb)
    # plain write, no newline= (Python 2 / Abaqus safe)
    fh = open(args.out, "w")
    try:
        fh.write("U2,RF2\n")
        for u, f in rows:
            fh.write("%.12g,%.12g\n" % (u, f))
    finally:
        fh.close()
    print("extracted_frames=%d out=%s" % (len(rows), args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
