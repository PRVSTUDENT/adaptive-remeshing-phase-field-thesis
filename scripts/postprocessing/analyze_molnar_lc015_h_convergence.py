#!/usr/bin/env python3
"""Numerical h-convergence comparison from CAE-exported RF-U CSVs.

Run only after Abaqus/CAE reports exist. This script does not open ODBs.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import math

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REF = ROOT / "references/derived/molnar_gravouil_2017/single_notch/fig7_lc015_corrected_origin/fig7_lc015_reference.csv"


def read_rf_u(path: Path) -> list[tuple[float, float]]:
    rows: list[tuple[float, float]] = []
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        u_key = next((k for k in fields if k.lower() in {"u2", "u_mm", "u"}), None)
        rf_key = next((k for k in fields if k.lower() in {"rf2", "rf_kn", "reaction_force_kn", "f"}), None)
        if u_key is None or rf_key is None:
            raise RuntimeError(f"Could not identify U/RF columns in {path}: {fields}")
        for row in reader:
            rows.append((float(row[u_key]), float(row[rf_key])))
    if not rows or abs(rows[0][0]) > 1e-12 or abs(rows[0][1]) > 1e-12:
        rows = [(0.0, 0.0)] + rows
    return rows


def interp(curve: list[tuple[float, float]], u: float) -> float:
    if u <= curve[0][0]:
        return curve[0][1]
    if u >= curve[-1][0]:
        return curve[-1][1]
    for (u0, f0), (u1, f1) in zip(curve, curve[1:]):
        if u0 <= u <= u1:
            if abs(u1 - u0) < 1e-16:
                return f0
            t = (u - u0) / (u1 - u0)
            return f0 + t * (f1 - f0)
    return curve[-1][1]


def peak(curve: list[tuple[float, float]]) -> tuple[float, float]:
    u_p, f_p = max(curve, key=lambda p: p[1])
    return f_p, u_p


def initial_stiffness(curve: list[tuple[float, float]]) -> float | None:
    for u, f in curve[1:]:
        if abs(u) > 1e-12:
            return f / u
    return None


def area(curve: list[tuple[float, float]]) -> float:
    total = 0.0
    for (u0, f0), (u1, f1) in zip(curve, curve[1:]):
        total += 0.5 * (f0 + f1) * (u1 - u0)
    return total


def nrmse(a: list[tuple[float, float]], b: list[tuple[float, float]], u_min: float | None = None, u_max: float | None = None) -> float:
    us = sorted({u for u, _ in a} | {u for u, _ in b})
    if u_min is not None:
        us = [u for u in us if u >= u_min - 1e-15]
    if u_max is not None:
        us = [u for u in us if u <= u_max + 1e-15]
    if len(us) < 2:
        return float("nan")
    err2 = 0.0
    ref2 = 0.0
    for u in us:
        fa = interp(a, u)
        fb = interp(b, u)
        err2 += (fa - fb) ** 2
        ref2 += fb ** 2
    rmse = math.sqrt(err2 / len(us))
    scale = math.sqrt(ref2 / len(us))
    return rmse / scale if scale > 1e-16 else rmse


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-root", default="runs/hpc/molnar_lc015_h_convergence")
    parser.add_argument("--reference", default=str(DEFAULT_REF))
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()
    study = Path(args.study_root)
    out = Path(args.out_dir) if args.out_dir else study / "comparison"
    out.mkdir(parents=True, exist_ok=True)

    case_paths = {
        "H0": study / "H0_exact",
        "H1": study / "H1_h0025",
        "H2-PUB": study / "H2_pub_h0010",
    }
    curves = {}
    case_rows = []
    for case, folder in case_paths.items():
        candidates = list(folder.rglob("*RF2_U2.csv")) + list(folder.rglob("*rf2_u2.csv"))
        if not candidates:
            case_rows.append([case, "missing_cae_csv", "", "", "", "", "", ""])
            continue
        curve = read_rf_u(candidates[0])
        curves[case] = curve
        pf, pu = peak(curve)
        case_rows.append(
            [
                case,
                "available",
                pf,
                pu,
                initial_stiffness(curve),
                area(curve),
                curve[-1][1],
                curve[-1][0],
            ]
        )

    write_csv(
        out / "h_convergence_case_metrics.csv",
        ["case", "status", "peak_RF2", "U2_at_peak", "initial_tangent_stiffness", "area_RF2_U2", "final_RF2", "final_U2"],
        case_rows,
    )

    successive = []
    pairs = [("H0", "H1"), ("H1", "H2-PUB")]
    for a, b in pairs:
        if a not in curves or b not in curves:
            successive.append([a, b, "missing_curve", "", "", "", "", ""])
            continue
        pa, ua = peak(curves[a])
        pb, ub = peak(curves[b])
        successive.append(
            [
                a,
                b,
                "compared",
                (pa - pb) / pb if abs(pb) > 1e-16 else "",
                (ua - ub) / ub if abs(ub) > 1e-16 else "",
                nrmse(curves[a], curves[b]),
                nrmse(curves[a], curves[b], u_max=min(ua, ub)),
                nrmse(curves[a], curves[b], u_min=max(ua, ub)),
            ]
        )
    write_csv(
        out / "h_convergence_successive_differences.csv",
        ["case_a", "case_b", "status", "rel_peak_RF2_change", "rel_peak_U2_change", "full_curve_nrmse", "prepeak_nrmse", "postpeak_nrmse"],
        successive,
    )

    ref_curve = None
    if Path(args.reference).exists():
        ref_curve = read_rf_u(Path(args.reference))
    ref_rows = []
    for case, curve in curves.items():
        if ref_curve is None:
            ref_rows.append([case, "reference_missing", "", "", ""])
            continue
        pf, pu = peak(curve)
        pr, ur = peak(ref_curve)
        ref_rows.append(
            [
                case,
                "compared_to_approximate_digitized_publication_reference",
                (pf - pr) / pr if abs(pr) > 1e-16 else "",
                (pu - ur) / ur if abs(ur) > 1e-16 else "",
                nrmse(curve, ref_curve),
            ]
        )
    write_csv(
        out / "h_convergence_reference_comparison.csv",
        ["case", "status", "rel_peak_RF2_error_vs_ref", "rel_peak_U2_error_vs_ref", "full_curve_nrmse_vs_ref"],
        ref_rows,
    )

    write_csv(
        out / "h_convergence_resource_scaling.csv",
        ["case", "physical_elements", "layered_elements", "runtime_s", "cpu_time_s", "memory_kb"],
        [[case, "", "", "", "", ""] for case in case_paths],
    )

    review = [
        "# H-Convergence Scientific Review",
        "",
        "Status: `h_convergence_scientific_review_pending`",
        "",
        "This file is a template filled after CAE exports exist for H0, H1 and H2-PUB.",
        "Main evidence is successive mesh change (H0 vs H1, H1 vs H2-PUB).",
        "Fig. 7 lc=0.015 comparison is approximate external evidence only.",
        "Do not claim convergence automatically because one metric is small.",
        "",
        "Thresholds: provisional descriptive metrics only.",
        "",
    ]
    (out / "H_CONVERGENCE_SCIENTIFIC_REVIEW.md").write_text("\n".join(review) + "\n", encoding="utf-8")

    # Optional plots if matplotlib is available and curves exist.
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        if curves:
            fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
            for case, curve in curves.items():
                ax.plot([p[0] for p in curve], [p[1] for p in curve], label=case)
            if ref_curve is not None:
                ax.plot([p[0] for p in ref_curve], [p[1] for p in ref_curve], "k--", label="Fig7 lc=0.015 approx")
            ax.set_xlabel("U2 [mm]")
            ax.set_ylabel("RF2 [kN]")
            ax.legend()
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            fig.savefig(out / "h_convergence_rf_u.png")
            plt.close(fig)

            hs = []
            peaks_f = []
            peaks_u = []
            labels = []
            for case, h in [("H0", 0.005), ("H1", 0.0025), ("H2-PUB", 0.001)]:
                if case in curves:
                    pf, pu = peak(curves[case])
                    hs.append(h)
                    peaks_f.append(pf)
                    peaks_u.append(pu)
                    labels.append(case)
            if hs:
                fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
                ax.plot(hs, peaks_f, "o-")
                ax.set_xlabel("target local h [mm]")
                ax.set_ylabel("peak RF2 [kN]")
                ax.invert_xaxis()
                fig.tight_layout()
                fig.savefig(out / "peak_force_vs_h.png")
                plt.close(fig)
                fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
                ax.plot(hs, peaks_u, "o-")
                ax.set_xlabel("target local h [mm]")
                ax.set_ylabel("U2 at peak [mm]")
                ax.invert_xaxis()
                fig.tight_layout()
                fig.savefig(out / "peak_displacement_vs_h.png")
                plt.close(fig)
            # runtime plot placeholder only when data later filled
            fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
            ax.set_xlabel("physical elements")
            ax.set_ylabel("runtime [s]")
            ax.set_title("runtime_vs_elements (pending job completion)")
            fig.tight_layout()
            fig.savefig(out / "runtime_vs_elements.png")
            plt.close(fig)
    except Exception as exc:
        (out / "plot_warning.txt").write_text(str(exc), encoding="utf-8")

    print(json.dumps({"out": str(out), "cases": list(curves.keys())}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
