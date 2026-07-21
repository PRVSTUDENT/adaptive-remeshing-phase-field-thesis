#!/usr/bin/env python3
"""Compare refined C2F RF-U against frozen uniform H1 CSV.

Provisional Stage C scientific gates (peak / pre-peak):
  peak-force difference <= 2%
  initial stiffness difference <= 1%
  pre-peak RF-U NRMSE <= 2%
  peak displacement within one output interval of reference

Full/post-peak NRMSE are reported separately and do not auto-fail the peak gate.
"""

from __future__ import print_function

import argparse
import csv
import json
import math
import sys


def _open_text(path, mode="r"):
    if sys.version_info[0] >= 3:
        if "b" in mode:
            return open(path, mode)
        if "r" in mode:
            return open(path, mode, newline="")
        return open(path, mode, newline="\n")
    return open(path, mode)


def load_rfu(path):
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
    # unique by U
    seen = {}
    for u, f in rows:
        seen[round(u, 12)] = f
    return sorted(seen.items(), key=lambda t: t[0])


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


def peak(rows):
    return max(rows, key=lambda t: t[1])


def nrmse(ref, cand, u_lo=None, u_hi=None):
    refs = []
    for u, fr in ref:
        if u_lo is not None and u < u_lo - 1e-15:
            continue
        if u_hi is not None and u > u_hi + 1e-15:
            continue
        refs.append((u, fr))
    if len(refs) < 2:
        refs = list(ref)
    num = 0.0
    den = 0.0
    for u, fr in refs:
        fc = f_at(cand, u)
        num += (fc - fr) ** 2
        den += fr ** 2
    if den <= 0:
        return float("inf")
    return math.sqrt(num / den)


def initial_stiffness(rows, u_max=0.001):
    # least-squares through origin on 0 < U <= u_max
    pts = [(u, f) for u, f in rows if 0.0 < u <= u_max + 1e-15]
    if len(pts) < 2:
        pts = [(u, f) for u, f in rows if u > 0][:5]
    num = 0.0
    den = 0.0
    for u, f in pts:
        num += u * f
        den += u * u
    if den <= 0:
        return float("nan"), 0
    return num / den, len(pts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref-csv", required=True, help="H1 RF-U CSV")
    ap.add_argument("--cand-csv", required=True, help="C2F refined RF-U CSV")
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-csv", default=None)
    ap.add_argument("--out-md", default=None)
    ap.add_argument("--n-physical", type=int, default=10088)
    ap.add_argument("--n-physical-h1", type=int, default=12064)
    ap.add_argument("--walltime-s", type=float, default=None)
    ap.add_argument("--cputime-s", type=float, default=None)
    ap.add_argument("--mem-kb", type=float, default=None)
    args = ap.parse_args()

    ref = load_rfu(args.ref_csv)
    cand = load_rfu(args.cand_csv)

    u_ref_peak, f_ref_peak = peak(ref)
    u_c_peak, f_c_peak = peak(cand)
    rel_f = abs(f_c_peak - f_ref_peak) / abs(f_ref_peak) if f_ref_peak else float("inf")

    us = sorted(set(u for u, _ in ref))
    if len(us) >= 2:
        du = min(us[i + 1] - us[i] for i in range(len(us) - 1) if us[i + 1] > us[i])
    else:
        du = 1e-4
    u_ok = abs(u_c_peak - u_ref_peak) <= (du + 1e-12)

    k_ref, n_k_ref = initial_stiffness(ref, 0.001)
    k_c, n_k_c = initial_stiffness(cand, 0.001)
    rel_k = abs(k_c - k_ref) / abs(k_ref) if k_ref else float("inf")

    nrmse_pre = nrmse(ref, cand, None, u_ref_peak)
    nrmse_full = nrmse(ref, cand, None, None)
    nrmse_post = nrmse(ref, cand, u_ref_peak, None)

    peak_ok = rel_f <= 0.02
    stiff_ok = rel_k <= 0.01
    pre_ok = nrmse_pre <= 0.02
    sci_peak_pass = peak_ok and stiff_ok and pre_ok and u_ok

    if args.out_csv:
        with _open_text(args.out_csv, "w") as f:
            f.write("U2_H1,RF2_H1,RF2_C2F_interp,abs_diff,rel_diff\n")
            for u, fr in ref:
                fc = f_at(cand, u)
                ad = abs(fc - fr)
                rd = ad / abs(fr) if abs(fr) > 1e-30 else 0.0
                f.write("%.12g,%.12g,%.12g,%.12g,%.12g\n" % (u, fr, fc, ad, rd))

    elem_reduction = 1.0 - (args.n_physical / float(args.n_physical_h1))

    out = {
        "comparison": "C2F_v2_refined_vs_uniform_H1",
        "scientific_peak_prepeak_pass": sci_peak_pass,
        "gates": {
            "peak_force_rel_le_0.02": peak_ok,
            "initial_stiffness_rel_le_0.01": stiff_ok,
            "prepeak_nrmse_le_0.02": pre_ok,
            "peak_u_within_one_output_interval": u_ok,
        },
        "metrics": {
            "ref_peak_force": f_ref_peak,
            "cand_peak_force": f_c_peak,
            "rel_peak_force": rel_f,
            "ref_u_peak": u_ref_peak,
            "cand_u_peak": u_c_peak,
            "u_peak_tol": du,
            "ref_initial_stiffness": k_ref,
            "cand_initial_stiffness": k_c,
            "rel_initial_stiffness": rel_k,
            "n_stiffness_points_ref": n_k_ref,
            "n_stiffness_points_cand": n_k_c,
            "prepeak_nrmse": nrmse_pre,
            "full_curve_nrmse": nrmse_full,
            "postpeak_nrmse": nrmse_post,
            "n_ref": len(ref),
            "n_cand": len(cand),
            "cand_final_U": cand[-1][0] if cand else None,
            "cand_final_RF": cand[-1][1] if cand else None,
            "ref_final_U": ref[-1][0] if ref else None,
            "ref_final_RF": ref[-1][1] if ref else None,
        },
        "mesh": {
            "n_physical_refined": args.n_physical,
            "n_physical_H1": args.n_physical_h1,
            "n_layered_refined": args.n_physical * 3,
            "element_reduction_vs_H1": elem_reduction,
            "element_reduction_pct": 100.0 * elem_reduction,
        },
        "resources": {
            "walltime_s": args.walltime_s,
            "cputime_s": args.cputime_s,
            "mem_kb": args.mem_kb,
            "note": "H1 reference was serial; C2F used 4 threads. Do not attribute walltime solely to remeshing.",
        },
        "tolerances": {
            "rel_peak_force": 0.02,
            "rel_initial_stiffness": 0.01,
            "prepeak_nrmse": 0.02,
        },
    }

    if sci_peak_pass:
        classification = "stage_c_refined_response_supported"
    else:
        classification = "stage_c_technically_valid_response_deviation"
    out["stage_c_classification"] = classification

    with _open_text(args.out_json, "w") as f:
        f.write(json.dumps(out, indent=2, sort_keys=True) + "\n")

    if args.out_md:
        m = out["metrics"]
        lines = [
            "# C2F-v2 vs uniform H1 RF-U comparison",
            "",
            "## Classification",
            "",
            "`%s`" % classification,
            "",
            "## Peak / pre-peak gates",
            "",
            "| Metric | Value | Tol | Pass |",
            "| --- | ---: | ---: | --- |",
            "| Peak RF relative | %.4f%% | 2%% | %s |"
            % (100.0 * m["rel_peak_force"], peak_ok),
            "| Initial stiffness relative | %.4f%% | 1%% | %s |"
            % (100.0 * m["rel_initial_stiffness"], stiff_ok),
            "| Pre-peak NRMSE | %.4f%% | 2%% | %s |"
            % (100.0 * m["prepeak_nrmse"], pre_ok),
            "| Peak U within interval | ΔU=%.6g tol=%.6g | one frame | %s |"
            % (abs(m["cand_u_peak"] - m["ref_u_peak"]), m["u_peak_tol"], u_ok),
            "",
            "## Absolute peaks",
            "",
            "- H1 peak RF: **%.6g** at U=**%.6g**" % (m["ref_peak_force"], m["ref_u_peak"]),
            "- C2F peak RF: **%.6g** at U=**%.6g**" % (m["cand_peak_force"], m["cand_u_peak"]),
            "- H1 initial stiffness: **%.6g**" % m["ref_initial_stiffness"],
            "- C2F initial stiffness: **%.6g**" % m["cand_initial_stiffness"],
            "",
            "## Full / post-peak (reported, not gate)",
            "",
            "- Full-curve NRMSE: **%.4f%%**" % (100.0 * m["full_curve_nrmse"]),
            "- Post-peak NRMSE: **%.4f%%**" % (100.0 * m["postpeak_nrmse"]),
            "",
            "## Mesh economy",
            "",
            "- Physical elements: **%d** vs H1 **%d** (%.1f%% reduction)"
            % (
                args.n_physical,
                args.n_physical_h1,
                100.0 * elem_reduction,
            ),
            "- Layered elements: **%d**" % (args.n_physical * 3),
            "",
            "## Resources",
            "",
            "- Walltime: %s s" % args.walltime_s,
            "- CPU time: %s s" % args.cputime_s,
            "- Memory: %s kB" % args.mem_kb,
            "- Note: H1 serial vs C2F 4-thread; walltime not solely remeshing credit.",
            "",
        ]
        with _open_text(args.out_md, "w") as f:
            f.write("\n".join(lines) + "\n")

    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if sci_peak_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
