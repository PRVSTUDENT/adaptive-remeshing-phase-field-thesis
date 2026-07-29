#!/usr/bin/env python
"""Generate derived summaries and figures from genuine Abaqus ODB extracted MISESERI evidence.

Target Job: 1379579.mmaster02
Input Evidence: runs/hpc/stage_f/miseseri_preanalysis/evidence/1379579.mmaster02/miseseri_preanalysis_elements.csv

Generates:
  1. Summary JSON: runs/hpc/stage_f/miseseri_preanalysis/evidence/1379579.mmaster02/MISESERI_EVIDENCE_SUMMARY.json
  2. Figures in results/figures/miseseri_preanalysis/1379579.mmaster02/:
     - miseseri_raw_contour.png (with stress units)
     - miseseri_normalized_contour.png (labeled project diagnostic)
     - miseseri_refinement_zone.png (percentile hotspot regions: top 10%, top 5%, top 1%)
     - miseseri_notch_tip_closeup.png
"""

from __future__ import print_function

import csv
import json
import math
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.postprocessing.export_miseseri_preanalysis_csv import (
    percentile,
    quantify_miseseri_field,
)


def read_extracted_csv(csv_path):
    rows = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(
                {
                    "physical_element_label": int(r["physical_element_label"]),
                    "visualization_element_label": int(r["visualization_element_label"]),
                    "centroid_x": float(r["centroid_x"]),
                    "centroid_y": float(r["centroid_y"]),
                    "MISESERI": float(r["MISESERI"]),
                    "MISESAVG": float(r["MISESAVG"]) if r.get("MISESAVG") != "" else None,
                    "EVOL": float(r["EVOL"]) if r.get("EVOL") != "" else None,
                    "von_mises": float(r["von_mises"]) if r.get("von_mises") != "" else None,
                    "SDV15": float(r["SDV15"]) if r.get("SDV15") != "" else None,
                    "n1": int(r["n1"]),
                    "n2": int(r["n2"]),
                    "n3": int(r["n3"]),
                    "n4": int(r["n4"]),
                }
            )
    return rows


def main():
    evidence_dir = os.path.join(REPO_ROOT, "runs", "hpc", "stage_f", "miseseri_preanalysis", "evidence", "1379579.mmaster02")
    csv_path = os.path.join(evidence_dir, "miseseri_preanalysis_elements.csv")
    tech_path = os.path.join(evidence_dir, "MISESERI_TECHNICAL_SUMMARY.json")

    if not os.path.exists(csv_path):
        print("ERROR: Extracted evidence CSV not found at %s" % csv_path, file=sys.stderr)
        return 1

    rows = read_extracted_csv(csv_path)
    print("Loaded %d extracted element rows from %s" % (len(rows), csv_path))

    u_final = None
    rf_final = None
    if os.path.exists(tech_path):
        with open(tech_path, "r") as f:
            tech = json.load(f)
            u_final = tech.get("U1_final", tech.get("U_final"))
            rf_final = tech.get("RF1_final", tech.get("RF_final"))

    # Compute quantified metrics from actual extracted rows
    metrics = quantify_miseseri_field(
        rows,
        target_disp=0.001,
        target_tol=1.0e-4,
        disp_comp=1,
        rf_comp=1,
        u_final=u_final,
        rf_final=rf_final,
        expected_elements=3930,
    )

    # Add explicit Pandey-Kumar paper vs project parameter provenance
    metrics["pandey_kumar_provenance"] = {
        "paper_listing_1": {
            "errorTarget": 1.0,
            "refinementFactor": 10,
            "coarseningFactor": "NOT_ALLOWED",
            "variables": ["MISESERI"],
        },
        "paper_narrative": "Example error targets lie between 1% and 5% depending on problem.",
        "project_selected_parameters": {
            "errorTarget": "5%",
            "refinementFactor": 2,
            "minElementSize_mm": 0.0025,
            "maxElementSize_mm": 0.025,
            "note": "Project-selected remeshing parameters, not directly copied from Paper Listing 1.",
        },
        "scientific_interpretation_rule": (
            "Raw MISESERI values have stress units (MPa or GPa). "
            "Raw MISESERI >= 0.05 is NOT automatically a 5% Abaqus errorTarget. "
            "Refinement rules must ultimately come from Abaqus RemeshingRule."
        ),
    }

    summary_json = os.path.join(evidence_dir, "MISESERI_EVIDENCE_SUMMARY.json")
    with open(summary_json, "w") as f:
        json.dump(metrics, f, indent=2, sort_keys=True)
        f.write("\n")
    print("Wrote updated summary JSON to %s" % summary_json)

    # Generate Lightweight Figures
    fig_dir = os.path.join(REPO_ROOT, "results", "figures", "miseseri_preanalysis", "1379579.mmaster02")
    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        xc_all = [r["centroid_x"] for r in rows]
        yc_all = [r["centroid_y"] for r in rows]
        val_all = [r["MISESERI"] for r in rows]
        max_val = max(val_all)
        norm_val_all = [v / max_val for v in val_all]

        # Percentile thresholds
        sorted_vals = sorted(val_all)
        p90 = percentile(sorted_vals, 90.0)
        p95 = percentile(sorted_vals, 95.0)
        p99 = percentile(sorted_vals, 99.0)

        # 1. Raw MISESERI Contour Plot (with stress units)
        fig, ax = plt.subplots(figsize=(7, 6))
        sc = ax.scatter(xc_all, yc_all, c=val_all, cmap="viridis", s=6, edgecolors="none")
        plt.colorbar(sc, ax=ax, label="MISESERI Stress Recovery Error Indicator (GPa)")
        ax.plot(0, 0, "ro", markersize=8, label="Notch Tip (0,0)")
        ax.plot([-0.5, 0], [0, 0], "r--", linewidth=2, label="True Notch Slit")
        ax.set_title("Mode-II Genuine ODB MISESERI Field (U1 = 0.001 mm)")
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.legend(loc="upper right")
        ax.set_aspect("equal")
        plt.tight_layout()
        fig.savefig(os.path.join(fig_dir, "miseseri_raw_contour.png"), dpi=200)
        plt.close(fig)

        # 2. Normalized MISESERI Contour Plot (Project Diagnostic)
        fig, ax = plt.subplots(figsize=(7, 6))
        sc = ax.scatter(xc_all, yc_all, c=norm_val_all, cmap="plasma", s=6, edgecolors="none", vmin=0, vmax=1)
        plt.colorbar(sc, ax=ax, label=r"Project Diagnostic ($\eta_e = \mathrm{MISESERI}_e / \mathrm{max}$)")
        ax.plot(0, 0, "ro", markersize=8, label="Notch Tip")
        ax.set_title(r"Normalized MISESERI Field (Project Diagnostic, not RemeshingRule)")
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.legend(loc="upper right")
        ax.set_aspect("equal")
        plt.tight_layout()
        fig.savefig(os.path.join(fig_dir, "miseseri_normalized_contour.png"), dpi=200)
        plt.close(fig)

        # 3. Percentile Hotspot Regions Plot (Top 10%, Top 5%, Top 1%)
        fig, ax = plt.subplots(figsize=(7, 6))
        bg_xc = [r["centroid_x"] for r in rows if r["MISESERI"] < p90]
        bg_yc = [r["centroid_y"] for r in rows if r["MISESERI"] < p90]
        p90_xc = [r["centroid_x"] for r in rows if p90 <= r["MISESERI"] < p95]
        p90_yc = [r["centroid_y"] for r in rows if p90 <= r["MISESERI"] < p95]
        p95_xc = [r["centroid_x"] for r in rows if p95 <= r["MISESERI"] < p99]
        p95_yc = [r["centroid_y"] for r in rows if p95 <= r["MISESERI"] < p99]
        p99_xc = [r["centroid_x"] for r in rows if r["MISESERI"] >= p99]
        p99_yc = [r["centroid_y"] for r in rows if r["MISESERI"] >= p99]

        ax.scatter(bg_xc, bg_yc, c="lightgray", s=4, label="Lower 90%")
        ax.scatter(p90_xc, p90_yc, c="gold", s=8, label="Top 10% (P90)")
        ax.scatter(p95_xc, p95_yc, c="darkorange", s=10, label="Top 5% (P95)")
        ax.scatter(p99_xc, p99_yc, c="crimson", s=14, label="Top 1% (P99)")
        ax.plot(0, 0, "ko", markersize=8, label="Notch Tip")
        ax.set_title("MISESERI Percentile Hotspot Regions (Genuine ODB)")
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.legend(loc="upper right")
        ax.set_aspect("equal")
        plt.tight_layout()
        fig.savefig(os.path.join(fig_dir, "miseseri_refinement_zone.png"), dpi=200)
        plt.close(fig)

        # 4. Notch-Tip Close-Up Plot
        fig, ax = plt.subplots(figsize=(7, 6))
        sc = ax.scatter(xc_all, yc_all, c=val_all, cmap="viridis", s=18, edgecolors="none")
        plt.colorbar(sc, ax=ax, label="MISESERI Error Indicator (GPa)")
        ax.plot(0, 0, "ro", markersize=10, label="Notch Tip (0,0)")
        ax.plot([-0.5, 0], [0, 0], "r-", linewidth=3, label="Notch Slit")
        ax.set_xlim(-0.1, 0.1)
        ax.set_ylim(-0.1, 0.1)
        ax.set_title("MISESERI Notch-Tip Close-Up Field (r <= 0.1 mm)")
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.legend(loc="upper right")
        ax.set_aspect("equal")
        plt.tight_layout()
        fig.savefig(os.path.join(fig_dir, "miseseri_notch_tip_closeup.png"), dpi=200)
        plt.close(fig)

        print("Generated 4 lightweight figures in %s" % fig_dir)
    except Exception as exc:
        print("WARN: Matplotlib plotting failed or skipped: %s" % exc, file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
