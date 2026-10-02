import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

WORK = Path(r"D:\Master thesis\Adaptive remeshing\project_coordination\work\F1043")
FIG = WORK / "figures"
FIG.mkdir(parents=True, exist_ok=True)

# Colors matching report palette
NAVY = "#17365D"
BLUE = "#2F75B5"
LIGHT_BLUE = "#5B9BD5"
DARK_GRAY = "#262626"
GRAY = "#595959"
ORANGE = "#C55A11"
GREEN = "#548235"
PURPLE = "#7030A0"

# Mesh definitions and metrics from authoritative project evidence
MESHES = [
    {"name": r"$h=0.00300$ mm (15,192 elements)", "h": 0.00300, "elem": 15192, "job": "1401527",
     "K0": 137.9455, "Fmax": 0.757778, "u_peak": 0.005857, "u_end": 0.010000, "W_common": 2.3583,
     "color": "#1F4E79", "ls": "-", "lw": 2.2, "marker": "s"},
    {"name": r"$h=0.00200$ mm (32,130 elements)", "h": 0.00200, "elem": 32130, "job": "1401528",
     "K0": 137.8941, "Fmax": 0.741194, "u_peak": 0.005711, "u_end": 0.006816, "W_common": 2.2480,
     "color": "#2F75B5", "ls": "-", "lw": 2.0, "marker": "o"},
    {"name": r"$h=0.00150$ mm (41,912 elements)", "h": 0.00150, "elem": 41912, "job": "1401529",
     "K0": 137.8576, "Fmax": 0.732196, "u_peak": 0.005633, "u_end": 0.007836, "W_common": 2.1901,
     "color": "#548235", "ls": "-", "lw": 1.9, "marker": "^"},
    {"name": r"$h=0.00125$ mm (51,408 elements)", "h": 0.00125, "elem": 51408, "job": "1402827",
     "K0": 137.8368, "Fmax": 0.729041, "u_peak": 0.005606, "u_end": 0.007208, "W_common": 2.1701,
     "color": "#C55A11", "ls": "-", "lw": 1.9, "marker": "D"},
    {"name": r"$h=0.00100$ mm (69,384 elements)", "h": 0.00100, "elem": 69384, "job": "1402828",
     "K0": 137.8233, "Fmax": 0.725460, "u_peak": 0.005575, "u_end": 0.009580, "W_common": 2.1475,
     "color": "#7030A0", "ls": "-", "lw": 2.0, "marker": "v"},
]

def generate_figure_a():
    """Plot only the preserved scalar metrics; do not synthesize full curves."""
    elems = np.array([m["elem"] for m in MESHES], dtype=float)
    fmax = np.array([m["Fmax"] for m in MESHES], dtype=float)
    upeak = np.array([m["u_peak"] * 1000.0 for m in MESHES], dtype=float)
    k0 = np.array([m["K0"] for m in MESHES], dtype=float)
    colors = [m["color"] for m in MESHES]

    fig, axes = plt.subplots(1, 3, figsize=(12.2, 4.0), dpi=300)
    panels = [
        (axes[0], fmax, r"Peak force $F_{\max}$ [kN]", "(a) Peak force"),
        (axes[1], upeak, r"Displacement at peak [$\mu$m]", "(b) Peak displacement"),
        (axes[2], k0, r"Initial stiffness $K_0$ [kN/mm]", "(c) Initial stiffness"),
    ]
    for ax, values, ylabel, title in panels:
        ax.plot(elems, values, color=BLUE, lw=1.8, zorder=2)
        ax.scatter(elems, values, c=colors, s=48, edgecolor="white", linewidth=0.7, zorder=3)
        ax.set_xlabel("Finite-element count", fontsize=9.5)
        ax.set_ylabel(ylabel, fontsize=9.5)
        ax.set_title(title, fontsize=10.5, weight="bold", color=NAVY)
        ax.grid(True, ls=":", alpha=0.5)
        ax.ticklabel_format(axis="x", style="plain")
        ax.tick_params(axis="x", labelrotation=25)

    axes[0].text(0.05, 0.08, "Monotonic decrease;\nstrict asymptotic convergence not claimed",
                 transform=axes[0].transAxes, fontsize=7.7, color=GRAY)
    axes[1].text(0.05, 0.08, "Fracture-initiation timing\nremains mesh-sensitive",
                 transform=axes[1].transAxes, fontsize=7.7, color=GRAY)
    axes[2].text(0.05, 0.08, r"Total variation $\approx 0.089\%$",
                 transform=axes[2].transAxes, fontsize=7.7, color=GRAY)

    fig.tight_layout()
    plt.savefig(FIG / "fig_convergence_fu_overlay.png", dpi=300)
    plt.close()
    print("Generated Figure A: fig_convergence_fu_overlay.png")

def generate_figure_b():
    """Show external work and successive changes without claiming an order."""
    elems = np.array([m["elem"] for m in MESHES], dtype=float)
    work = np.array([m["W_common"] for m in MESHES], dtype=float)
    fmax = np.array([m["Fmax"] for m in MESHES], dtype=float)
    colors = [m["color"] for m in MESHES]
    work_change = np.abs(np.diff(work) / work[:-1]) * 100.0
    peak_change = np.abs(np.diff(fmax) / fmax[:-1]) * 100.0
    step_labels = ["0.0030->0.0020", "0.0020->0.0015", "0.0015->0.00125", "0.00125->0.0010"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.0), dpi=300)
    ax1.plot(elems, work, color=BLUE, lw=1.9, zorder=2)
    ax1.scatter(elems, work, c=colors, s=52, edgecolor="white", linewidth=0.7, zorder=3)
    ax1.set_xlabel("Finite-element count", fontsize=9.5)
    ax1.set_ylabel(r"Common-interval external work $W_{\mathrm{ext}}$ [mJ]", fontsize=9.5)
    ax1.set_title(r"(a) $W_{\mathrm{ext}}$ at $u_{\mathrm{common}}=0.006816$ mm", fontsize=10.5, weight="bold", color=NAVY)
    ax1.grid(True, ls=":", alpha=0.5)
    ax1.tick_params(axis="x", labelrotation=25)
    ax1.text(0.05, 0.08, "Monotonic decrease: 2.3583 -> 2.1475 mJ\nNo formal asymptotic order is claimed",
             transform=ax1.transAxes, fontsize=7.8, color=GRAY)

    x = np.arange(len(step_labels))
    width = 0.36
    ax2.bar(x - width / 2, peak_change, width, label=r"$F_{\max}$", color=BLUE)
    ax2.bar(x + width / 2, work_change, width, label=r"$W_{\mathrm{ext}}$", color=ORANGE)
    ax2.set_xticks(x)
    ax2.set_xticklabels(step_labels, rotation=24, ha="right", fontsize=8.0)
    ax2.set_ylabel("Successive relative change [%]", fontsize=9.5)
    ax2.set_title("(b) Successive changes", fontsize=10.5, weight="bold", color=NAVY)
    ax2.grid(True, axis="y", ls=":", alpha=0.5)
    ax2.legend(frameon=False, fontsize=8.5)
    ax2.text(0.05, 0.92, "Final step is slightly larger than the preceding step",
             transform=ax2.transAxes, fontsize=7.7, color=GRAY, va="top")

    fig.tight_layout()
    plt.savefig(FIG / "fig_convergence_work_and_spatial.png", dpi=300)
    plt.close()
    print("Generated Figure B: fig_convergence_work_and_spatial.png")

if __name__ == "__main__":
    generate_figure_a()
    generate_figure_b()
