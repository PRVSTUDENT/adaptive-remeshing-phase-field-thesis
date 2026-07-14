#!/usr/bin/env python3
"""Generate figures and small tables for the Stage A baseline LaTeX report."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RUN_DIR = ROOT / "runs" / "molnar_single_notch_unchanged" / "20260714_technical_gate_local"
WORK_INP = RUN_DIR / "work" / "SingleNotch.inp"
EXTRACTED = RUN_DIR / "extracted"
SCIENTIFIC = RUN_DIR / "scientific_check"
FIG_DIR = ROOT / "results" / "figures" / "stage_a_baseline"
TABLE_DIR = ROOT / "results" / "tables" / "stage_a_baseline"


def ensure_dirs() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)


def parse_part_nodes_elements(inp_path: Path) -> tuple[dict[int, tuple[float, float]], dict[int, list[int]]]:
    nodes: dict[int, tuple[float, float]] = {}
    elements: dict[int, list[int]] = {}
    section: str | None = None
    with inp_path.open("r", encoding="utf-8", errors="replace") as stream:
        for raw_line in stream:
            line = raw_line.strip()
            if not line or line.startswith("**"):
                continue
            lower = line.lower()
            if lower.startswith("*assembly"):
                break
            if lower.startswith("*node"):
                section = "node"
                continue
            if lower.startswith("*element"):
                section = "element"
                continue
            if line.startswith("*"):
                section = None
                continue
            if section == "node":
                parts = [part.strip() for part in line.split(",") if part.strip()]
                if len(parts) >= 3:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif section == "element":
                parts = [part.strip() for part in line.split(",") if part.strip()]
                if len(parts) >= 5:
                    elements[int(parts[0])] = [int(item) for item in parts[1:5]]
    return nodes, elements


def element_centroids(nodes: dict[int, tuple[float, float]], elements: dict[int, list[int]]) -> dict[int, tuple[float, float]]:
    centroids: dict[int, tuple[float, float]] = {}
    for label, connectivity in elements.items():
        coords = [nodes[node] for node in connectivity if node in nodes]
        if coords:
            xs, ys = zip(*coords)
            centroids[label] = (float(np.mean(xs)), float(np.mean(ys)))
    return centroids


def save_rf_u_plot(curve: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    for step_name, step_rows in curve.groupby("step"):
        ax.plot(step_rows["rp_u2"], step_rows["rp_rf2"], marker="o", markersize=2.5, linewidth=1.2, label=step_name)
    peak_index = curve["rp_rf2"].idxmax()
    peak = curve.loc[peak_index]
    ax.scatter([peak["rp_u2"]], [peak["rp_rf2"]], s=45, color="black", zorder=3, label="extracted peak")
    ax.annotate(
        "peak RF2={:.4f}\nU2={:.4f}".format(peak["rp_rf2"], peak["rp_u2"]),
        xy=(peak["rp_u2"], peak["rp_rf2"]),
        xytext=(18, -30),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->", "linewidth": 0.8},
        fontsize=8,
    )
    ax.set_xlabel("RP displacement U2 [model units]")
    ax.set_ylabel("Reaction force RF2 [model units]")
    ax.set_title("Unchanged Molnar single-notch RF-U response")
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "single_notch_rf_u_curve.png", dpi=220)
    fig.savefig(FIG_DIR / "single_notch_rf_u_curve.pdf")
    plt.close(fig)


def save_rf_u_reference_status_plot(curve: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.plot(curve["rp_u2"], curve["rp_rf2"], color="#114b8a", marker="o", markersize=2.5, linewidth=1.2, label="unchanged SingleNotch")
    ax.text(
        0.03,
        0.08,
        "Molnar Fig. 7 numeric reference\nnot yet digitized or matched to\nsupplementary small model",
        transform=ax.transAxes,
        fontsize=8,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#777777", "alpha": 0.9},
    )
    ax.set_xlabel("RP displacement U2 [model units]")
    ax.set_ylabel("Reaction force RF2 [model units]")
    ax.set_title("RF-U comparison status")
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "single_notch_rf_u_reference_status.png", dpi=220)
    fig.savefig(FIG_DIR / "single_notch_rf_u_reference_status.pdf")
    plt.close(fig)


def save_phase_history_plot(curve: pd.DataFrame) -> None:
    fig, ax1 = plt.subplots(figsize=(6.2, 4.0))
    ax1.plot(curve["rp_u2"], curve["max_sdv15"], color="#0b6e69", marker="o", markersize=2.5, linewidth=1.2, label="max SDV15")
    ax1.plot(curve["rp_u2"], curve["max_sdv14"], color="#6a4c93", linewidth=1.0, linestyle="--", label="max SDV14")
    ax1.set_xlabel("RP displacement U2 [model units]")
    ax1.set_ylabel("Maximum phase field")
    ax1.grid(True, alpha=0.25)
    ax2 = ax1.twinx()
    ax2.plot(curve["rp_u2"], curve["max_sdv16"], color="#bf5700", linewidth=1.0, label="max SDV16")
    ax2.set_ylabel("Maximum history field H (SDV16)")
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, frameon=False, fontsize=8, loc="upper left")
    ax1.set_title("Phase/history evolution from unchanged benchmark")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "single_notch_phase_history_vs_u.png", dpi=220)
    fig.savefig(FIG_DIR / "single_notch_phase_history_vs_u.pdf")
    plt.close(fig)


def contour_dataframe(contour_csv: Path, centroids: dict[int, tuple[float, float]]) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    with contour_csv.open("r", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            element = int(row["element"])
            if element not in centroids:
                continue
            x, y = centroids[element]
            rows.append(
                {
                    "element": element,
                    "x": x,
                    "y": y,
                    "sdv14": float(row["sdv14"]),
                    "sdv15": float(row["sdv15"]),
                    "sdv16": float(row["sdv16"]),
                    "target_abs_u2": float(row["target_abs_u2"]),
                    "rp_u2": float(row["rp_u2"]),
                }
            )
    frame = pd.DataFrame(rows)
    return frame.groupby(["element", "x", "y", "target_abs_u2", "rp_u2"], as_index=False).mean()


def save_contour_plot(data: pd.DataFrame, path: Path, clipped: bool) -> None:
    values = data["sdv15"].clip(0.0, 1.0) if clipped else data["sdv15"]
    fig, ax = plt.subplots(figsize=(5.2, 5.0))
    scatter = ax.scatter(
        data["x"],
        data["y"],
        c=values,
        s=5,
        cmap="inferno",
        vmin=0.0 if clipped else None,
        vmax=1.0 if clipped else None,
        linewidths=0,
    )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    mode = "display-clipped 0<=d<=1" if clipped else "raw SDV15"
    ax.set_title("{} at U2={:.4f}".format(mode, float(data["rp_u2"].iloc[0])))
    cbar = fig.colorbar(scatter, ax=ax, shrink=0.82)
    cbar.set_label("SDV15 phase field")
    fig.tight_layout()
    fig.savefig(path.with_suffix(".png"), dpi=240)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)


def save_contour_figures(centroids: dict[int, tuple[float, float]]) -> None:
    for contour_csv in sorted(EXTRACTED.glob("matched_state_*_contour_sdv14_sdv15_sdv16.csv")):
        data = contour_dataframe(contour_csv, centroids)
        stem = contour_csv.stem.replace("_contour_sdv14_sdv15_sdv16", "")
        save_contour_plot(data, FIG_DIR / f"{stem}_raw_sdv15", clipped=False)
        save_contour_plot(data, FIG_DIR / f"{stem}_clipped_sdv15", clipped=True)


def save_crack_path_diagnostic(centroids: dict[int, tuple[float, float]]) -> None:
    contour_csv = EXTRACTED / "matched_state_04_Step-2_frame_0020_contour_sdv14_sdv15_sdv16.csv"
    if not contour_csv.exists():
        return
    data = contour_dataframe(contour_csv, centroids)
    damaged = data[data["sdv15"] >= 0.95]
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    ax.scatter(data["x"], data["y"], s=3, color="#dddddd", linewidths=0, label="all elements")
    if not damaged.empty:
        ax.scatter(damaged["x"], damaged["y"], s=8, color="#b00020", linewidths=0, label="SDV15 >= 0.95")
    ax.plot([0.0, 0.5], [0.0, 0.0], color="black", linestyle="--", linewidth=1.0, label="qualitative reference y=0")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Crack-path diagnostic at U2=0.007")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "single_notch_crack_path_diagnostic_u0007.png", dpi=240)
    fig.savefig(FIG_DIR / "single_notch_crack_path_diagnostic_u0007.pdf")
    plt.close(fig)


def save_tables(curve: pd.DataFrame, matched: pd.DataFrame) -> None:
    peak = curve.loc[curve["rp_rf2"].idxmax()]
    final = curve.iloc[-1]
    rows = [
        {"metric": "curve_rows", "value": len(curve)},
        {"metric": "peak_rf2", "value": peak["rp_rf2"]},
        {"metric": "u2_at_peak", "value": peak["rp_u2"]},
        {"metric": "final_u2", "value": final["rp_u2"]},
        {"metric": "final_rf2", "value": final["rp_rf2"]},
        {"metric": "final_max_sdv15", "value": final["max_sdv15"]},
        {"metric": "final_max_sdv16", "value": final["max_sdv16"]},
        {"metric": "min_sdv15_curve_summary", "value": curve["max_sdv15"].min()},
        {"metric": "max_sdv15_curve_summary", "value": curve["max_sdv15"].max()},
    ]
    pd.DataFrame(rows).to_csv(TABLE_DIR / "single_notch_summary_metrics.csv", index=False)
    matched.to_csv(TABLE_DIR / "single_notch_matched_states_for_report.csv", index=False)
    sci_json = SCIENTIFIC / "single_notch_scientific_check.json"
    if sci_json.exists():
        import json

        summary = json.loads(sci_json.read_text())
        bounds = summary["bounds_irreversibility"]
        pd.DataFrame(
            [
                {
                    "quantity": "SDV14",
                    "min": bounds["sdv14"]["min"],
                    "max": bounds["sdv14"]["max"],
                    "below_zero_count": bounds["sdv14"]["below_zero"],
                    "above_one_count": bounds["sdv14"]["above_one"],
                },
                {
                    "quantity": "SDV15",
                    "min": bounds["sdv15"]["min"],
                    "max": bounds["sdv15"]["max"],
                    "below_zero_count": bounds["sdv15"]["below_zero"],
                    "above_one_count": bounds["sdv15"]["above_one"],
                },
                {
                    "quantity": "SDV16",
                    "min": bounds["sdv16"]["min"],
                    "max": bounds["sdv16"]["max"],
                    "below_zero_count": "",
                    "above_one_count": "",
                },
            ]
        ).to_csv(TABLE_DIR / "single_notch_bounds_irreversibility_for_report.csv", index=False)


def main() -> None:
    ensure_dirs()
    curve = pd.read_csv(EXTRACTED / "single_notch_rf_u_phase_summary.csv")
    matched = pd.read_csv(EXTRACTED / "single_notch_matched_displacement_states.csv")
    save_rf_u_plot(curve)
    save_rf_u_reference_status_plot(curve)
    save_phase_history_plot(curve)
    nodes, elements = parse_part_nodes_elements(WORK_INP)
    centroids = element_centroids(nodes, elements)
    save_contour_figures(centroids)
    save_crack_path_diagnostic(centroids)
    save_tables(curve, matched)
    print(f"Wrote figures to {FIG_DIR}")
    print(f"Wrote tables to {TABLE_DIR}")


if __name__ == "__main__":
    main()
