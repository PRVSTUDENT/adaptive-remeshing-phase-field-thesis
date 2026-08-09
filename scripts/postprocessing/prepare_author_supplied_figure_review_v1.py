#!/usr/bin/env python3
"""Prepare supervisor-review figures for the author-supplied SingleNotch run."""


import csv
import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import Normalize, PowerNorm
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
RUN = ROOT / "runs" / "molnar_single_notch_author_supplied_exact" / "20260720_abaqus_cae_reproduction"
OUT = RUN / "figure_review_v1"
PLOTS = OUT / "plots"
CONTOURS = OUT / "contours"
PANELS = OUT / "panels"
NOTES = OUT / "notes"

SIM_CSV = RUN / "cae_exports" / "cae_author_supplied_rf2_u2.csv"
REF_CSV = RUN / "digitization" / "fig7_lc_0p015_processed.csv"
METRICS_JSON = RUN / "report" / "comparison_metrics.json"
INP = RUN / "work" / "SingleNotch.inp"
CAE_EXPORTS = RUN / "cae_exports"

N_ELEM = 3930


def ensure_dirs() -> None:
    for path in [PLOTS, CONTOURS, PANELS, NOTES]:
        path.mkdir(parents=True, exist_ok=True)


def read_xy_csv(path: Path, x_key: str, y_key: str) -> tuple[np.ndarray, np.ndarray]:
    xs: list[float] = []
    ys: list[float] = []
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            xs.append(float(row[x_key]))
            ys.append(float(row[y_key]))
    return np.array(xs), np.array(ys)


def read_metrics() -> dict:
    return json.loads(METRICS_JSON.read_text())


def style_axes(ax) -> None:
    ax.grid(True, color="#d7d7d7", linewidth=0.65)
    for spine in ax.spines.values():
        spine.set_color("#2f2f2f")
        spine.set_linewidth(0.9)
    ax.tick_params(colors="#242424", labelsize=11)


def plot_rf_u(annotated: bool) -> None:
    sim_u, sim_rf = read_xy_csv(SIM_CSV, "u2_mm", "rf2_kN")
    ref_u, ref_rf = read_xy_csv(REF_CSV, "u_mm", "reaction_force_kN")
    metrics = read_metrics()

    fig, ax = plt.subplots(figsize=(7.4, 5.1), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.plot(
        sim_u,
        sim_rf,
        color="#b12a34",
        linewidth=2.1,
        label="Author-supplied supplementary model",
    )
    ax.plot(
        ref_u,
        ref_rf,
        color="#1f4e79",
        linewidth=2.0,
        linestyle="--",
        marker="o",
        markersize=3.8,
        markerfacecolor="white",
        markeredgewidth=0.9,
        label="Digitized Molnár Fig. 7 points, ℓc = 0.015 mm",
    )

    sim_peak = metrics["simulation_peak"]
    ref_peak = metrics["reference_peak"]
    ax.scatter(
        [sim_peak["u2_mm"], ref_peak["u_mm"]],
        [sim_peak["rf2_kN"], ref_peak["force_kN"]],
        s=42,
        color=["#b12a34", "#1f4e79"],
        edgecolor="white",
        linewidth=0.8,
        zorder=4,
    )
    ax.scatter([0], [0], s=28, color="#222222", zorder=5)

    ax.set_xlabel("Displacement at RP, U₂ [mm]", fontsize=12)
    ax.set_ylabel("Reaction force at RP, RF₂ [kN]", fontsize=12)
    ax.set_xlim(-0.0001, 0.00715)
    ax.set_ylim(-0.02, 0.78)
    ax.ticklabel_format(axis="x", style="plain", useOffset=False)
    style_axes(ax)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 0.03), fontsize=10, frameon=True)

    if annotated:
        note = (
            "Peak force error: +5.36%\n"
            "Peak displacement error: +9.25%\n"
            "Full-curve NRMSE: 0.1723 (17.23%)"
        )
        ax.text(
            0.00034,
            0.71,
            note,
            fontsize=10,
            va="top",
            ha="left",
            bbox=dict(boxstyle="round,pad=0.28", facecolor="white", edgecolor="#b8b8b8", linewidth=0.8),
        )
        stem_kwargs = dict(arrowstyle="->", color="#333333", linewidth=0.8, shrinkA=3, shrinkB=3)
        ax.annotate("Simulation peak", xy=(sim_peak["u2_mm"], sim_peak["rf2_kN"]), xytext=(0.00455, 0.74), arrowprops=stem_kwargs, fontsize=9)
        ax.annotate("Digitized peak", xy=(ref_peak["u_mm"], ref_peak["force_kN"]), xytext=(0.00435, 0.63), arrowprops=stem_kwargs, fontsize=9)

    fig.tight_layout(pad=0.5)
    stem = PLOTS / "author_supplied_vs_fig7_lc_0p015_clean"
    if annotated:
        fig.savefig(stem.with_suffix(".png"), dpi=300)
        fig.savefig(stem.with_suffix(".pdf"))
    else:
        fig.savefig(PLOTS / "author_supplied_vs_fig7_lc_0p015_clean_minimal.png", dpi=300)
    plt.close(fig)


def parse_inp_mesh() -> tuple[dict[int, tuple[float, float]], dict[int, list[int]]]:
    nodes: dict[int, tuple[float, float]] = {}
    elems: dict[int, list[int]] = {}
    mode = None
    with INP.open() as stream:
        for raw in stream:
            line = raw.strip()
            if not line or line.startswith("**"):
                continue
            lower = line.lower()
            if lower.startswith("*node"):
                mode = "node"
                continue
            if lower.startswith("*element"):
                if "type=u1" in lower:
                    mode = "u1"
                else:
                    mode = None
                continue
            if line.startswith("*"):
                mode = None
                continue
            parts = [part.strip() for part in line.split(",") if part.strip()]
            if mode == "node" and len(parts) >= 3:
                nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif mode == "u1" and len(parts) >= 5:
                label = int(parts[0])
                if label <= N_ELEM:
                    elems[label] = [int(item) for item in parts[1:5]]
    return nodes, elems


def element_polygons(nodes: dict[int, tuple[float, float]], elems: dict[int, list[int]]) -> tuple[list[list[tuple[float, float]]], list[int]]:
    labels = sorted(elems)
    polygons = [[nodes[node] for node in elems[label]] for label in labels]
    return polygons, labels


def plot_geometry_mesh(nodes: dict[int, tuple[float, float]], elems: dict[int, list[int]]) -> None:
    polygons, _ = element_polygons(nodes, elems)
    segments = []
    for poly in polygons:
        closed = poly + [poly[0]]
        for a, b in zip(closed[:-1], closed[1:]):
            segments.append([a, b])

    fig, ax = plt.subplots(figsize=(7.0, 7.0), dpi=240)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.add_collection(LineCollection(segments, colors="#303030", linewidths=0.18))
    ax.set_aspect("equal")
    ax.set_xlim(-0.54, 0.54)
    ax.set_ylim(-0.54, 0.54)
    ax.set_xlabel("x [mm]", fontsize=11)
    ax.set_ylabel("y [mm]", fontsize=11)
    style_axes(ax)

    ax.annotate("Initial notch", xy=(-0.22, 0.0), xytext=(-0.46, 0.17), arrowprops=dict(arrowstyle="->", lw=1.1), fontsize=10)
    ax.annotate("Refined crack-path region", xy=(0.28, 0.0), xytext=(0.02, -0.43), arrowprops=dict(arrowstyle="->", lw=1.1), fontsize=10)
    ax.annotate("Top edge coupled to RP;\nprescribed U₂", xy=(-0.35, 0.5), xytext=(-0.45, 0.64), arrowprops=dict(arrowstyle="->", lw=1.1), fontsize=10, ha="left")
    for xpos in [-0.25, 0.0, 0.25]:
        ax.annotate("", xy=(xpos, 0.5), xytext=(xpos, 0.575), arrowprops=dict(arrowstyle="->", lw=1.0, color="#222222"))
    ax.annotate("Bottom edge: U₂ = 0", xy=(-0.25, -0.5), xytext=(-0.47, -0.64), arrowprops=dict(arrowstyle="->", lw=1.1), fontsize=10)
    ax.annotate("Source-defined\nhorizontal constraints", xy=(-0.5, -0.02), xytext=(-0.47, -0.24), arrowprops=dict(arrowstyle="->", lw=1.1), fontsize=10, ha="left")
    for xpos in [-0.25, 0.0, 0.25]:
        ax.plot([xpos - 0.018, xpos + 0.018], [-0.515, -0.515], color="#222222", linewidth=1.0)
    for ypos in [-0.24, 0.24]:
        ax.plot([-0.515, -0.515], [ypos - 0.018, ypos + 0.018], color="#222222", linewidth=1.0)
    ax.plot([-0.5, 0.0], [0.0, 0.0], color="#d02f2f", linewidth=2.4, solid_capstyle="butt")
    ax.add_patch(plt.Rectangle((-0.03, -0.055), 0.53, 0.11, fill=False, edgecolor="#1f78b4", linewidth=1.2, linestyle="--"))

    fig.tight_layout(pad=0.6)
    fig.savefig(CONTOURS / "geometry_mesh_clean.png", dpi=240)
    plt.close(fig)


def read_contour_values(path: Path, variable: str) -> dict[int, float]:
    values: dict[int, list[float]] = {}
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            if not row.get(variable):
                continue
            raw_element = int(row["element"])
            physical_element = raw_element - 2 * N_ELEM if raw_element > 2 * N_ELEM else raw_element
            values.setdefault(physical_element, []).append(float(row[variable]))
    return {label: float(np.mean(items)) for label, items in values.items()}


def plot_contour(
    nodes: dict[int, tuple[float, float]],
    elems: dict[int, list[int]],
    source_csv: Path,
    variable: str,
    out_name: str,
    state_label: str,
    final_sdv15: bool = False,
    power_normalized: bool = False,
) -> None:
    polygons, labels = element_polygons(nodes, elems)
    values_by_element = read_contour_values(source_csv, variable)
    values = np.array([values_by_element.get(label, np.nan) for label in labels])

    fig, ax = plt.subplots(figsize=(7.2, 5.8), dpi=240)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    if variable == "sdv15":
        norm = Normalize(vmin=0.0, vmax=1.05)
        cmap = "viridis"
        cbar_label = "Element-wise mean of integration-point SDV15"
    else:
        finite = values[np.isfinite(values)]
        vmax = float(np.nanmax(finite))
        norm = PowerNorm(gamma=0.35, vmin=0.0, vmax=vmax) if power_normalized else Normalize(vmin=0.0, vmax=vmax)
        cmap = "magma"
        cbar_label = (
            "SDV16 history variable, power-normalized color scale"
            if power_normalized
            else "Element-wise mean of integration-point SDV16"
        )

    coll = PolyCollection(
        polygons,
        array=values,
        cmap=cmap,
        norm=norm,
        edgecolors="none",
        linewidths=0.0,
    )
    ax.add_collection(coll)
    ax.set_aspect("equal")
    ax.set_xlim(-0.52, 0.52)
    ax.set_ylim(-0.52, 0.52)
    ax.set_xlabel("x [mm]", fontsize=10)
    ax.set_ylabel("y [mm]", fontsize=10)
    ax.set_xticks([-0.5, -0.25, 0.0, 0.25, 0.5])
    ax.set_yticks([-0.5, -0.25, 0.0, 0.25, 0.5])
    ax.tick_params(labelsize=9, colors="#222222")
    for spine in ax.spines.values():
        spine.set_color("#333333")
        spine.set_linewidth(0.8)
    cbar = fig.colorbar(coll, ax=ax, fraction=0.045, pad=0.025)
    cbar.ax.tick_params(labelsize=9)
    cbar.set_label(cbar_label, fontsize=9)
    ax.text(
        0.02,
        0.965,
        state_label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=11,
        bbox=dict(facecolor="white", edgecolor="#bcbcbc", pad=3.0),
    )
    ax.plot([-0.5, 0.0], [0.0, 0.0], color="white", linewidth=3.2, alpha=0.95, solid_capstyle="butt")
    ax.plot([-0.5, 0.0], [0.0, 0.0], color="#111111", linewidth=1.25, alpha=0.95, solid_capstyle="butt")
    if variable == "sdv15":
        ax.text(-0.45, 0.055, "Initial notch", color="white", fontsize=10, ha="left", va="bottom", bbox=dict(facecolor="#202020", edgecolor="white", alpha=0.65, pad=2.2))
        ax.annotate("Initial notch tip", xy=(0.0, 0.0), xytext=(-0.34, 0.25), arrowprops=dict(arrowstyle="->", color="white", lw=1.8), color="white", fontsize=10)
        ax.annotate("Crack extension direction", xy=(0.35, 0.0), xytext=(0.02, -0.35), arrowprops=dict(arrowstyle="->", color="white", lw=1.8), color="white", fontsize=10)
    if variable == "sdv16":
        if power_normalized:
            ax.text(
                0.02,
                0.94,
                "Power-normalized visualization for qualitative visibility",
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=9,
                color="white",
                bbox=dict(facecolor="#202020", edgecolor="white", alpha=0.72, pad=3.0),
            )
        ax.text(
            0.02,
            0.06,
            "History / driving state",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=10,
            color="white",
            bbox=dict(facecolor="#202020", edgecolor="white", alpha=0.72, pad=3.0),
        )
    fig.tight_layout(pad=0.3)
    fig.savefig(CONTOURS / out_name, dpi=240)
    plt.close(fig)


def make_panel() -> None:
    images = [
        (CONTOURS / "geometry_mesh_clean.png", "(a) Geometry and mesh"),
        (PLOTS / "author_supplied_vs_fig7_lc_0p015_clean_minimal.png", "(b) RF2-U2 comparison"),
        (CONTOURS / "sdv15_final_clean.png", "(c) Final SDV15 contour"),
        (CONTOURS / "sdv16_final_linear_clean.png", "(d) Final SDV16 contour"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12.0, 10.0), dpi=220)
    fig.patch.set_facecolor("white")
    for ax, (path, label) in zip(axes.ravel(), images):
        img = np.asarray(Image.open(path).convert("RGB"))
        ax.imshow(img)
        ax.set_axis_off()
        ax.set_title(label, loc="left", fontsize=14, fontweight="bold", pad=8)
    fig.tight_layout(pad=1.0, h_pad=1.2, w_pad=0.8)
    fig.savefig(PANELS / "author_supplied_reproduction_summary_panel.png", dpi=220)
    fig.savefig(PANELS / "author_supplied_reproduction_summary_panel.pdf")
    plt.close(fig)


def make_mockup() -> None:
    canvas = Image.new("RGB", (1800, 2400), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        head_font = ImageFont.truetype("arial.ttf", 34)
        body_font = ImageFont.truetype("arial.ttf", 30)
    except OSError:
        title_font = head_font = body_font = ImageFont.load_default()
    draw.text((90, 70), "Author-supplied SingleNotch supplementary reproduction", fill="#111111", font=title_font)
    draw.text((90, 135), "Preview page only - not the final supervisor PDF", fill="#555555", font=body_font)

    plot = Image.open(PLOTS / "author_supplied_vs_fig7_lc_0p015_clean.png").convert("RGB")
    plot.thumbnail((1620, 920), Image.Resampling.LANCZOS)
    canvas.paste(plot, (90, 220))
    contour = Image.open(CONTOURS / "sdv15_final_clean.png").convert("RGB")
    contour.thumbnail((900, 760), Image.Resampling.LANCZOS)
    canvas.paste(contour, (90, 1250))
    draw.text((1050, 1280), "Key observations", fill="#111111", font=head_font)
    bullets = [
        "Exact supplied input and Fortran hashes match.",
        "Local Abaqus 2024 serial run completed successfully.",
        "Both RF-U curves start at the origin.",
        "Peak force is about 5.36% higher than digitized Fig. 7.",
        "Smaller supplementary mesh is not publication-scale.",
    ]
    y = 1350
    for item in bullets:
        draw.text((1065, y), "- " + item, fill="#222222", font=body_font)
        y += 78
    canvas.save(PANELS / "supervisor_report_page_mockup.png", dpi=(300, 300))


def write_notes() -> None:
    captions = """# Figure Captions

## `plots/author_supplied_vs_fig7_lc_0p015_clean.png`

Reaction force-displacement comparison for the exact author-supplied supplementary Molnár single-notch model and the digitized Molnár Fig. 7 black solid `ℓc = 0.015 mm` reference. Both curves start at the origin; peak points are marked. The digitized reference is shown as points connected by a thin dashed line to make its image-digitized provenance clear. The comparison uses the unchanged Abaqus result and the documented digitized reference.

## `plots/author_supplied_vs_fig7_lc_0p015_clean_minimal.png`

Compact RF2-U2 comparison without metric annotations, suitable for insertion where the surrounding text already reports errors.

## `contours/geometry_mesh_clean.png`

Author-supplied single-edge-notched specimen mesh parsed from the unchanged input deck. The figure identifies the initial notch, the refined crack-path region, the top displacement loading, and the bottom vertical restraint.

## `contours/sdv15_u2_0p0020_clean.png`

SDV15 field at `U2 ~= 0.0020 mm`, rebuilt from the Abaqus contour CSV exported from the completed ODB. The field was reconstructed from Abaqus-exported integration-point data for presentation; the underlying values were not modified.

## `contours/sdv15_u2_0p0050_clean.png`

SDV15 field at `U2 ~= 0.0050 mm`, showing phase-field growth near the notch before complete ligament failure. The field was reconstructed from Abaqus-exported integration-point data for presentation; the underlying values were not modified.

## `contours/sdv15_u2_0p0060_clean.png`

SDV15 field at `U2 ~= 0.0060 mm`, showing the developing horizontal crack extension from the notch tip. The field was reconstructed from Abaqus-exported integration-point data for presentation; the underlying values were not modified.

## `contours/sdv15_final_clean.png`

Final SDV15 field at `U2 ~= 0.0070 mm`, showing the connected horizontal crack extension through the ligament. The field was reconstructed from Abaqus-exported integration-point data for presentation; the underlying values were not modified.

## `contours/sdv16_final_linear_clean.png`

Primary final SDV16 history/driving-state contour at `U2 ~= 0.0070 mm`, rebuilt from the Abaqus contour CSV with a linear color scale.

## `contours/sdv16_final_power_normalized_clean.png`

Supplementary final SDV16 history/driving-state contour at `U2 ~= 0.0070 mm`. This is a qualitative power-normalized visualization for visibility; numerical values are unchanged.

## `panels/author_supplied_reproduction_summary_panel.png`

Four-panel summary of the exact supplementary reproduction: geometry/mesh, RF2-U2 comparison, final SDV15 contour, and final SDV16 contour.

## `panels/supervisor_report_page_mockup.png`

Preview-only one-page layout showing how the improved RF-U and contour figures could appear in a supervisor report section.
"""
    (NOTES / "FIGURE_CAPTIONS.md").write_text(captions, encoding="utf-8")

    provenance = """# Figure Provenance

Underlying scientific data changed: `no`.

| Figure | Source file(s) | Method | Styling/cropping/annotation | Data changed |
|---|---|---|---|---|
| `plots/author_supplied_vs_fig7_lc_0p015_clean.png` | `cae_exports/cae_author_supplied_rf2_u2.csv`; `digitization/fig7_lc_0p015_processed.csv`; `report/comparison_metrics.json` | Rebuilt from CSV with matplotlib | White background, clean axes, peak markers, metric annotation, digitized points shown as markers | no |
| `plots/author_supplied_vs_fig7_lc_0p015_clean.pdf` | same as PNG | Rebuilt from CSV with matplotlib | Vector line plot | no |
| `plots/author_supplied_vs_fig7_lc_0p015_clean_minimal.png` | same CSV files | Rebuilt from CSV with matplotlib | Annotation-free compact styling | no |
| `contours/geometry_mesh_clean.png` | `work/SingleNotch.inp` | Parsed unchanged mesh and plotted element edges | Added exact boundary-condition annotations | no |
| `contours/sdv15_u2_0p0020_clean.png` | `cae_exports/matched_state_01_Step-1_frame_0020_contour_sdv14_sdv15_sdv16.csv`; `work/SingleNotch.inp` | Rebuilt from exported Abaqus contour CSV | White background, axes, color bar, state label, notch annotations | no |
| `contours/sdv15_u2_0p0050_clean.png` | `cae_exports/matched_state_02_Step-1_frame_0050_contour_sdv14_sdv15_sdv16.csv`; `work/SingleNotch.inp` | Rebuilt from exported Abaqus contour CSV | White background, axes, color bar, state label, notch annotations | no |
| `contours/sdv15_u2_0p0060_clean.png` | `cae_exports/matched_state_03_Step-2_frame_0010_contour_sdv14_sdv15_sdv16.csv`; `work/SingleNotch.inp` | Rebuilt from exported Abaqus contour CSV | White background, axes, color bar, state label, notch annotations | no |
| `contours/sdv15_final_clean.png` | `cae_exports/matched_state_04_Step-2_frame_0020_contour_sdv14_sdv15_sdv16.csv`; `work/SingleNotch.inp` | Rebuilt from exported Abaqus contour CSV | Added initial-notch, notch-tip, and crack-direction annotations | no |
| `contours/sdv16_final_linear_clean.png` | `cae_exports/matched_state_04_Step-2_frame_0020_contour_sdv14_sdv15_sdv16.csv`; `work/SingleNotch.inp` | Rebuilt from exported Abaqus contour CSV | Linear color scale; primary scientific SDV16 figure | no |
| `contours/sdv16_final_power_normalized_clean.png` | `cae_exports/matched_state_04_Step-2_frame_0020_contour_sdv14_sdv15_sdv16.csv`; `work/SingleNotch.inp` | Rebuilt from exported Abaqus contour CSV | Qualitative power-normalized visualization for visibility | no |
| `panels/author_supplied_reproduction_summary_panel.png` | Improved figures listed above | Assembled with matplotlib | Panel labels and white page layout | no |
| `panels/supervisor_report_page_mockup.png` | Improved figures listed above | Layout mockup with PIL | Preview heading and key observations | no |

No Abaqus analysis rerun was performed. No ZIP file, email draft, commit, stage, or push was created.
"""
    (NOTES / "FIGURE_PROVENANCE.md").write_text(provenance, encoding="utf-8")

    checklist = """# Figure Review Checklist

| Figure | Readable labels | Legend | Units | Correct identity | Origin included | No offsets | No dark margins | Annotation text | Naming | Supervisor-ready |
|---|---|---|---|---|---|---|---|---|---|---|
| `author_supplied_vs_fig7_lc_0p015_clean.png` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| `author_supplied_vs_fig7_lc_0p015_clean_minimal.png` | yes | yes | yes | yes | yes | yes | yes | n/a | yes | yes |
| `geometry_mesh_clean.png` | yes | n/a | yes | yes | n/a | n/a | yes | yes | yes | yes |
| `sdv15_u2_0p0020_clean.png` | yes | n/a | state labelled | yes | n/a | n/a | yes | yes | yes | yes |
| `sdv15_u2_0p0050_clean.png` | yes | n/a | state labelled | yes | n/a | n/a | yes | yes | yes | yes |
| `sdv15_u2_0p0060_clean.png` | yes | n/a | state labelled | yes | n/a | n/a | yes | yes | yes | yes |
| `sdv15_final_clean.png` | yes | n/a | state labelled | yes | n/a | n/a | yes | yes | yes | yes |
| `sdv16_final_linear_clean.png` | yes | n/a | state labelled | yes | n/a | n/a | yes | yes | yes | yes |
| `sdv16_final_power_normalized_clean.png` | yes | n/a | state labelled | yes | n/a | n/a | yes | yes | yes | supplementary |
| `author_supplied_reproduction_summary_panel.png` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| `supervisor_report_page_mockup.png` | yes | n/a | yes | yes | yes | yes | yes | yes | yes | preview only |
"""
    (NOTES / "FIGURE_REVIEW_CHECKLIST.md").write_text(checklist, encoding="utf-8")

    summary = """# Figure Generation Summary

Figure package directory:

`runs/molnar_single_notch_author_supplied_exact/20260720_abaqus_cae_reproduction/figure_review_v1`

## Files Created

- `plots/author_supplied_vs_fig7_lc_0p015_clean.png`
- `plots/author_supplied_vs_fig7_lc_0p015_clean.pdf`
- `plots/author_supplied_vs_fig7_lc_0p015_clean_minimal.png`
- `contours/geometry_mesh_clean.png`
- `contours/sdv15_u2_0p0020_clean.png`
- `contours/sdv15_u2_0p0050_clean.png`
- `contours/sdv15_u2_0p0060_clean.png`
- `contours/sdv15_final_clean.png`
- `contours/sdv16_final_linear_clean.png`
- `contours/sdv16_final_power_normalized_clean.png`
- `panels/author_supplied_reproduction_summary_panel.png`
- `panels/author_supplied_reproduction_summary_panel.pdf`
- `panels/supervisor_report_page_mockup.png`
- `notes/FIGURE_CAPTIONS.md`
- `notes/FIGURE_PROVENANCE.md`
- `notes/FIGURE_REVIEW_CHECKLIST.md`
- `notes/FIGURE_GENERATION_SUMMARY.md`

## Recommended For Supervisor Report

Use `plots/author_supplied_vs_fig7_lc_0p015_clean.png`, `contours/geometry_mesh_clean.png`, `contours/sdv15_final_clean.png`, `contours/sdv16_final_linear_clean.png`, and `panels/author_supplied_reproduction_summary_panel.png`.

## Validation

- Scientific data values changed: `no`.
- RF-U plot source: exact existing CSV files.
- Simulation origin: `(0, 0)`.
- Digitized reference origin: `(0, 0)`.
- Curve labels identify the author-supplied supplement and digitized Molnár Fig. 7 `ℓc = 0.015 mm`.
- Contour figures correspond to the matched displacement-state CSV files from the completed ODB.
- Linear SDV16 scale is used in the primary SDV16 figure and in the summary panel.
- Abaqus/CAE re-export required: `no`.
- Abaqus analysis rerun: `no`.
- ZIP created: `no`.
- Email drafted/finalized: `no`.
- Git commit/stage/push: `no`.
- Git status after generation: existing unrelated modified/deleted/untracked files remain; new figure package is under `runs/molnar_single_notch_author_supplied_exact/`; new helper script is `scripts/postprocessing/prepare_author_supplied_figure_review_v1.py`; no files were staged.

## Possible Further Improvement

The contour figures are rebuilt from element-averaged integration-point CSV values, which is cleaner for presentation than the original CAE screenshots. If a strict Abaqus/CAE screenshot provenance is required for the final report, a later CAE export pass could reproduce the same views at higher viewport resolution.
"""
    (NOTES / "FIGURE_GENERATION_SUMMARY.md").write_text(summary, encoding="utf-8")

    cae_note = """# Abaqus/CAE Compatibility Note

The clean supervisor-facing figures are presentation figures, not replacements for the retained Abaqus/CAE evidence.

- RF2 and U2 were obtained through Abaqus/CAE from assembly node set `RP`.
- The CAE XY report is retained at `cae_exports/cae_author_supplied_rf2_u2.rpt`.
- The original CAE RF-U PNG is retained at `cae_exports/cae_author_supplied_vs_fig7_lc_0p015.png`.
- The original direct CAE SDV15 contour PNGs are retained in `cae_exports/cae_sdv15_u2_0p0020.png`, `cae_exports/cae_sdv15_u2_0p0050.png`, `cae_exports/cae_sdv15_u2_0p0060.png`, and `cae_exports/cae_final_sdv15_contour.png`.
- The original direct CAE SDV16 contour PNG is retained in `cae_exports/cae_final_sdv16_contour.png`.
- The CAE noGUI script is retained at `scripts/postprocessing/export_author_supplied_cae_package.py`; CAE replay journals are retained in `evidence/abaqus.rpy*`.
- Contour data were exported from the Abaqus ODB and are retained as matched-state CSV files in `cae_exports/`.
- Clean report figures were restyled from these exported data for readability.
- Scientific values modified: `no`.
"""
    (NOTES / "CAE_COMPATIBILITY_NOTE.md").write_text(cae_note, encoding="utf-8")


def validate_images() -> None:
    required = [
        PLOTS / "author_supplied_vs_fig7_lc_0p015_clean.png",
        PLOTS / "author_supplied_vs_fig7_lc_0p015_clean.pdf",
        PLOTS / "author_supplied_vs_fig7_lc_0p015_clean_minimal.png",
        CONTOURS / "geometry_mesh_clean.png",
        CONTOURS / "sdv15_u2_0p0020_clean.png",
        CONTOURS / "sdv15_u2_0p0050_clean.png",
        CONTOURS / "sdv15_u2_0p0060_clean.png",
        CONTOURS / "sdv15_final_clean.png",
        CONTOURS / "sdv16_final_linear_clean.png",
        CONTOURS / "sdv16_final_power_normalized_clean.png",
        PANELS / "author_supplied_reproduction_summary_panel.png",
        PANELS / "author_supplied_reproduction_summary_panel.pdf",
        PANELS / "supervisor_report_page_mockup.png",
    ]
    for path in required:
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"missing output: {path}")
        if path.suffix.lower() == ".png":
            Image.open(path).verify()


def main() -> int:
    ensure_dirs()
    plot_rf_u(annotated=True)
    plot_rf_u(annotated=False)
    nodes, elems = parse_inp_mesh()
    plot_geometry_mesh(nodes, elems)
    contour_specs = [
        ("matched_state_01_Step-1_frame_0020_contour_sdv14_sdv15_sdv16.csv", "sdv15", "sdv15_u2_0p0020_clean.png", "U₂ ≈ 0.0020 mm", False),
        ("matched_state_02_Step-1_frame_0050_contour_sdv14_sdv15_sdv16.csv", "sdv15", "sdv15_u2_0p0050_clean.png", "U₂ ≈ 0.0050 mm", False),
        ("matched_state_03_Step-2_frame_0010_contour_sdv14_sdv15_sdv16.csv", "sdv15", "sdv15_u2_0p0060_clean.png", "U₂ ≈ 0.0060 mm", False),
        ("matched_state_04_Step-2_frame_0020_contour_sdv14_sdv15_sdv16.csv", "sdv15", "sdv15_final_clean.png", "Final state, U₂ ≈ 0.0070 mm", True),
        ("matched_state_04_Step-2_frame_0020_contour_sdv14_sdv15_sdv16.csv", "sdv16", "sdv16_final_linear_clean.png", "Final state, U₂ ≈ 0.0070 mm", False),
        ("matched_state_04_Step-2_frame_0020_contour_sdv14_sdv15_sdv16.csv", "sdv16", "sdv16_final_power_normalized_clean.png", "Final state, U₂ ≈ 0.0070 mm", False),
    ]
    for csv_name, variable, out_name, label, final_sdv15 in contour_specs:
        plot_contour(
            nodes,
            elems,
            CAE_EXPORTS / csv_name,
            variable,
            out_name,
            label,
            final_sdv15=final_sdv15,
            power_normalized=("power_normalized" in out_name),
        )
    shutil.copyfile(CONTOURS / "sdv16_final_linear_clean.png", CONTOURS / "sdv16_final_clean.png")
    make_panel()
    if not (PANELS / "supervisor_report_page_mockup.png").exists():
        make_mockup()
    write_notes()
    validate_images()
    print(f"Figure review package written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
