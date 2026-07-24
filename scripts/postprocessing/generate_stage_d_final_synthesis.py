#!/usr/bin/env python3
"""Generate final Stage D figures, tables, metrics, and provenance."""

import csv
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/final/stage_d"
FIG = OUT / "figures"
TAB = OUT / "tables"
SEG = ROOT / "runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment"
A1 = ROOT / "runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_update"


def rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def savefig(name):
    path = FIG / name
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close()
    return path


def workflow():
    labels = ["D1", "D2A", "D2B", "D2C", "D3A3-R4", "D3D", "D3D-A1", "H0 limit"]
    subtitles = [
        "analytical\ntransfer", "Abaqus\ningestion", "serial\ncontinuation",
        "4-thread\nrepeatability", "nonmatching\nrelease hold",
        "fixed set\ndisproved", "offline KKT\ncorrection", "restart\nunknown",
    ]
    colors = ["#2f7d32"] * 5 + ["#b33a3a", "#2f7d32", "#8a6d1d"]
    fig, ax = plt.subplots(figsize=(12, 2.7))
    ax.set_xlim(-0.6, len(labels) - 0.4)
    ax.set_ylim(-0.7, 0.9)
    ax.axis("off")
    for i, (label, subtitle, color) in enumerate(zip(labels, subtitles, colors)):
        if i:
            ax.annotate("", xy=(i - 0.25, 0.2), xytext=(i - 0.75, 0.2),
                        arrowprops={"arrowstyle": "->", "lw": 1.6, "color": "#555"})
        ax.scatter(i, 0.2, s=1050, color=color, edgecolor="white", linewidth=2, zorder=3)
        label_size = 7 if len(label) > 4 else 9
        ax.text(i, 0.2, label, ha="center", va="center", color="white", weight="bold", fontsize=label_size)
        ax.text(i, -0.43, subtitle, ha="center", va="center", fontsize=8)
    ax.set_title("Stage D evidence workflow and final decision boundary", weight="bold")
    return savefig("stage_d_workflow.png")


def active_violations():
    candidates = rows(SEG / "D3D_ACTIVE_SET_UPDATE_CANDIDATES_BY_FRAME.csv")
    manifest = rows(SEG / "D3D_FRAME_MANIFEST.csv")
    u2 = {r["frame_tag"]: float(r["actual_top_u2_mean"]) for r in manifest}
    first_nodes = {}
    for record in candidates:
        first_nodes.setdefault(record["first_violating_frame"], set()).add(record["node"])
    counts = {tag: len(nodes) for tag, nodes in first_nodes.items()}
    tags = ["F4_segment_initial"] + [
        "F4_segment_inc_{:03d}".format(i) for i in range(1, 10)
    ] + ["F4_segment_end"]
    cumulative = []
    total = 0
    for tag in tags:
        total += counts.get(tag, 0)
        cumulative.append(total)
    assert cumulative[0] == 30 and cumulative[-1] == 3157
    plt.figure(figsize=(7.2, 4.3))
    plt.plot([u2[t] for t in tags], cumulative, marker="o", color="#b33a3a")
    plt.xlabel(r"Top displacement $U_2$ [mm]")
    plt.ylabel("Cumulative active nodes below multiplier threshold")
    plt.title(r"Fixed-active-set violations ($\lambda_\mathrm{active}<-10^{-8}$)")
    plt.grid(alpha=0.25)
    return savefig("violating_active_nodes_vs_displacement.png")


def multiplier():
    kkt = {r["frame_tag"]: r for r in rows(SEG / "D3D_PER_FRAME_KKT.csv")}
    manifest = rows(SEG / "D3D_FRAME_MANIFEST.csv")
    selected = [r for r in manifest if r["frame_tag"] in kkt and r["frame_tag"].startswith("F4_")]
    x = [float(r["actual_top_u2_mean"]) for r in selected]
    y = [float(kkt[r["frame_tag"]]["minimum_active_multiplier"]) for r in selected]
    plt.figure(figsize=(7.2, 4.3))
    plt.plot(x, y, marker="o", color="#6a3d9a", label="minimum active multiplier")
    plt.axhline(-1.0e-8, color="#b33a3a", linestyle="--", label=r"threshold $-10^{-8}$")
    plt.xlabel(r"Top displacement $U_2$ [mm]")
    plt.ylabel("Minimum active multiplier")
    plt.title("Loss of fixed-active-set dual admissibility")
    plt.grid(alpha=0.25)
    plt.legend()
    return savefig("minimum_active_multiplier_vs_displacement.png")


def convergence():
    data = rows(A1 / "D3D_A1_ACTIVE_SET_ITERATIONS.csv")
    it = [int(r["iteration"]) for r in data]
    active = [int(r["active_count"]) for r in data]
    free = [int(r["free_count"]) for r in data]
    residual = [float(r["free_residual_infinity_norm"]) for r in data]
    finite_residual = [value if math.isfinite(value) else math.nan for value in residual]
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.5), sharex=True)
    active_line = axes[0].plot(it, active, marker="o", label="active", color="#1f78b4")
    free_axis = axes[0].twinx()
    free_line = free_axis.plot(it, free, marker="s", label="free", color="#33a02c")
    axes[0].set_ylabel("Active nodes", color="#1f78b4")
    free_axis.set_ylabel("Free nodes", color="#33a02c")
    axes[0].set_ylim(min(active) - 5, max(active) + 5)
    free_axis.set_ylim(min(free) - 5, max(free) + 5)
    axes[0].legend(active_line + free_line, [line.get_label() for line in active_line + free_line])
    axes[0].grid(alpha=0.25)
    axes[1].semilogy(it, finite_residual, marker="o", color="#ff7f00", label="free residual")
    axes[1].axhline(1.0e-8, color="#b33a3a", linestyle="--", label=r"gate $10^{-8}$")
    axes[1].set_xlabel("Primal--dual iteration")
    axes[1].set_ylabel(r"$\|r_F\|_\infty$")
    axes[1].grid(alpha=0.25)
    axes[1].legend()
    fig.suptitle("D3D-A1 active-set convergence")
    return savefig("d3d_a1_active_set_convergence.png")


def released_nodes():
    data = rows(A1 / "D3D_A1_RELEASED_NODES.csv")
    seed = [r for r in data if r["initial_release_seed"].lower() == "true"]
    extra = [r for r in data if r["initial_release_seed"].lower() != "true"]
    assert len(seed) == 30 and len(extra) == 42
    plt.figure(figsize=(6.2, 5.4))
    plt.scatter([float(r["x"]) for r in extra], [float(r["y"]) for r in extra],
                s=30, color="#1f78b4", label="42 additional releases")
    plt.scatter([float(r["x"]) for r in seed], [float(r["y"]) for r in seed],
                s=45, marker="x", color="#e31a1c", label="30 initial seeds")
    plt.xlabel("x [mm]")
    plt.ylabel("y [mm]")
    plt.title("Spatial distribution of 72 released nodes")
    plt.axis("equal")
    plt.grid(alpha=0.2)
    plt.legend()
    return savefig("d3d_a1_released_nodes_spatial.png")


def tables_and_metrics():
    d1 = load(ROOT / "results/validation/stage_d_analytical_transfer/D1_ANALYTICAL_TRANSFER_RESULTS.json")
    r4 = load(ROOT / "runs/hpc/stage_d3/interrupted_transfer/D3A3_ACCEPTED_CLOSURE.json")
    d3d = load(SEG / "D3D_RESULT_CLOSURE.json")
    a1 = load(A1 / "D3D_A1_UPDATE_SUMMARY.json")
    metrics = {
        "classification": "stage_d_final_metrics_frozen",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "d1_phase_l2_error": d1["nodal_d"]["l2_error"],
        "d1_phase_max_error": d1["nodal_d"]["max_abs_error"],
        "d1_history_l2_error": d1["ip_H"]["l2_error"],
        "d1_history_max_error": d1["ip_H"]["max_abs_error"],
        "r4_sdv15_max_transfer_error": r4["accepted_metrics"]["sdv15_max_transfer_error"],
        "r4_sdv16_max_transfer_error": r4["accepted_metrics"]["sdv16_max_transfer_error"],
        "r4_rf_release_jump": r4["accepted_metrics"]["rf_release_jump"],
        "r4_energy_release_jump": r4["accepted_metrics"]["energy_release_jump"],
        "d3d_initial_violating_active_nodes": 30,
        "d3d_endpoint_violating_active_nodes": 3157,
        "d3d_minimum_active_multiplier": d3d["minimum_active_multiplier"],
        "a1_iterations": a1["iteration_count"],
        "a1_active_nodes": a1["final_active_nodes"],
        "a1_free_nodes": a1["final_free_nodes"],
        "a1_free_residual_infinity_norm": a1["free_residual_infinity_norm"],
        "a1_minimum_active_multiplier": a1["minimum_active_multiplier"],
        "a1_active_bound_error": a1["active_bound_error"],
        "a1_phase_decrease_violations": a1["phase_decrease_violations"],
        "a1_non_positive_detJ": a1["non_positive_detJ"],
        "corrected_mechanical_restart": "unproven",
    }
    (OUT / "STAGE_D_FINAL_METRICS.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    transfer_rows = [
        ("D1 phase coverage", d1["nodal_d"]["coverage"], "proven"),
        ("D1 history coverage", d1["ip_H"]["coverage"], "proven"),
        ("R4 phase transfer max error", r4["accepted_metrics"]["sdv15_max_transfer_error"], "<=1e-8"),
        ("R4 history transfer max error", r4["accepted_metrics"]["sdv16_max_transfer_error"], "<=1e-8"),
        ("R4 RF release jump", r4["accepted_metrics"]["rf_release_jump"], "<=1%"),
        ("R4 energy release jump", r4["accepted_metrics"]["energy_release_jump"], "<=1%"),
        ("D3D-A1 free residual", a1["free_residual_infinity_norm"], "<=1e-8"),
        ("D3D-A1 minimum multiplier", a1["minimum_active_multiplier"], ">=-1e-8"),
        ("D3D-A1 active-bound error", a1["active_bound_error"], "<=1e-10"),
        ("D3D-A1 phase decrease violations", a1["phase_decrease_violations"], "0"),
        ("D3D-A1 non-positive detJ", a1["non_positive_detJ"], "0"),
    ]
    with (TAB / "transfer_validation_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value", "gate_or_status"])
        writer.writerows(transfer_rows)
    execution = [
        ("1378003", "line-ending checksum mismatch", "no", "none"),
        ("1378004", "Python 3.8 syntax under Python 3.6", "no", "none"),
        ("1378005", "git unavailable after module loading", "no", "mechanical checkpoint unknown"),
    ]
    with (TAB / "execution_qualification_failures.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["job", "failure", "abaqus_reached", "scientific_consequence"])
        writer.writerows(execution)
    return metrics


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    figures = [workflow(), active_violations(), multiplier(), convergence(), released_nodes()]
    metrics = tables_and_metrics()
    source_files = [
        "runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment/D3D_ACTIVE_SET_UPDATE_CANDIDATES_BY_FRAME.csv",
        "runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment/D3D_PER_FRAME_KKT.csv",
        "runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment/D3D_FRAME_MANIFEST.csv",
        "runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_update/D3D_A1_ACTIVE_SET_ITERATIONS.csv",
        "runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_update/D3D_A1_RELEASED_NODES.csv",
        "runs/hpc/stage_d3/interrupted_transfer/D3A3_ACCEPTED_CLOSURE.json",
        "results/validation/stage_d_analytical_transfer/D1_ANALYTICAL_TRANSFER_RESULTS.json",
    ]
    provenance = {
        "classification": "stage_d_final_figure_provenance_complete",
        "source_commit": metrics["source_commit"],
        "generation_script": "scripts/postprocessing/generate_stage_d_final_synthesis.py",
        "source_files": source_files,
        "figures": {
            str(path.relative_to(ROOT)).replace("\\", "/"): {
                "scientific_classification": "descriptive_from_committed_evidence",
                "manual_scientific_edits": False,
            }
            for path in figures
        },
        "axis_definitions": {
            "violating_active_nodes_vs_displacement.png": "x=top U2 [mm]; y=cumulative active nodes with multiplier below -1e-8",
            "minimum_active_multiplier_vs_displacement.png": "x=top U2 [mm]; y=minimum active multiplier; horizontal gate=-1e-8",
            "d3d_a1_active_set_convergence.png": "x=iteration; y=node counts and free residual infinity norm",
            "d3d_a1_released_nodes_spatial.png": "x,y=target-mesh coordinates [mm]; groups=30 seeds and 42 additional releases",
            "stage_d_workflow.png": "ordered evidence stages and decision outcome",
        },
    }
    (OUT / "FIGURE_PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"figures": len(figures), "tables": 2, "classification": provenance["classification"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
