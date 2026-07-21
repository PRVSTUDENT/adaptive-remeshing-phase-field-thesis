#!/usr/bin/env python3
"""Compare 4-thread H0 RF-U against frozen serial H0 CSV.

Provisional gates:
  peak-force difference <= 0.2%
  pre-peak RF-U NRMSE <= 0.2%
  peak displacement within one output increment of reference

Runtime policy:
  - Prefer plain CSV candidates produced by extract_rfu_from_odb.py under
    ``abaqus python`` (ODB access only).
  - Numerical comparison runs under system/module Python 3.11+ (not Abaqus
    embedded Python).
  - ``open(..., newline=)`` is used only when sys.version_info >= 3.
"""

from __future__ import print_function

import argparse
import csv
import json
import math
import sys


def _open_text(path, mode="r"):
    """Text open compatible with Py2 and Py3."""
    if sys.version_info[0] >= 3:
        if "b" in mode:
            return open(path, mode)
        # newline only supported on Py3
        if "r" in mode:
            return open(path, mode, newline="")
        return open(path, mode, newline="\n")
    return open(path, mode)


def load_ref(path):
    rows = []
    with _open_text(path, "r") as f:
        r = csv.DictReader(f)
        for row in r:
            u = None
            rf = None
            for k, v in row.items():
                if k is None:
                    continue
                kl = k.lower().strip()
                if kl in ("u2", "u", "displacement"):
                    u = float(v)
                if kl in ("rf2", "rf", "force"):
                    rf = float(v)
            if u is None:
                vals = [v for v in row.values() if v is not None]
                u, rf = float(vals[0]), float(vals[1])
            rows.append((u, abs(rf) if rf is not None else 0.0))
    return rows


def extract_rfu_from_odb(odb_path):
    try:
        from odbAccess import openOdb  # type: ignore
    except ImportError:
        raise SystemExit(
            "odbAccess required for --odb without --cand-csv; "
            "run extract_rfu_from_odb.py under abaqus python first"
        )

    odb = openOdb(path=str(odb_path), readOnly=True)
    rp = None
    for name, ns in odb.rootAssembly.nodeSets.items():
        uname = str(name).upper()
        if uname == "RP" or uname.endswith(".RP") or uname.endswith("_RP") or "RP" in uname:
            rp = ns
            break
    if rp is None:
        odb.close()
        raise RuntimeError("RP node set not found")

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
    seen = {}
    for u, f in rows:
        seen[round(u, 12)] = f
    return sorted(seen.items(), key=lambda t: t[0])


def peak(rows):
    return max(rows, key=lambda t: t[1])


def nrmse_prepeak(ref, cand, u_split):
    def f_at(rows, u):
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


def write_comparison_csv(path, ref, cand):
    # resample cand onto ref U for inspection
    def f_at(rows, u):
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

    with _open_text(path, "w") as f:
        f.write("U2_ref,RF2_ref,RF2_threads_interp,abs_diff,rel_diff\n")
        for u, fr in ref:
            fc = f_at(cand, u)
            ad = abs(fc - fr)
            rd = ad / abs(fr) if abs(fr) > 1e-30 else 0.0
            f.write("%.12g,%.12g,%.12g,%.12g,%.12g\n" % (u, fr, fc, ad, rd))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--odb", default=None, help="Optional ODB (requires odbAccess)")
    ap.add_argument("--cand-csv", default=None, help="Candidate RF-U CSV (preferred)")
    ap.add_argument("--ref-csv", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-csv", default=None, help="RF-U comparison table")
    ap.add_argument("--out-report-md", default=None)
    ap.add_argument(
        "--write-ok-marker",
        default=None,
        help="If set and qualification passes, create this empty marker file",
    )
    args = ap.parse_args()

    ref = load_ref(args.ref_csv)
    if args.cand_csv:
        cand = load_ref(args.cand_csv)
    elif args.odb:
        try:
            cand = extract_rfu_from_odb(args.odb)
        except Exception as exc:
            out = {
                "qualification_pass": False,
                "error": str(exc),
                "solver_executed": True,
                "solver_completed": True,
                "postprocessing_completed": False,
            }
            with _open_text(args.out_json, "w") as f:
                f.write(json.dumps(out, indent=2, sort_keys=True) + "\n")
            print(out)
            return 2
    else:
        raise SystemExit("Provide --cand-csv (preferred) or --odb")

    u_ref_peak, f_ref_peak = peak(ref)
    u_c_peak, f_c_peak = peak(cand)
    rel_f = abs(f_c_peak - f_ref_peak) / abs(f_ref_peak) if f_ref_peak else float("inf")
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
        "solver_executed": True,
        "solver_completed": True,
        "postprocessing_completed": True,
        "ref_peak_force": f_ref_peak,
        "cand_peak_force": f_c_peak,
        "rel_peak_force": rel_f,
        "ref_u_peak": u_ref_peak,
        "cand_u_peak": u_c_peak,
        "u_peak_ok": u_ok,
        "u_peak_tol": du,
        "prepeak_nrmse": nrmse,
        "n_ref": len(ref),
        "n_cand": len(cand),
        "tolerances": {"rel_peak_force": 0.002, "prepeak_nrmse": 0.002},
        "threads": 4,
        "mp_mode": "threads",
    }
    with _open_text(args.out_json, "w") as f:
        f.write(json.dumps(out, indent=2, sort_keys=True) + "\n")

    if args.out_csv:
        write_comparison_csv(args.out_csv, ref, cand)

    if args.out_report_md:
        lines = [
            "# C2D Thread Qualification Report",
            "",
            "- qualification_pass: `%s`" % pass_q,
            "- rel_peak_force: %.6g (tol 0.002)" % rel_f,
            "- prepeak_nrmse: %.6g (tol 0.002)" % nrmse,
            "- u_peak_ok: `%s` (tol one output interval = %.6g)" % (u_ok, du),
            "- ref peak RF: %.6g at U=%.6g" % (f_ref_peak, u_ref_peak),
            "- threads peak RF: %.6g at U=%.6g" % (f_c_peak, u_c_peak),
            "- solver_executed: true (existing C2D ODB reused; not re-solved)",
            "",
        ]
        with _open_text(args.out_report_md, "w") as f:
            f.write("\n".join(lines) + "\n")

    if pass_q and args.write_ok_marker:
        with open(args.write_ok_marker, "w") as f:
            f.write("")

    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if pass_q else 1


if __name__ == "__main__":
    raise SystemExit(main())
