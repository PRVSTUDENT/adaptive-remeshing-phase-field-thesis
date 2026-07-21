#!/usr/bin/env python3
"""Compare 4-thread H0 RF-U against frozen serial H0 CSV.

Provisional gates:
  peak-force difference <= 0.2%
  pre-peak RF-U NRMSE <= 0.2%
  peak displacement within one output increment of reference
"""

import argparse
import csv
import json
import math
import sys


def load_ref(path):
    rows = []
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            # flexible column names
            u = None
            rf = None
            for k, v in row.items():
                kl = k.lower()
                if kl in ("u2", "u", "displacement"):
                    u = float(v)
                if kl in ("rf2", "rf", "force"):
                    rf = float(v)
            if u is None:
                # try first two columns
                vals = list(row.values())
                u, rf = float(vals[0]), float(vals[1])
            rows.append((u, rf))
    return rows


def extract_rfu_from_odb(odb_path):
    # Prefer pre-exported CSV next to odb if present; else abaqus not available
    # This script is run after Abaqus; use odbAccess when available
    try:
        from odbAccess import openOdb
    except ImportError:
        raise SystemExit("odbAccess required (run with abaqus python or ensure Abaqus env)")

    odb = openOdb(path=odb_path, readOnly=True)
    # find RP
    rp = None
    for name, ns in odb.rootAssembly.nodeSets.items():
        if str(name).upper().endswith("RP") or str(name).upper() == "RP":
            rp = ns
            break
    rows = []
    for step in odb.steps.values():
        for fr in step.frames:
            u = fr.fieldOutputs["U"].getSubset(region=rp).values[0]
            rf = fr.fieldOutputs["RF"].getSubset(region=rp).values[0]
            try:
                u2 = float(u.data[1])
                rf2 = float(rf.data[1])
            except Exception:
                u2 = float(u.data[0])
                rf2 = float(rf.data[0])
            rows.append((u2, abs(rf2)))
    odb.close()
    # dedupe by U increasing
    rows = sorted(set((round(u, 12), r) for u, r in rows))
    return rows


def peak(rows):
    # max force and corresponding u
    best = max(rows, key=lambda t: t[1])
    return best  # u_peak, f_peak


def nrmse_prepeak(ref, cand, u_split):
    # interpolate cand force onto ref U grid for U <= u_split
    def f_at(rows, u):
        # linear interp
        if u <= rows[0][0]:
            return rows[0][1]
        if u >= rows[-1][0]:
            return rows[-1][1]
        for i in range(1, len(rows)):
            u0, f0 = rows[i - 1]
            u1, f1 = rows[i]
            if u0 <= u <= u1:
                if u1 == u0:
                    return f1
                t = (u - u0) / (u1 - u0)
                return f0 + t * (f1 - f0)
        return rows[-1][1]

    refs = [(u, f) for u, f in ref if u <= u_split + 1e-12]
    if len(refs) < 2:
        refs = ref
    num = 0.0
    den = 0.0
    for u, fr in refs:
        fc = f_at(cand, u)
        num += (fc - fr) ** 2
        den += fr ** 2
    if den <= 0:
        return float("inf")
    return math.sqrt(num / den)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--odb", required=True)
    ap.add_argument("--ref-csv", required=True)
    ap.add_argument("--out-json", required=True)
    args = ap.parse_args()

    ref = load_ref(args.ref_csv)
    # If run under system python without odbAccess, try abaqus python - already invoked after solve
    try:
        cand = extract_rfu_from_odb(args.odb)
    except Exception as exc:
        # write failure
        out = {"qualification_pass": False, "error": str(exc)}
        with open(args.out_json, "w") as f:
            json.dump(out, f, indent=2)
        print(out)
        return 2

    u_ref_peak, f_ref_peak = peak(ref)
    u_c_peak, f_c_peak = peak(cand)
    rel_f = abs(f_c_peak - f_ref_peak) / abs(f_ref_peak) if f_ref_peak else float("inf")
    # one output increment on ref grid
    us = sorted(set(u for u, _ in ref))
    if len(us) >= 2:
        du = min(us[i + 1] - us[i] for i in range(len(us) - 1) if us[i + 1] > us[i])
    else:
        du = 1e-4
    u_ok = abs(u_c_peak - u_ref_peak) <= (du + 1e-12)
    nrmse = nrmse_prepeak(ref, cand, u_ref_peak)

    pass_q = (rel_f <= 0.002) and (nrmse <= 0.002) and u_ok
    out = {
        "qualification_pass": pass_q,
        "ref_peak_force": f_ref_peak,
        "cand_peak_force": f_c_peak,
        "rel_peak_force": rel_f,
        "ref_u_peak": u_ref_peak,
        "cand_u_peak": u_c_peak,
        "u_peak_ok": u_ok,
        "prepeak_nrmse": nrmse,
        "n_ref": len(ref),
        "n_cand": len(cand),
        "tolerances": {"rel_peak_force": 0.002, "prepeak_nrmse": 0.002},
    }
    with open(args.out_json, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(out, indent=2))
    return 0 if pass_q else 1


if __name__ == "__main__":
    raise SystemExit(main())
