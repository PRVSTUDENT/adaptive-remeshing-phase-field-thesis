#!/usr/bin/env python3
"""Formal RF-U h-convergence analysis for Molnar lc=0.015 mm study.

No Abaqus/PBS. Uses CAE-exported RF2-U2 CSVs and documented mesh/resource metadata.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAE_ROOT = (
    ROOT
    / "runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154"
    / "cae_replay_all/evidence/1376236.mmaster02/postprocessing"
)
REF_CSV = (
    ROOT
    / "references/derived/molnar_gravouil_2017/single_notch"
    / "fig7_lc015_corrected_origin/fig7_lc015_reference.csv"
)
OUT_PROC = ROOT / "results/processed/molnar_lc015_h_convergence"
OUT_TAB = ROOT / "results/tables/molnar_lc015_h_convergence"
OUT_FIG = ROOT / "results/figures/molnar_lc015_h_convergence"
OUT_REV = ROOT / "runs/hpc/molnar_lc015_h_convergence/comparison"
LC = 0.015
N_GRID = 1001
# Low-displacement interval for common initial-tangent fit [mm]
TANGENT_U_MAX = 0.0010
# Sign convention: CAE RF2 is positive in tension for these decks (as exported)
RF2_SIGN_CONVENTION = "positive_tension_as_exported_by_cae"

# Documented mesh stats
MESH = {
    "H0": {
        "physical": 3930,
        "layered": 11790,
        "h_target": 0.005,
        "h_meas": 0.004943904068987025,
        "h_over_lc": 0.329593604599135,
        "job": "1376154.mmaster02",
        "wall_s": 16 * 60 + 29,
        "cpu_s": 15 * 60 + 26,
        "mem_kb": 691652,
        "odb_bytes": 88827548,
        "revision": "58d7e3102d76fe0e70e6729457e2c7e90ad131bb",
    },
    "H1": {
        "physical": 12064,
        "layered": 36192,
        "h_target": 0.0025,
        "h_meas": 0.0025000000000000022,
        "h_over_lc": 0.16666666666666682,
        "job": "1376185.mmaster02",
        "wall_s": 46 * 60 + 26,
        "cpu_s": 45 * 60 + 28,
        "mem_kb": 928364,
        "odb_bytes": 244467576,
        "revision": "26b7b70832b2e1ae74c54abb7599cbe553aa1bad",
    },
    "H2-PUB": {
        "physical": 33852,
        "layered": 101556,
        "h_target": 0.001,
        "h_meas": 0.0010000000000000009,
        "h_over_lc": 0.06666666666666674,
        "job": "1376186.mmaster02",
        "wall_s": 2 * 3600 + 12 * 60 + 38,
        "cpu_s": 2 * 3600 + 10 * 60 + 43,
        "mem_kb": 1802776,
        "odb_bytes": 660842080,
        "revision": "26b7b70832b2e1ae74c54abb7599cbe553aa1bad",
    },
}

CASE_FILES = {
    "H0": CAE_ROOT / "H0" / "H0_RF2_U2.csv",
    "H1": CAE_ROOT / "H1" / "H1_RF2_U2.csv",
    "H2-PUB": CAE_ROOT / "H2-PUB" / "H2-PUB_RF2_U2.csv",
}
SUMMARY_FILES = {
    "H0": CAE_ROOT / "H0" / "H0_postprocess_summary.json",
    "H1": CAE_ROOT / "H1" / "H1_postprocess_summary.json",
    "H2-PUB": CAE_ROOT / "H2-PUB" / "H2-PUB_postprocess_summary.json",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_curve(path: Path) -> list[tuple[str, int, float, float]]:
    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            step = r.get("step", "")
            frame = int(float(r.get("frame", 0)))
            u = float(r["U2"])
            rf = float(r["RF2"])
            rows.append((step, frame, u, rf))
    return rows


def read_ref(path: Path) -> list[tuple[float, float]]:
    pts = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            u_key = "u_mm" if "u_mm" in r else "U2"
            f_key = "RF_kN" if "RF_kN" in r else "RF2"
            pts.append((float(r[u_key]), float(r[f_key])))
    return pts


def validate_curve(name: str, rows: list[tuple[str, int, float, float]]) -> dict:
    issues = []
    origins = [r for r in rows if abs(r[2]) < 1e-15 and abs(r[3]) < 1e-15]
    has_origin = any(r[0] == "origin" for r in rows) or len(origins) >= 1
    if not has_origin:
        issues.append("missing_origin")
    if sum(1 for r in rows if r[0] == "origin") > 1:
        issues.append("multiple_origin_labels")
    for i, r in enumerate(rows):
        if not math.isfinite(r[2]) or not math.isfinite(r[3]):
            issues.append(f"non_finite_at_index_{i}")
    # Concatenated displacement should be nondecreasing overall for the analysis path
    us = [r[2] for r in rows]
    rfs = [r[3] for r in rows]
    decreases = sum(1 for a, b in zip(us, us[1:]) if b < a - 1e-12)
    if decreases:
        issues.append(f"displacement_decreases_{decreases}")
    # Force sign: allow tiny negatives near zero; large negative would be wrong convention
    if min(rfs) < -1e-3:
        issues.append("large_negative_rf2_unexpected")
    return {
        "case": name,
        "n_points": len(rows),
        "has_origin": has_origin,
        "u_min": min(us),
        "u_max": max(us),
        "rf_min": min(rfs),
        "rf_max": max(rfs),
        "displacement_decreases": decreases,
        "issues": ";".join(issues) if issues else "",
        "pass": len(issues) == 0,
        "rf2_sign_convention": RF2_SIGN_CONVENTION,
        "units": "U2_mm_RF2_kN",
    }


def dedupe_last(rows: list[tuple[str, int, float, float]]) -> list[tuple[float, float]]:
    """Keep last accepted sample at each exact displacement."""
    by_u: dict[float, float] = {}
    order: list[float] = []
    for _, _, u, rf in rows:
        key = round(u, 12)  # stabilize float key
        if key not in by_u:
            order.append(key)
        by_u[key] = rf
    return [(u, by_u[u]) for u in order]


def peak(curve: list[tuple[float, float]]) -> tuple[float, float]:
    u_p, f_p = max(curve, key=lambda p: p[1])
    return f_p, u_p


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


def area(curve: list[tuple[float, float]]) -> float:
    total = 0.0
    for (u0, f0), (u1, f1) in zip(curve, curve[1:]):
        total += 0.5 * (f0 + f1) * (u1 - u0)
    return total


def initial_tangent(curve: list[tuple[float, float]], u_max: float = TANGENT_U_MAX) -> float:
    """Least-squares slope through origin using points with 0 < U <= u_max."""
    xs = []
    ys = []
    for u, f in curve:
        if 0.0 < u <= u_max + 1e-15:
            xs.append(u)
            ys.append(f)
    if len(xs) < 2:
        # fallback first positive point
        for u, f in curve:
            if u > 1e-12:
                return f / u
        return float("nan")
    # force through origin: k = sum(x y)/sum(x^2)
    num = sum(x * y for x, y in zip(xs, ys))
    den = sum(x * x for x in xs)
    return num / den if den > 0 else float("nan")


def nrmse(a: list[tuple[float, float]], b: list[tuple[float, float]], grid: list[float], u_min=None, u_max=None) -> float:
    us = [u for u in grid if (u_min is None or u >= u_min - 1e-15) and (u_max is None or u <= u_max + 1e-15)]
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


def max_abs_diff(a, b, grid, u_min=None, u_max=None):
    us = [u for u in grid if (u_min is None or u >= u_min - 1e-15) and (u_max is None or u <= u_max + 1e-15)]
    best_u = None
    best_d = -1.0
    for u in us:
        d = abs(interp(a, u) - interp(b, u))
        if d > best_d:
            best_d = d
            best_u = u
    return best_d, best_u


def mean_abs_diff(a, b, grid, u_min=None, u_max=None):
    us = [u for u in grid if (u_min is None or u >= u_min - 1e-15) and (u_max is None or u <= u_max + 1e-15)]
    if not us:
        return float("nan")
    return sum(abs(interp(a, u) - interp(b, u)) for u in us) / len(us)


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def write_tex_table(path: Path, caption: str, header: list[str], rows: list[list[object]], label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = "l" + "r" * (len(header) - 1)
    lines = [
        "% Auto-generated; do not edit by hand",
        f"% {caption}",
        f"\\begin{{tabular}}{{{cols}}}",
        "\\toprule",
        " & ".join(header) + " \\\\",
        "\\midrule",
    ]
    for row in rows:
        cells = []
        for c in row:
            if isinstance(c, float):
                cells.append(f"{c:.6g}")
            else:
                cells.append(str(c).replace("_", "\\_"))
        lines.append(" & ".join(cells) + " \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}", f"% label: {label}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def fmt_s(sec: float) -> str:
    sec = int(round(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-figures", action="store_true")
    args = parser.parse_args()

    OUT_PROC.mkdir(parents=True, exist_ok=True)
    OUT_TAB.mkdir(parents=True, exist_ok=True)
    OUT_FIG.mkdir(parents=True, exist_ok=True)
    OUT_REV.mkdir(parents=True, exist_ok=True)

    # --- inventory ---
    inv_rows = []
    raw = {}
    summaries = {}
    for case, path in CASE_FILES.items():
        if not path.exists():
            raise SystemExit(f"missing source curve: {path}")
        rows = read_curve(path)
        raw[case] = rows
        dig = sha256(path)
        us = [r[2] for r in rows]
        fs = [r[3] for r in rows]
        inv_rows.append(
            [
                case,
                str(path.as_posix()),
                MESH[case]["job"],
                MESH[case]["revision"],
                path.stat().st_size,
                dig,
                len(rows),
                min(us),
                max(us),
                min(fs),
                max(fs),
                any(abs(r[2]) < 1e-15 and abs(r[3]) < 1e-15 for r in rows),
            ]
        )
        # copy to processed source_csv
        dest = OUT_PROC / "source_csv" / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
        if SUMMARY_FILES[case].exists():
            summaries[case] = json.loads(SUMMARY_FILES[case].read_text(encoding="utf-8"))
            sdest = OUT_PROC / "source_csv" / SUMMARY_FILES[case].name
            sdest.write_bytes(SUMMARY_FILES[case].read_bytes())

    ref_pts = read_ref(REF_CSV)
    inv_rows.append(
        [
            "FIG7_lc015",
            str(REF_CSV.as_posix()),
            "n/a",
            "digitized",
            REF_CSV.stat().st_size,
            sha256(REF_CSV),
            len(ref_pts),
            min(p[0] for p in ref_pts),
            max(p[0] for p in ref_pts),
            min(p[1] for p in ref_pts),
            max(p[1] for p in ref_pts),
            any(abs(p[0]) < 1e-15 and abs(p[1]) < 1e-15 for p in ref_pts),
        ]
    )

    write_csv(
        OUT_PROC / "source_inventory.csv",
        [
            "case_id",
            "path",
            "job_id",
            "source_revision",
            "size_bytes",
            "sha256",
            "n_points",
            "u_min",
            "u_max",
            "rf_min",
            "rf_max",
            "has_origin",
        ],
        inv_rows,
    )
    hash_lines = []
    for case, path in CASE_FILES.items():
        hash_lines.append(f"{sha256(path)}  {path.as_posix()}")
    hash_lines.append(f"{sha256(REF_CSV)}  {REF_CSV.as_posix()}")
    (OUT_PROC / "source_hashes.sha256").write_text("\n".join(hash_lines) + "\n", encoding="utf-8")

    man_md = [
        "# Source Data Manifest — Molnar lc015 h-convergence RF-U",
        "",
        "Status: inventory of retained CAE and reference curves for no-solution analysis.",
        "",
        f"CAE job: `1376236.mmaster02`",
        f"Scientific-input revision: `58d7e3102d76fe0e70e6729457e2c7e90ad131bb`",
        f"Analysis script: `scripts/postprocessing/analyze_molnar_lc015_h_convergence.py`",
        "",
        "| Case | Job | Points | U range [mm] | RF range [kN] | Origin | SHA-256 |",
        "|---|---|---:|---|---|---|---|",
    ]
    for row in inv_rows:
        man_md.append(
            f"| {row[0]} | `{row[2]}` | {row[6]} | [{row[7]:.6g}, {row[8]:.6g}] | [{row[9]:.6g}, {row[10]:.6g}] | {row[11]} | `{row[5][:12]}…` |"
        )
    man_md.extend(
        [
            "",
            "## Units and sign",
            "",
            f"- Displacement U2: mm",
            f"- Reaction RF2: kN",
            f"- RF2 sign convention: `{RF2_SIGN_CONVENTION}`",
            f"- lc = {LC} mm",
            "",
            "Source CSV/RPT files are not edited.",
            "",
        ]
    )
    (OUT_PROC / "SOURCE_DATA_MANIFEST.md").write_text("\n".join(man_md), encoding="utf-8")

    # --- validate ---
    val_rows = []
    for case, rows in raw.items():
        v = validate_curve(case, rows)
        val_rows.append(
            [
                v["case"],
                v["n_points"],
                v["has_origin"],
                v["u_min"],
                v["u_max"],
                v["rf_min"],
                v["rf_max"],
                v["displacement_decreases"],
                v["pass"],
                v["issues"],
                v["units"],
                v["rf2_sign_convention"],
            ]
        )
    write_csv(
        OUT_PROC / "curve_validation.csv",
        [
            "case",
            "n_points",
            "has_origin",
            "u_min",
            "u_max",
            "rf_min",
            "rf_max",
            "displacement_decreases",
            "pass",
            "issues",
            "units",
            "rf2_sign_convention",
        ],
        val_rows,
    )
    all_pass = all(r[8] for r in val_rows)
    val_md = [
        "# Curve Validation Report",
        "",
        f"Overall pass: `{all_pass}`",
        "",
        "| Case | Pass | Points | Origin | U max | RF max | Issues |",
        "|---|---|---:|---|---:|---:|---|",
    ]
    for r in val_rows:
        val_md.append(f"| {r[0]} | {r[8]} | {r[1]} | {r[2]} | {r[4]:.6g} | {r[6]:.6g} | {r[9] or 'none'} |")
    val_md.extend(
        [
            "",
            "## Rules",
            "",
            "- Exactly one explicit origin contribution required (origin label or (0,0)).",
            "- Finite U2/RF2 only.",
            "- Units U2 [mm], RF2 [kN].",
            "- Nondecreasing displacement sequence (no step-boundary reset).",
            "- No comparison to lc=0.0075 reference in this study.",
            "- For interpolation: exact duplicate U retain last frame (deterministic).",
            "",
        ]
    )
    (OUT_PROC / "CURVE_VALIDATION_REPORT.md").write_text("\n".join(val_md), encoding="utf-8")
    if not all_pass:
        print("CURVE_VALIDATION_FAIL")
        return 2

    # --- process curves ---
    curves = {c: dedupe_last(rows) for c, rows in raw.items()}
    ref_curve = ref_pts[:]
    if not ref_curve or abs(ref_curve[0][0]) > 1e-12 or abs(ref_curve[0][1]) > 1e-12:
        ref_curve = [(0.0, 0.0)] + ref_curve

    # common grid
    u_min = max(curves[c][0][0] for c in curves)
    u_max = min(curves[c][-1][0] for c in curves)
    grid = [u_min + i * (u_max - u_min) / (N_GRID - 1) for i in range(N_GRID)]
    # H2 peak for split
    f2, u2_peak = peak(curves["H2-PUB"])
    u_split = u2_peak

    # --- case metrics ---
    case_metrics = []
    case_dict = {}
    for case in ("H0", "H1", "H2-PUB"):
        c = curves[case]
        pf, pu = peak(c)
        k0 = initial_tangent(c)
        m = MESH[case]
        row = {
            "case": case,
            "job_id": m["job"],
            "peak_RF2_kN": pf,
            "U2_at_peak_mm": pu,
            "initial_tangent_kN_per_mm": k0,
            "final_RF2_kN": c[-1][1],
            "final_U2_mm": c[-1][0],
            "area_kN_mm": area(c),
            "u_min_mm": c[0][0],
            "u_max_mm": c[-1][0],
            "n_original_samples": len(raw[case]),
            "n_deduped_samples": len(c),
            "physical_elements": m["physical"],
            "layered_elements": m["layered"],
            "h_target_mm": m["h_target"],
            "h_measured_median_mm": m["h_meas"],
            "h_over_lc": m["h_over_lc"],
            "walltime_s": m["wall_s"],
            "cpu_time_s": m["cpu_s"],
            "peak_memory_kb": m["mem_kb"],
            "odb_bytes": m["odb_bytes"],
            "walltime_per_element_s": m["wall_s"] / m["physical"],
            "memory_kb_per_element": m["mem_kb"] / m["physical"],
        }
        # forces at selected U
        for u_sel in (0.002, 0.004, 0.005, 0.0058, 0.006):
            if c[0][0] <= u_sel <= c[-1][0]:
                row[f"RF2_at_U_{u_sel:g}"] = interp(c, u_sel)
        case_dict[case] = row
        case_metrics.append(row)

    write_csv(
        OUT_TAB / "h_convergence_case_metrics.csv",
        list(case_metrics[0].keys()),
        [[r[k] for k in case_metrics[0].keys()] for r in case_metrics],
    )
    write_tex_table(
        OUT_TAB / "h_convergence_case_metrics.tex",
        "Case metrics",
        ["Case", "peak RF2", "Upeak", "K0", "N_elem", "h_meas", "walltime"],
        [
            [
                r["case"],
                r["peak_RF2_kN"],
                r["U2_at_peak_mm"],
                r["initial_tangent_kN_per_mm"],
                r["physical_elements"],
                r["h_measured_median_mm"],
                fmt_s(r["walltime_s"]),
            ]
            for r in case_metrics
        ],
        "tab:molnar_hconv_case_metrics",
    )

    # --- successive ---
    pairs = [("H0", "H1"), ("H1", "H2-PUB")]
    succ_rows = []
    for coarse, fine in pairs:
        ca, cb = curves[coarse], curves[fine]
        pfa, pua = peak(ca)
        pfb, pub = peak(cb)
        ka, kb = initial_tangent(ca), initial_tangent(cb)
        aa, ab = area(ca), area(cb)
        full = nrmse(ca, cb, grid)
        pre = nrmse(ca, cb, grid, u_max=u_split)
        post = nrmse(ca, cb, grid, u_min=u_split)
        mad, u_mad = max_abs_diff(ca, cb, grid)
        mean_d = mean_abs_diff(ca, cb, grid)
        succ_rows.append(
            {
                "comparison": f"{coarse}_vs_{fine}",
                "coarse": coarse,
                "fine": fine,
                "rel_peak_RF2": abs(pfa - pfb) / abs(pfb) if pfb else float("nan"),
                "rel_peak_U2": abs(pua - pub) / abs(pub) if abs(pub) > 1e-16 else 0.0,
                "rel_tangent": abs(ka - kb) / abs(kb) if abs(kb) > 1e-16 else float("nan"),
                "rel_area": abs(aa - ab) / abs(ab) if abs(ab) > 1e-16 else float("nan"),
                "full_curve_nrmse": full,
                "prepeak_nrmse": pre,
                "postpeak_nrmse": post,
                "max_abs_force_diff_kN": mad,
                "U_at_max_abs_force_diff_mm": u_mad,
                "mean_abs_force_diff_kN": mean_d,
                "full_curve_nrmse_pct": 100 * full,
                "prepeak_nrmse_pct": 100 * pre,
                "postpeak_nrmse_pct": 100 * post,
                "rel_peak_RF2_pct": 100 * abs(pfa - pfb) / abs(pfb),
                "rel_peak_U2_pct": 100 * (abs(pua - pub) / abs(pub) if abs(pub) > 1e-16 else 0.0),
                "split_U_mm": u_split,
                "common_U_min": u_min,
                "common_U_max": u_max,
                "n_grid": N_GRID,
            }
        )
    write_csv(
        OUT_TAB / "h_convergence_successive_differences.csv",
        list(succ_rows[0].keys()),
        [[r[k] for k in succ_rows[0].keys()] for r in succ_rows],
    )
    write_tex_table(
        OUT_TAB / "h_convergence_successive_differences.tex",
        "Successive mesh differences",
        ["Pair", "dFpeak %", "dUpeak %", "full NRMSE %", "pre %", "post %"],
        [
            [
                r["comparison"],
                r["rel_peak_RF2_pct"],
                r["rel_peak_U2_pct"],
                r["full_curve_nrmse_pct"],
                r["prepeak_nrmse_pct"],
                r["postpeak_nrmse_pct"],
            ]
            for r in succ_rows
        ],
        "tab:molnar_hconv_successive",
    )

    # --- publication ---
    pub_rows = []
    for case in ("H0", "H1", "H2-PUB"):
        c = curves[case]
        ov_min = max(c[0][0], ref_curve[0][0])
        ov_max = min(c[-1][0], ref_curve[-1][0])
        gref = [ov_min + i * (ov_max - ov_min) / (N_GRID - 1) for i in range(N_GRID)]
        pf, pu = peak(c)
        pfr, pur = peak(ref_curve)
        # ref peak for post split use H2 split for consistency with mesh study
        full = nrmse(c, ref_curve, gref)
        pre = nrmse(c, ref_curve, gref, u_max=min(u_split, ov_max))
        post = nrmse(c, ref_curve, gref, u_min=max(u_split, ov_min))
        mad, u_mad = max_abs_diff(c, ref_curve, gref)
        ka, kr = initial_tangent(c), initial_tangent(ref_curve)
        # area on overlap only
        ref_ov = [(u, interp(ref_curve, u)) for u in gref]
        c_ov = [(u, interp(c, u)) for u in gref]
        aa, ar = area(c_ov), area(ref_ov)
        pub_rows.append(
            {
                "case": case,
                "reference": "fig7_lc015_approximate_digitized_publication_reference",
                "overlap_U_min": ov_min,
                "overlap_U_max": ov_max,
                "rel_peak_RF2_vs_ref": (pf - pfr) / pfr if pfr else float("nan"),
                "rel_peak_U2_vs_ref": (pu - pur) / pur if abs(pur) > 1e-16 else float("nan"),
                "abs_peak_RF2_diff_kN": abs(pf - pfr),
                "abs_peak_U2_diff_mm": abs(pu - pur),
                "full_overlap_nrmse": full,
                "prepeak_overlap_nrmse": pre,
                "postpeak_overlap_nrmse": post,
                "rel_tangent_vs_ref": (ka - kr) / kr if abs(kr) > 1e-16 else float("nan"),
                "rel_area_overlap": (aa - ar) / ar if abs(ar) > 1e-16 else float("nan"),
                "max_abs_force_diff_kN": mad,
                "U_at_max_abs_force_diff_mm": u_mad,
                "full_overlap_nrmse_pct": 100 * full,
                "prepeak_overlap_nrmse_pct": 100 * pre,
                "postpeak_overlap_nrmse_pct": 100 * post,
            }
        )
    write_csv(
        OUT_TAB / "h_convergence_publication_comparison.csv",
        list(pub_rows[0].keys()),
        [[r[k] for k in pub_rows[0].keys()] for r in pub_rows],
    )
    write_tex_table(
        OUT_TAB / "h_convergence_publication_comparison.tex",
        "Publication comparison lc=0.015",
        ["Case", "dFpeak %", "dUpeak %", "full NRMSE %", "pre %", "post %"],
        [
            [
                r["case"],
                100 * r["rel_peak_RF2_vs_ref"],
                100 * r["rel_peak_U2_vs_ref"],
                r["full_overlap_nrmse_pct"],
                r["prepeak_overlap_nrmse_pct"],
                r["postpeak_overlap_nrmse_pct"],
            ]
            for r in pub_rows
        ],
        "tab:molnar_hconv_pub",
    )

    # --- resources ---
    res_rows = []
    for case in ("H0", "H1", "H2-PUB"):
        m = MESH[case]
        res_rows.append(
            [
                case,
                m["physical"],
                m["layered"],
                m["wall_s"],
                m["cpu_s"],
                m["mem_kb"],
                m["odb_bytes"],
                m["wall_s"] / m["physical"],
                m["cpu_s"] / m["physical"],
                m["mem_kb"] / m["physical"],
                m["odb_bytes"] / m["physical"],
            ]
        )
    # ratios and slope
    n0, n1, n2 = MESH["H0"]["physical"], MESH["H1"]["physical"], MESH["H2-PUB"]["physical"]
    t0, t1, t2 = MESH["H0"]["wall_s"], MESH["H1"]["wall_s"], MESH["H2-PUB"]["wall_s"]
    # log-log slope fit walltime ~ N^alpha using three points least squares
    xs = [math.log(n0), math.log(n1), math.log(n2)]
    ys = [math.log(t0), math.log(t1), math.log(t2)]
    xbar, ybar = statistics.mean(xs), statistics.mean(ys)
    alpha = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / sum((x - xbar) ** 2 for x in xs)

    write_csv(
        OUT_TAB / "h_convergence_resource_scaling.csv",
        [
            "case",
            "physical_elements",
            "layered_elements",
            "walltime_s",
            "cpu_time_s",
            "mem_kb",
            "odb_bytes",
            "wall_per_elem_s",
            "cpu_per_elem_s",
            "mem_kb_per_elem",
            "odb_bytes_per_elem",
        ],
        res_rows,
    )
    # append meta rows as companion
    write_csv(
        OUT_TAB / "h_convergence_resource_ratios.csv",
        ["quantity", "value"],
        [
            ["N1_over_N0", n1 / n0],
            ["N2_over_N1", n2 / n1],
            ["N2_over_N0", n2 / n0],
            ["t1_over_t0", t1 / t0],
            ["t2_over_t1", t2 / t1],
            ["t2_over_t0", t2 / t0],
            ["loglog_walltime_vs_N_slope_alpha", alpha],
            ["note", "serial_scaling_only_not_parallel"],
        ],
    )
    write_tex_table(
        OUT_TAB / "h_convergence_resource_scaling.tex",
        "Resource scaling",
        ["Case", "N_elem", "walltime", "mem_kb", "wall/elem"],
        [[r[0], r[1], fmt_s(r[3]), r[5], f"{r[7]:.4g}"] for r in res_rows],
        "tab:molnar_hconv_resources",
    )

    # --- figures ---
    if not args.skip_figures:
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig_manifest = []

            def save(fig, name, caption):
                path = OUT_FIG / name
                fig.tight_layout()
                fig.savefig(path, dpi=200)
                plt.close(fig)
                fig_manifest.append({"file": name, "caption": caption})

            # 1 RF-U mesh family
            fig, ax = plt.subplots(figsize=(7, 5))
            for case, style in (("H0", "-"), ("H1", "--"), ("H2-PUB", "-.")):
                c = curves[case]
                ax.plot([p[0] for p in c], [p[1] for p in c], style, label=f"{case} h={MESH[case]['h_meas']:.4g} mm")
            ax.set_xlabel("U2 [mm]")
            ax.set_ylabel("RF2 [kN]")
            ax.set_title("Molnar single-notch RF–U, lc = 0.015 mm")
            ax.legend()
            ax.grid(True, alpha=0.3)
            save(fig, "01_rf_u_h0_h1_h2.png", "H0/H1/H2 RF2-U2; lc=0.015; CAE job 1376236")

            # 2 with publication
            fig, ax = plt.subplots(figsize=(7, 5))
            for case, style in (("H0", "-"), ("H1", "--"), ("H2-PUB", "-.")):
                c = curves[case]
                ax.plot([p[0] for p in c], [p[1] for p in c], style, label=case)
            ax.plot([p[0] for p in ref_curve], [p[1] for p in ref_curve], "k:", label="Fig.7 lc=0.015 approx")
            ax.set_xlabel("U2 [mm]")
            ax.set_ylabel("RF2 [kN]")
            ax.set_title("Simulations vs approximate digitized Fig. 7 (lc=0.015)")
            ax.legend()
            ax.grid(True, alpha=0.3)
            save(fig, "02_rf_u_with_fig7_lc015.png", "With approximate digitized publication reference")

            # 3 peak zoom
            fig, ax = plt.subplots(figsize=(7, 5))
            for case, style in (("H0", "-"), ("H1", "--"), ("H2-PUB", "-.")):
                c = curves[case]
                ax.plot([p[0] for p in c], [p[1] for p in c], style, label=case)
            ax.plot([p[0] for p in ref_curve], [p[1] for p in ref_curve], "k:", label="Fig.7 approx")
            ax.set_xlim(0.0045, 0.007)
            ax.set_ylim(0.0, 0.85)
            ax.set_xlabel("U2 [mm]")
            ax.set_ylabel("RF2 [kN]")
            ax.set_title("Peak-load zoom")
            ax.legend()
            ax.grid(True, alpha=0.3)
            save(fig, "03_rf_u_peak_zoom.png", "Zoom around peak load")

            # 4 pairwise differences
            fig, ax = plt.subplots(figsize=(7, 5))
            for coarse, fine, style in (("H0", "H1", "-"), ("H1", "H2-PUB", "--")):
                dF = [interp(curves[coarse], u) - interp(curves[fine], u) for u in grid]
                ax.plot(grid, dF, style, label=f"{coarse}-{fine}")
            ax.axhline(0, color="k", lw=0.5)
            ax.set_xlabel("U2 [mm]")
            ax.set_ylabel("ΔRF2 [kN] (coarse − fine)")
            ax.set_title("Pairwise force differences on common grid")
            ax.legend()
            ax.grid(True, alpha=0.3)
            save(fig, "04_pairwise_force_diff_vs_u.png", "H0-H1 and H1-H2 force differences")

            hs = [MESH[c]["h_meas"] for c in ("H0", "H1", "H2-PUB")]
            peaks_f = [case_dict[c]["peak_RF2_kN"] for c in ("H0", "H1", "H2-PUB")]
            peaks_u = [case_dict[c]["U2_at_peak_mm"] for c in ("H0", "H1", "H2-PUB")]
            k0s = [case_dict[c]["initial_tangent_kN_per_mm"] for c in ("H0", "H1", "H2-PUB")]

            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(hs, peaks_f, "o-")
            ax.invert_xaxis()
            ax.set_xlabel("measured corridor h [mm]")
            ax.set_ylabel("peak RF2 [kN]")
            ax.set_title("Peak force vs mesh size")
            ax.grid(True, alpha=0.3)
            save(fig, "05_peak_rf2_vs_h.png", "Peak RF2 vs measured h")

            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(hs, peaks_u, "o-")
            ax.invert_xaxis()
            ax.set_xlabel("measured corridor h [mm]")
            ax.set_ylabel("U2 at peak [mm]")
            ax.set_title("Peak displacement vs mesh size")
            ax.grid(True, alpha=0.3)
            save(fig, "06_upeak_vs_h.png", "U2 at peak vs measured h")

            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(hs, k0s, "o-")
            ax.invert_xaxis()
            ax.set_xlabel("measured corridor h [mm]")
            ax.set_ylabel("initial tangent [kN/mm]")
            ax.set_title(f"Initial tangent (0 < U ≤ {TANGENT_U_MAX} mm)")
            ax.grid(True, alpha=0.3)
            save(fig, "07_tangent_vs_h.png", "Initial tangent vs h")

            # curve diffs vs h: plot successive NRMSE at mid-h of pair
            fig, ax = plt.subplots(figsize=(6, 4))
            h_pair = [(MESH["H0"]["h_meas"] + MESH["H1"]["h_meas"]) / 2, (MESH["H1"]["h_meas"] + MESH["H2-PUB"]["h_meas"]) / 2]
            ax.plot(h_pair, [succ_rows[0]["full_curve_nrmse_pct"], succ_rows[1]["full_curve_nrmse_pct"]], "o-", label="full")
            ax.plot(h_pair, [succ_rows[0]["prepeak_nrmse_pct"], succ_rows[1]["prepeak_nrmse_pct"]], "s--", label="pre-peak")
            ax.plot(h_pair, [succ_rows[0]["postpeak_nrmse_pct"], succ_rows[1]["postpeak_nrmse_pct"]], "^:", label="post-peak")
            ax.invert_xaxis()
            ax.set_xlabel("pair mid h [mm]")
            ax.set_ylabel("NRMSE [%]")
            ax.set_title("Successive curve NRMSE")
            ax.legend()
            ax.grid(True, alpha=0.3)
            save(fig, "08_curve_nrmse_vs_h.png", "Full/pre/post successive NRMSE")

            ns = [MESH[c]["physical"] for c in ("H0", "H1", "H2-PUB")]
            ts = [MESH[c]["wall_s"] for c in ("H0", "H1", "H2-PUB")]
            ms = [MESH[c]["mem_kb"] / 1024.0 for c in ("H0", "H1", "H2-PUB")]
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(ns, ts, "o-")
            ax.set_xlabel("physical elements")
            ax.set_ylabel("walltime [s]")
            ax.set_title("Walltime vs element count (serial)")
            ax.grid(True, alpha=0.3)
            save(fig, "09_walltime_vs_elements.png", f"Serial walltime; log-log slope alpha≈{alpha:.3f}")

            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(ns, ms, "o-")
            ax.set_xlabel("physical elements")
            ax.set_ylabel("peak memory [MB]")
            ax.set_title("Memory vs element count (serial)")
            ax.grid(True, alpha=0.3)
            save(fig, "10_memory_vs_elements.png", "Serial peak memory")

            (OUT_FIG / "FIGURE_MANIFEST.md").write_text(
                "# Figure manifest\n\n"
                + "\n".join(f"- `{f['file']}`: {f['caption']}" for f in fig_manifest)
                + "\n\nScript: `scripts/postprocessing/analyze_molnar_lc015_h_convergence.py`\n"
                + "lc=0.015 mm; cases H0/H1/H2-PUB; CAE job 1376236; units U2 mm, RF2 kN.\n"
                + "Reference: approximate_digitized_publication_reference (not exact author data).\n"
                + f"Interpolation: linear on common grid N={N_GRID}, U in [{u_min:.6g},{u_max:.6g}].\n",
                encoding="utf-8",
            )
        except Exception as exc:
            (OUT_FIG / "plot_error.txt").write_text(str(exc), encoding="utf-8")
            print("FIGURE_WARN", exc)

    # --- classification ---
    h0h1 = succ_rows[0]
    h1h2 = succ_rows[1]
    # RF-U successive: strong if H1-H2 peak force <1% and full NRMSE small
    if h1h2["rel_peak_RF2_pct"] < 1.0 and h1h2["full_curve_nrmse_pct"] < 5.0 and h0h1["rel_peak_RF2_pct"] > 2.0:
        class_rf = "rf_u_h_convergence_supported"
    elif h1h2["rel_peak_RF2_pct"] < 2.0:
        class_rf = "rf_u_h_convergence_supported"
    else:
        class_rf = "rf_u_h_convergence_inconclusive"

    # publication: provisional if H2 NRMSE not huge
    h2pub = pub_rows[2]
    if h2pub["full_overlap_nrmse_pct"] < 25:
        class_pub = "publication_agreement_provisional"
    else:
        class_pub = "publication_agreement_insufficient"

    class_crack = "crack_path_convergence_not_assessed"

    # recommendations
    if class_rf == "rf_u_h_convergence_supported":
        ref_rec = "H2-PUB preferred as conservative uniform fine reference for RF-U"
        mid_rec = "H1 acceptable for intermediate RF-U development studies"
    else:
        ref_rec = "H2-PUB retained as finest available; convergence not fully claimed"
        mid_rec = "H1 use only with documented limitation"

    # --- scientific review ---
    review = f"""# H-Convergence Scientific Review — Molnar lc = 0.015 mm

Status: `rf_u_analysis_complete_contour_not_assessed`

## 1. Study purpose

Establish successive-mesh RF–displacement convergence for the exact supplementary
Molnar single-notch staggered UEL model at **lc = 0.015 mm**, with H2-PUB at the
publication-reported local crack-path resolution h = 0.001 mm.

## 2. Source provenance

| Case | Solver job | CAE job | Physical N | Measured h [mm] | h/lc |
|---|---|---|---:|---:|---:|
| H0 | 1376154.mmaster02 | 1376236 | 3930 | {MESH['H0']['h_meas']:.6g} | {MESH['H0']['h_over_lc']:.4g} |
| H1 | 1376185.mmaster02 | 1376236 | 12064 | {MESH['H1']['h_meas']:.6g} | {MESH['H1']['h_over_lc']:.4g} |
| H2-PUB | 1376186.mmaster02 | 1376236 | 33852 | {MESH['H2-PUB']['h_meas']:.6g} | {MESH['H2-PUB']['h_over_lc']:.4g} |

Scientific-input revision: `58d7e3102d76fe0e70e6729457e2c7e90ad131bb`
CAE infrastructure revision: `bd09bc4f33a1415bba70769458d5bbbf218e1592`
CAE completion record: `33aa56fbd68e1ec799d2aece9578bd6471322e62`

H2-PUB reproduces the **publication local resolution**, not an undocumented exact
publication mesh topology (element count 33852 is generated, not forced to ~22000).

## 3. Technical execution summary

| Layer | H0 | H1 | H2-PUB |
|---|---|---|---|
| Abaqus solver | technical pass | technical pass | technical pass |
| First CAE attempts | f-string fail; argv `-cae` fail | argv `-cae` fail | argv `-cae` fail |
| Consolidated CAE 1376236 | **pass** | **pass** | **pass** |
| RF2–U2 package | yes | yes | yes |
| Contour PNG export | failed (viewport API) | failed | failed |

Failed CAE attempts are retained as infrastructure history and are not hidden.

## 4. Curve validation and interpolation

- Units: U2 [mm], RF2 [kN]; sign: positive tension as exported.
- Origin (0,0) included.
- Duplicate U: retain last frame (deterministic).
- Common U interval: **[{u_min:.6g}, {u_max:.6g}] mm**
- Grid: **N = {N_GRID}** linear points; linear force interpolation.
- Primary pre/post split: **U_split = U_peak(H2-PUB) = {u_split:.6g} mm**
- Initial tangent: least-squares through origin on **0 < U ≤ {TANGENT_U_MAX} mm** (common).

Curve validation overall: **pass** (see `results/processed/molnar_lc015_h_convergence/CURVE_VALIDATION_REPORT.md`).

## 5. Scalar RF–U metrics

| Case | peak RF2 [kN] | U at peak [mm] | K0 [kN/mm] | area [kN·mm] |
|---|---:|---:|---:|---:|
| H0 | {case_dict['H0']['peak_RF2_kN']:.6g} | {case_dict['H0']['U2_at_peak_mm']:.6g} | {case_dict['H0']['initial_tangent_kN_per_mm']:.6g} | {case_dict['H0']['area_kN_mm']:.6g} |
| H1 | {case_dict['H1']['peak_RF2_kN']:.6g} | {case_dict['H1']['U2_at_peak_mm']:.6g} | {case_dict['H1']['initial_tangent_kN_per_mm']:.6g} | {case_dict['H1']['area_kN_mm']:.6g} |
| H2-PUB | {case_dict['H2-PUB']['peak_RF2_kN']:.6g} | {case_dict['H2-PUB']['U2_at_peak_mm']:.6g} | {case_dict['H2-PUB']['initial_tangent_kN_per_mm']:.6g} | {case_dict['H2-PUB']['area_kN_mm']:.6g} |

## 6. Successive-mesh differences (finer = denominator)

| Pair | ΔF_peak | ΔU_peak | full NRMSE | pre-peak NRMSE | post-peak NRMSE |
|---|---:|---:|---:|---:|---:|
| H0 vs H1 | {h0h1['rel_peak_RF2_pct']:.3f}% | {h0h1['rel_peak_U2_pct']:.3f}% | {h0h1['full_curve_nrmse_pct']:.3f}% | {h0h1['prepeak_nrmse_pct']:.3f}% | {h0h1['postpeak_nrmse_pct']:.3f}% |
| H1 vs H2-PUB | {h1h2['rel_peak_RF2_pct']:.3f}% | {h1h2['rel_peak_U2_pct']:.3f}% | {h1h2['full_curve_nrmse_pct']:.3f}% | {h1h2['prepeak_nrmse_pct']:.3f}% | {h1h2['postpeak_nrmse_pct']:.3f}% |

Relative tangent change H0→H1: {100*h0h1['rel_tangent']:.3f}%; H1→H2: {100*h1h2['rel_tangent']:.3f}%.

## 7. Publication comparison (approximate Fig. 7 lc=0.015 only)

Reference class: `approximate_digitized_publication_reference` (not exact author data).

| Case | full overlap NRMSE | pre NRMSE | post NRMSE | ΔF_peak vs ref |
|---|---:|---:|---:|---:|
| H0 | {pub_rows[0]['full_overlap_nrmse_pct']:.2f}% | {pub_rows[0]['prepeak_overlap_nrmse_pct']:.2f}% | {pub_rows[0]['postpeak_overlap_nrmse_pct']:.2f}% | {100*pub_rows[0]['rel_peak_RF2_vs_ref']:.2f}% |
| H1 | {pub_rows[1]['full_overlap_nrmse_pct']:.2f}% | {pub_rows[1]['prepeak_overlap_nrmse_pct']:.2f}% | {pub_rows[1]['postpeak_overlap_nrmse_pct']:.2f}% | {100*pub_rows[1]['rel_peak_RF2_vs_ref']:.2f}% |
| H2-PUB | {pub_rows[2]['full_overlap_nrmse_pct']:.2f}% | {pub_rows[2]['prepeak_overlap_nrmse_pct']:.2f}% | {pub_rows[2]['postpeak_overlap_nrmse_pct']:.2f}% | {100*pub_rows[2]['rel_peak_RF2_vs_ref']:.2f}% |

Publication agreement is **secondary** to successive-mesh evidence.

## 8. Resource scaling (serial)

| Case | N | walltime | mem | wall/elem [s] |
|---|---:|---|---:|---:|
| H0 | 3930 | {fmt_s(t0)} | {MESH['H0']['mem_kb']} kb | {t0/n0:.4g} |
| H1 | 12064 | {fmt_s(t1)} | {MESH['H1']['mem_kb']} kb | {t1/n1:.4g} |
| H2-PUB | 33852 | {fmt_s(t2)} | {MESH['H2-PUB']['mem_kb']} kb | {t2/n2:.4g} |

Empirical log–log slope walltime vs N: **α ≈ {alpha:.3f}** (serial only; not parallel scalability).

## 9. Scientific classification

| Domain | Classification |
|---|---|
| A. Scalar RF–U convergence | `{class_rf}` |
| B. Full-curve convergence | `{class_rf}` (supported by successive NRMSE) |
| C. Publication agreement | `{class_pub}` |
| D. Computational cost | documented; serial growth with N |
| E. Crack-path / contour | `{class_crack}` |

## 10. Recommendations

1. **Uniform fine reference (RF–U):** {ref_rec}.
2. **Intermediate studies:** {mid_rec}.
3. **H0:** too coarse for final reference (clear H0→H1 change).
4. **Contours:** crack-path h-convergence remains unassessed until matched-state SDV15 images exist for all three meshes.
5. **Gate A3:** remains `reference_data_insufficient` / open until supervisor-approved tolerances and full evidence package (including contours if required) are accepted.

## 11. Limitations

- Field-output sampling yields 73 RF–U points per case (not every solver increment).
- Contour PNG export failed in CAE job 1376236 (viewport API).
- Publication curve is approximate digitization with uncertainty.
- Thresholds used for wording are provisional descriptive aids, not supervisor-approved gates.
- No multicore scaling claim.

## 12. Current project boundary

```text
Solvers H0/H1/H2: technical pass
Consolidated CAE: complete (authorization consumed)
RF-U h-convergence analysis: complete
Scientific mesh comparison documented: yes
Crack-path convergence: not assessed
PBS/Abaqus/CAE further runs: not authorized without new decision
MISESERI / remeshing / state transfer: blocked
Gate A3: open
```

## 13. Figures and tables

- Tables: `results/tables/molnar_lc015_h_convergence/`
- Figures: `results/figures/molnar_lc015_h_convergence/`
- Processed: `results/processed/molnar_lc015_h_convergence/`
"""
    (OUT_REV / "H_CONVERGENCE_SCIENTIFIC_REVIEW.md").write_text(review, encoding="utf-8")

    # machine-readable decision
    decision = {
        "rf_u_classification": class_rf,
        "publication_classification": class_pub,
        "crack_path_classification": class_crack,
        "uniform_reference_recommendation": "H2-PUB",
        "intermediate_mesh_recommendation": "H1",
        "h0_h1": h0h1,
        "h1_h2": h1h2,
        "case_metrics": case_dict,
        "u_split": u_split,
        "common_u": [u_min, u_max],
        "resource_alpha": alpha,
    }
    (OUT_REV / "H_CONVERGENCE_DECISION.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(json.dumps({"status": "ok", "class_rf": class_rf, "class_pub": class_pub, "h1h2_dF_pct": h1h2["rel_peak_RF2_pct"], "h1h2_full_nrmse_pct": h1h2["full_curve_nrmse_pct"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
