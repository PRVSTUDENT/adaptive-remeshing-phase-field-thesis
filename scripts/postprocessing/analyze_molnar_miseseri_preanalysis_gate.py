#!/usr/bin/env python3
"""Scientific + technical gate analysis for Stage C Job 2 MISESERI pre-analysis.

Reads JOB2_MISESERI_ELEMENT_DATA.csv (exported from ODB) and writes:
  JOB2_FIELD_SUMMARY.json
  JOB2_GATE_REPORT.md
  figures (if matplotlib available)

Does not require Abaqus Python.
"""

import argparse
import csv
import json
import math
import statistics
from collections import Counter
from pathlib import Path


def load_rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def f(row, key):
    return float(row[key])


def classify_region(x, y):
    # Geometry: plate [-0.5,0.5]^2, notch along y=0 for x in [-0.5,0)
    # Crack corridor / notch tip region (defensible refinement zone)
    if -0.05 <= x <= 0.35 and abs(y) <= 0.03:
        return "notch_corridor"
    if abs(y) >= 0.45:
        return "support_boundary"
    if abs(x) >= 0.45:
        return "side_boundary"
    # Loaded top is y=+0.5 already covered as support_boundary for |y|>=0.45
    if y >= 0.40:
        return "loaded_boundary"
    if y <= -0.40:
        return "support_boundary"
    return "far_field"


def percentile_indices(values, frac):
    """Indices of the top fraction by value."""
    n = len(values)
    if n == 0:
        return set()
    k = max(1, int(math.ceil(frac * n)))
    order = sorted(range(n), key=lambda i: values[i], reverse=True)
    return set(order[:k])


def analyze(rows, u_pre):
    n = len(rows)
    miseseri = [f(r, "MISESERI") for r in rows]
    misesavg = [f(r, "MISESAVG") for r in rows]
    evol = [f(r, "EVOL") for r in rows]
    vm = [f(r, "von_mises") for r in rows]
    sdv15 = [f(r, "SDV15") if "SDV15" in rows[0] and rows[0]["SDV15"] != "" else 0.0 for r in rows]
    xs = [f(r, "centroid_x") for r in rows]
    ys = [f(r, "centroid_y") for r in rows]

    max_e = max(miseseri) if miseseri else 0.0
    max_vm = max(vm) if vm else 0.0
    max_sdv15 = max(sdv15) if sdv15 else 0.0

    finite = all(math.isfinite(v) for v in miseseri)
    nonempty = any(abs(v) > 0.0 for v in miseseri)
    # "scientifically inactive" if max is machine-noise level
    inactive = (not nonempty) or (max_e < 1.0e-12)

    regions = [classify_region(x, y) for x, y in zip(xs, ys)]
    for r, reg in zip(rows, regions):
        r["region_classification"] = reg
        r["normalized_MISESERI"] = (f(r, "MISESERI") / max_e) if max_e > 0 else 0.0

    top01 = percentile_indices(miseseri, 0.01)
    top05 = percentile_indices(miseseri, 0.05)
    top10 = percentile_indices(miseseri, 0.10)

    def region_frac(idx_set, name):
        if not idx_set:
            return 0.0
        return sum(1 for i in idx_set if regions[i] == name) / float(len(idx_set))

    def region_frac_any(idx_set, names):
        if not idx_set:
            return 0.0
        return sum(1 for i in idx_set if regions[i] in names) / float(len(idx_set))

    boundary_names = {"support_boundary", "loaded_boundary", "side_boundary"}

    # Marked elements: errorTarget=0.05 absolute OR top 5% if absolute marks nothing useful
    error_target = 0.05
    marked_abs = [i for i, v in enumerate(miseseri) if v > error_target]
    # For ranking use, always compute top 5% marked
    marked_top5 = sorted(top05)

    # Spatial nonuniformity: coefficient of variation / unique-ish range
    mean_e = statistics.mean(miseseri) if miseseri else 0.0
    stdev_e = statistics.pstdev(miseseri) if len(miseseri) > 1 else 0.0
    cov = (stdev_e / mean_e) if mean_e > 0 else 0.0
    # Fraction of mass in top 5%
    total = sum(miseseri) if miseseri else 0.0
    mass_top5 = sum(miseseri[i] for i in top05) / total if total > 0 else 0.0

    # Phase field: meaningful crack if many elements with SDV15 high
    cracked = sum(1 for v in sdv15 if v >= 0.5)
    highly_damaged = sum(1 for v in sdv15 if v >= 0.95)

    # Scientific classification
    technical_field_ok = finite and nonempty and n == 3930
    corridor_top5 = region_frac(top05, "notch_corridor")
    boundary_top5 = region_frac_any(top05, boundary_names)
    corridor_top1 = region_frac(top01, "notch_corridor")

    if inactive:
        sci_class = "miseseri_output_available_but_scientifically_inactive"
        sci_pass = False
    elif not finite:
        sci_class = "miseseri_nonfinite_values"
        sci_pass = False
    elif max_sdv15 >= 0.95 and highly_damaged >= 5:
        sci_class = "phase_field_crack_already_developed"
        sci_pass = False
    elif corridor_top5 >= 0.40 and boundary_top5 <= 0.40 and mass_top5 >= 0.15:
        sci_class = "miseseri_preanalysis_suitable_for_remeshing"
        sci_pass = True
    elif corridor_top5 >= 0.25 and boundary_top5 < 0.55 and not inactive:
        sci_class = "miseseri_preanalysis_marginal_review"
        sci_pass = False  # do not auto-release Job 3 on marginal
    else:
        sci_class = "miseseri_preanalysis_boundary_dominated_or_diffuse"
        sci_pass = False

    summary = {
        "n_elements": n,
        "u_pre_mm": u_pre,
        "MISESERI_min": min(miseseri) if miseseri else None,
        "MISESERI_max": max_e,
        "MISESERI_mean": mean_e,
        "MISESERI_stdev": stdev_e,
        "MISESERI_cov": cov,
        "MISESERI_all_finite": finite,
        "MISESERI_nonempty": nonempty,
        "scientifically_inactive": inactive,
        "MISESAVG_max": max(misesavg) if misesavg else None,
        "von_mises_max": max_vm,
        "SDV15_max": max_sdv15,
        "n_SDV15_ge_0.5": cracked,
        "n_SDV15_ge_0.95": highly_damaged,
        "n_marked_errorTarget_0.05": len(marked_abs),
        "top1_pct_n": len(top01),
        "top5_pct_n": len(top05),
        "top10_pct_n": len(top10),
        "top1_fraction_notch_corridor": corridor_top1,
        "top5_fraction_notch_corridor": corridor_top5,
        "top5_fraction_boundary": boundary_top5,
        "top5_fraction_far_field": region_frac(top05, "far_field"),
        "mass_fraction_in_top5": mass_top5,
        "region_counts_all": dict(Counter(regions)),
        "region_counts_top5": dict(
            Counter(regions[i] for i in top05)
        ),
        "technical_field_shape_ok": technical_field_ok,
        "scientific_classification": sci_class,
        "scientific_gate_pass": sci_pass,
        "job3_release": sci_pass and technical_field_ok,
        "errorTarget": error_target,
        "criteria": {
            "inactive_threshold_max_MISESERI": 1.0e-12,
            "corridor_top5_min_for_pass": 0.40,
            "boundary_top5_max_for_pass": 0.40,
            "mass_top5_min_for_pass": 0.15,
            "crack_block_if_SDV15_ge_0.95_count": 5,
        },
    }

    # annotate rows for CSV rewrite
    for i, r in enumerate(rows):
        r["in_top_1pct"] = 1 if i in top01 else 0
        r["in_top_5pct"] = 1 if i in top05 else 0
        r["in_top_10pct"] = 1 if i in top10 else 0
        r["marked_errorTarget"] = 1 if i in marked_abs else 0

    return summary, rows


def write_figures(rows, outdir, summary):
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.collections import PatchCollection
        from matplotlib.patches import Rectangle
    except Exception as exc:
        (outdir / "FIGURE_EXPORT_WARNING.txt").write_text(
            f"matplotlib unavailable: {exc}\n", encoding="utf-8"
        )
        return []

    xs = [float(r["centroid_x"]) for r in rows]
    ys = [float(r["centroid_y"]) for r in rows]
    e = [float(r["MISESERI"]) for r in rows]
    en = [float(r["normalized_MISESERI"]) for r in rows]
    vm = [float(r["von_mises"]) for r in rows]
    sdv = [float(r["SDV15"]) if r.get("SDV15") not in (None, "") else 0.0 for r in rows]
    top5 = [int(r["in_top_5pct"]) for r in rows]

    figures = []

    def scatter(vals, title, fname, cmap="viridis", log=False):
        fig, ax = plt.subplots(figsize=(6, 6), dpi=140)
        plot_vals = vals
        if log:
            plot_vals = [math.log10(v) if v > 0 else -40 for v in vals]
            title = title + " (log10)"
        sc = ax.scatter(xs, ys, c=plot_vals, s=6, cmap=cmap, linewidths=0)
        fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
        ax.set_aspect("equal")
        ax.set_xlim(-0.55, 0.55)
        ax.set_ylim(-0.55, 0.55)
        ax.set_xlabel("x [mm]")
        ax.set_ylabel("y [mm]")
        ax.set_title(title)
        # notch guide
        ax.plot([-0.5, 0.0], [0.0, 0.0], "r-", lw=1.0, alpha=0.7)
        path = outdir / fname
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        figures.append(str(path.as_posix()))

    scatter(e, "MISESERI at Upre", "01_miseseri_contour.png", log=True)
    scatter(en, "Normalized MISESERI", "02_normalized_miseseri_contour.png")
    scatter(vm, "von Mises stress", "03_von_mises_contour.png")
    # top 5% marked
    fig, ax = plt.subplots(figsize=(6, 6), dpi=140)
    ax.scatter(xs, ys, c="0.85", s=4, linewidths=0)
    xt = [x for x, m in zip(xs, top5) if m]
    yt = [y for y, m in zip(ys, top5) if m]
    ax.scatter(xt, yt, c="crimson", s=10, linewidths=0, label="top 5% MISESERI")
    ax.plot([-0.5, 0.0], [0.0, 0.0], "k-", lw=1.0)
    ax.set_aspect("equal")
    ax.set_xlim(-0.55, 0.55)
    ax.set_ylim(-0.55, 0.55)
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_title("Top 5% MISESERI elements")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    p = outdir / "04_top5pct_marked_elements.png"
    fig.savefig(p)
    plt.close(fig)
    figures.append(str(p.as_posix()))

    scatter(sdv, "Phase field SDV15 at Upre", "05_phase_field_sdv15.png", cmap="magma")

    return figures


def write_report(path, summary, figures):
    lines = [
        "# Stage C Job 2 Gate Report",
        "",
        f"Scientific classification: `{summary['scientific_classification']}`",
        f"Scientific gate: **{'PASS' if summary['scientific_gate_pass'] else 'FAIL'}**",
        f"Job 3 release: **{'YES' if summary['job3_release'] else 'NO'}**",
        "",
        "## Field scalars",
        "",
        f"- n elements: {summary['n_elements']}",
        f"- Upre: {summary['u_pre_mm']} mm",
        f"- MISESERI min/mean/max: {summary['MISESERI_min']:.6e} / {summary['MISESERI_mean']:.6e} / {summary['MISESERI_max']:.6e}",
        f"- MISESERI CoV: {summary['MISESERI_cov']:.4f}",
        f"- scientifically_inactive: {summary['scientifically_inactive']}",
        f"- von Mises max: {summary['von_mises_max']}",
        f"- SDV15 max: {summary['SDV15_max']}",
        f"- n SDV15≥0.5 / ≥0.95: {summary['n_SDV15_ge_0.5']} / {summary['n_SDV15_ge_0.95']}",
        f"- n marked by absolute errorTarget=0.05: {summary['n_marked_errorTarget_0.05']}",
        "",
        "## Spatial concentration (top 5% by MISESERI)",
        "",
        f"- fraction notch_corridor: {summary['top5_fraction_notch_corridor']:.3f}",
        f"- fraction boundary: {summary['top5_fraction_boundary']:.3f}",
        f"- fraction far_field: {summary['top5_fraction_far_field']:.3f}",
        f"- mass fraction in top 5%: {summary['mass_fraction_in_top5']:.3f}",
        f"- top1 notch_corridor fraction: {summary['top1_fraction_notch_corridor']:.3f}",
        "",
        "## Region counts (all / top5)",
        "",
        f"- all: `{summary['region_counts_all']}`",
        f"- top5: `{summary['region_counts_top5']}`",
        "",
        "## Pass criteria",
        "",
        "```text",
        "inactive if max(MISESERI) < 1e-12",
        "pass if corridor_top5 >= 0.40 and boundary_top5 <= 0.40",
        "      and mass_top5 >= 0.15 and no meaningful crack",
        "```",
        "",
        "## Figures",
        "",
    ]
    for fig in figures:
        lines.append(f"- `{fig}`")
    if not figures:
        lines.append("- (no figures; matplotlib missing or export failed)")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"```text",
            f"scientific_classification = {summary['scientific_classification']}",
            f"job3_release = {summary['job3_release']}",
            f"```",
            "",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--u-pre", type=float, default=0.00464)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = load_rows(args.csv)
    summary, rows = analyze(rows, args.u_pre)

    # rewrite annotated CSV
    out_csv = args.out_dir / "JOB2_MISESERI_ELEMENT_DATA.csv"
    if rows:
        fields = list(rows[0].keys())
        with out_csv.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    (args.out_dir / "JOB2_FIELD_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    fig_dir = args.out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    figures = write_figures(rows, fig_dir, summary)
    write_report(args.out_dir / "JOB2_GATE_REPORT.md", summary, figures)
    print(
        json.dumps(
            {
                "scientific_classification": summary["scientific_classification"],
                "job3_release": summary["job3_release"],
                "MISESERI_max": summary["MISESERI_max"],
                "top5_corridor": summary["top5_fraction_notch_corridor"],
                "top5_boundary": summary["top5_fraction_boundary"],
            },
            indent=2,
        )
    )
    return 0 if summary.get("technical_field_shape_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
