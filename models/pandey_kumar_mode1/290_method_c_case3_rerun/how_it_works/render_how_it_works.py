"""Generate a silent, schematic Method C explainer; no solver data are rendered.

Run from the repository root. Requires matplotlib, Pillow and ffmpeg. Geometry
and reported Case 3 milestones are read from committed JSON; the eight-cell mesh
is an illustrative toy and is not a reconstruction of a simulation result.
"""
import io
import json
import pathlib
import subprocess
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
from PIL import Image

REV = "860f462a95c27a3c936fb282916206b7dfcfc4a3"
ROOT = pathlib.Path("models/pandey_kumar_mode1/290_method_c_case3_rerun")
FRAMES = ROOT / "how_it_works/frames"
VIDEO = ROOT / "video_method_c_how_it_works.mp4"
DURATIONS = [3, 5, 7, 5, 7, 9, 9, 6, 8, 6, 7, 7]
NAVY, BLUE, TEAL, PAPER = "#152a40", "#2079aa", "#087f75", "#f5f8fb"
CMAP = matplotlib.colormaps["turbo"]


def committed(path):
    return json.loads(subprocess.check_output(["git", "show", f"{REV}:{path}"]))


def page(number, title, caption, tag=None):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=PAPER)
    fig.patches.append(Rectangle((0, .895), 1, .105, transform=fig.transFigure, facecolor=NAVY, zorder=-1))
    fig.text(.04, .94, title, fontsize=27, color="white", weight="bold", va="center")
    fig.text(.96, .94, f"{number:02d} / 12", fontsize=16, color="#c5d4e1", va="center", ha="right")
    if tag:
        fig.text(.04, .86, tag, fontsize=15, color="#28729c", weight="bold")
    fig.patches.append(Rectangle((.035, .035), .93, .15, transform=fig.transFigure, facecolor="#e5eef5", edgecolor="none", zorder=-1))
    fig.text(.055, .11, caption, fontsize=19, color=NAVY, va="center", linespacing=1.4)
    return fig


def axblank(fig, rect):
    ax = fig.add_axes(rect); ax.set_axis_off(); return ax


def panel_text(fig, x, y, text, size=20, color=NAVY, weight="normal", **kw):
    fig.text(x, y, text, fontsize=size, color=color, weight=weight, **kw)


def cbar(fig, rect):
    ax = fig.add_axes(rect)
    bar = matplotlib.colorbar.ColorbarBase(ax, cmap=CMAP, norm=colors.Normalize(0, 1), orientation="horizontal")
    bar.set_ticks([0, .5, 1]); bar.set_label("damage d", fontsize=13); bar.ax.tick_params(labelsize=12)


def toy(ax, refined=0, advance=0, highlighted=False, pale=False, arrows=False):
    """4×2 parent grid: col 0 is initial tip; refine first `refined` columns."""
    ax.set_xlim(-.2, 4.25); ax.set_ylim(-.25, 2.7); ax.set_aspect("equal"); ax.axis("off")
    for col in range(4):
        for row in range(2):
            val = 1.0 if col <= advance else (.5 if col == advance + 1 else 0.0)
            n = 2 if col < refined else 1
            for i in range(n):
                for j in range(n):
                    ax.add_patch(Rectangle((col + i/n, row + j/n), 1/n, 1/n,
                        facecolor="#e7edf2" if pale else CMAP(val), edgecolor="white", lw=1.7))
            if highlighted and val >= .5:
                ax.add_patch(Rectangle((col, row), 1, 1, fill=False, edgecolor="#172d42", lw=3))
    ax.add_patch(Rectangle((0, 0), 4, 2, fill=False, edgecolor=NAVY, lw=2))
    tip = advance + 1
    ax.plot([0, tip], [1, 1], color="white", lw=7, solid_capstyle="round", zorder=5)
    ax.plot([0, tip], [1, 1], color="#9b1928", lw=2.4, zorder=6)
    if highlighted:
        ax.add_patch(Rectangle((-.07, -.07), 2.14, 2.14, fill=False, edgecolor="#f18b32", ls="--", lw=3))
    if arrows:
        for x in (.5, 1.5, 2.5, 3.5):
            ax.annotate("", (x, 2.06 + .30*float(arrows)), (x, 2.06), arrowprops=dict(arrowstyle="-|>", lw=1.8, color=BLUE))
    expected = 8 + 6 * refined
    return expected


def toy_main(fig, refined=0, advance=0, highlighted=False, arrows=False):
    ax = axblank(fig, [.075, .26, .58, .52]); count = toy(ax, refined, advance, highlighted, arrows=arrows)
    panel_text(fig, .70, .72, f"Elements: {count}", 27, weight="bold")
    panel_text(fig, .70, .62, "Refined element size\nh_ref = 0.5 (fixed)", 19, linespacing=1.5)
    cbar(fig, [.16, .235, .39, .018])
    return ax


def geometry(fig, config, path=False, milestones=None):
    ax = fig.add_axes([.28, .21, .42, .63]); ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-48, 135); ax.set_ylim(-5, 125)
    ax.add_patch(Rectangle((0, 0), 65, 120, facecolor="white", edgecolor=NAVY, lw=2))
    ax.plot([0, 10], [70, 70], color="#ad2938", lw=4)
    for h in config["geometry"]["voids"]:
        ax.add_patch(Circle((h["x"], h["y"]), h["r"], facecolor=PAPER, edgecolor=NAVY, lw=2))
    ax.annotate("", (20, 116), (20, 103), arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=3))
    ax.annotate("Upper pin: pull u₂; u₁ = 0", (20, 100), (-45, 120), fontsize=13, arrowprops=dict(arrowstyle="->"))
    ax.annotate("Lower pin fixed\nu₁ = u₂ = 0", (20, 20), (-46, 15), fontsize=13, arrowprops=dict(arrowstyle="->"))
    ax.annotate("Notch a₀ = 10 mm\ny = 70 mm", (8, 70), (-45, 70), fontsize=13, arrowprops=dict(arrowstyle="->"))
    ax.annotate("Pin holes R = 5 mm", (25, 100), (74, 102), fontsize=13, arrowprops=dict(arrowstyle="->"))
    ax.annotate("Central hole R = 10 mm", (46.5, 51), (74, 55), fontsize=13, arrowprops=dict(arrowstyle="->"))
    if path:
        # Conceptual path, not a field plot or a numerically reconstructed contour.
        ax.plot([10, 18, 26, 32, 36.5], [70, 69, 67, 64, 61], color="#cf343d", lw=4, solid_capstyle="round")
        ax.plot([46.5, 51, 57, 62, 65], [51, 51.3, 51.7, 51.85, 52], color="#cf343d", lw=4, solid_capstyle="round")
        ax.plot([64.14], [51.86], marker="o", ms=8, color="#f3a833", markeredgecolor=NAVY)
        ax.plot([65], [52], marker="*", ms=14, color="#cf343d", markeredgecolor="white")
    return ax


def main():
    cfg = committed("configs/remeshing/f1728_case3_notched_plate_pins.json")
    summary = committed("models/pandey_kumar_mode1/290_method_c_case3_rerun/METHOD_C_CASE3_RERUN_SUMMARY.json")
    assert cfg["loading"]["loading_type"] == "PIN_HOLE_PULL"
    assert (cfg["geometry"]["plate_width"], cfg["geometry"]["plate_height"]) == (65, 120)
    assert summary["evaluation_mode"] == "RE_EVALUATION_OF_ORIGINAL_TRAJECTORY_UNDER_FIXED_STOPPING_LOGIC"
    milestones = {r["cycle_idx"]: r for r in summary["cycle_comparison_table"]}
    c52, c53 = milestones[52], milestones[53]
    assert summary["improved_framework_rerun"]["adaptive_remesh_steps"] == 53
    FRAMES.mkdir(parents=True, exist_ok=True)
    paths = [FRAMES / f"scene_{i:02}.png" for i in range(1, 13)]
    if VIDEO.exists() or any(p.exists() for p in paths): raise FileExistsError("Output exists; refusing overwrite")
    figures = []
    fig = page(1, "How Method C Works", "Solve → remesh → transfer → re-equilibrate → advance. Repeat one cycle at a time.")
    panel_text(fig, .12, .66, "Adaptive remeshing\nwith history transfer", 42, weight="bold", linespacing=1.3)
    panel_text(fig, .12, .43, "A visual guide using the Case 3 plate", 25, color="#377398")
    panel_text(fig, .12, .33, "Silent explainer  •  conceptual mesh diagrams", 18, color="#5b6f80")
    figures.append(fig)

    fig = page(2, "The problem | Case 3", "A notched plate is pulled through the upper pin hole; the lower pin hole is fixed.")
    geometry(fig, cfg)
    panel_text(fig, .05, .23, "65 × 120 mm plate\nE = 210 GPa   ν = 0.3\nℓ₀ = 0.285 mm   Gc = 0.00228 kN/mm", 17, linespacing=1.55)
    figures.append(fig)

    fig = page(3, "Cycle 0 | Coarse mesh", "The solver finds the response. Damage d and history H develop near the crack tip.", "SIMPLIFIED CONCEPTUAL MESH • NOT THE CASE 3 MESH")
    toy_main(fig, arrows=True); figures.append(fig)

    fig = page(4, "Damage marks the region to refine", "In this toy example, elements with d ≥ 0.5 mark a corridor around the crack.\nThe F1852 driver uses the damage-envelope branch once maximum damage reaches 0.5.", "SIMPLIFIED CONCEPTUAL MESH • MARKED REGION IS ILLUSTRATIVE")
    toy_main(fig, highlighted=True); panel_text(fig, .70, .47, "Dashed outline:\nillustrative corridor", 18, color="#ae6017"); figures.append(fig)

    fig = page(5, "Cycle 1 | Remesh", "The tip region gets more elements of the same fixed small size.\nThe number of elements grows; h_ref does not shrink.", "SIMPLIFIED CONCEPTUAL MESH")
    toy_main(fig, refined=1); figures.append(fig)

    fig = page(6, "Transfer damage and history", "Python interpolates nodal displacement u and damage d, and Gauss-point history H,\nfrom the old mesh to the new mesh. The transfer is not Abaqus *MAP SOLUTION.", "SIMPLIFIED CONCEPTUAL MESH • INHERITANCE IS ILLUSTRATIVE")
    left=axblank(fig,[.045,.32,.39,.38]);toy(left);right=axblank(fig,[.565,.32,.39,.38]);toy(right,refined=1,pale=True)
    panel_text(fig,.11,.75,"Old mesh | 8 elements",18,weight="bold");panel_text(fig,.63,.75,"New mesh | 14 elements",18,weight="bold")
    arrow=FancyArrowPatch((.46,.51),(.55,.51),transform=fig.transFigure,arrowstyle="-|>",mutation_scale=28,lw=3,color=BLUE);fig.add_artist(arrow)
    panel_text(fig,.465,.58,"u, d, H",16,color=BLUE,weight="bold");cbar(fig,[.33,.23,.34,.018])
    # Only the post-transfer state is saved as the scene PNG.  A matching
    # uncoloured schematic is rendered in memory for the first three seconds.
    before=io.BytesIO();fig.savefig(before,format='png',dpi=100,facecolor=fig.get_facecolor());before.seek(0)
    before_transfer=Image.open(before).convert('RGB').tobytes()
    toy(right,refined=1);figures.append(fig)

    fig = page(7, "Step 1 | Re-equilibrate at the same load", "Hold the load fixed and solve for equilibrium on the new mesh.\nCompare reaction forces against the transfer gate; a check can fail.", "SIMPLIFIED CONCEPTUAL MESH")
    ax=toy_main(fig,refined=1,arrows=True)
    for x,y in [(1.5,.5),(2.5,.5),(3.5,.5),(1.5,1.5),(2.5,1.5),(3.5,1.5)]:
        ax.annotate("",(x+.12,y+.12),(x,y),arrowprops=dict(arrowstyle="->",lw=1.2,color="white"))
    panel_text(fig,.69,.50,"External pull\n        ↕ balance\nInternal resistance",18,linespacing=1.5)
    panel_text(fig,.69,.28,"Example gate: |ΔRF2| ≤ 5%\nCase 3 Cycle 1: −11.31% (failed)",16,color="#a43b35",linespacing=1.5)
    figures.append(fig)

    fig = page(8, "Step 2 | Advance the load", "The load advances with RIKS. In this illustration the crack extends and damage spreads.", "SIMPLIFIED CONCEPTUAL MESH")
    toy_main(fig,refined=1,advance=1,arrows=1.8);panel_text(fig,.70,.45,"Load ↑\nCrack advances →",20,color=BLUE,linespacing=1.5,weight="bold");figures.append(fig)

    fig = page(9, "Cycle 2 | Repeat the loop", "Refine at the new tip, transfer the state, hold the load to re-equilibrate, then advance.", "SIMPLIFIED CONCEPTUAL MESH")
    toy_main(fig,refined=2,advance=1);panel_text(fig,.69,.46,"Refine → transfer\n→ hold → advance",19,color=TEAL,linespacing=1.6,weight="bold");figures.append(fig)

    fig = page(10, "Cycle 3 | The refined band follows", "More fixed-size elements follow the crack. The toy damage field never heals.", "SIMPLIFIED CONCEPTUAL MESH")
    toy_main(fig,refined=3,advance=2);panel_text(fig,.69,.45,"8 → 14 → 20 → 26\nh_ref stays fixed",20,color=TEAL,linespacing=1.5,weight="bold");figures.append(fig)

    fig = page(11, "Case 3 | Full trajectory and stopping", "A revised rule stops at Cycle 53, eliminating three post-severance steps.\nThis re-evaluates recorded states; no new Abaqus cycles were run.", "CONCEPTUAL CRACK PATH • NOT A SIMULATION FIELD")
    geometry(fig,cfg,path=True)
    panel_text(fig,.70,.76,"Cycle 52",20,weight="bold",va="top")
    panel_text(fig,.70,.71,f"s = {c52['cumulative_arc_length_mm']:.2f} mm\nRF2 = {c52['terminal_rf2_kN']:.3f} kN\n{c52['rf2_ratio_pct']:.2f}% of peak",16,linespacing=1.5,va="top")
    panel_text(fig,.70,.51,"Cycle 53",20,weight="bold",va="top")
    panel_text(fig,.70,.46,f"Tip reaches x = 65 mm\nRF2 = {c53['terminal_rf2_kN']:.6f} kN\n{c53['rf2_ratio_pct']:.3f}% of peak",16,linespacing=1.5,va="top")
    figures.append(fig)

    fig = page(12, "The tools and their roles", "Python performs state transfer; Abaqus/Standard solves equilibrium and the load advance.")
    lines=["Abaqus/Standard — finite-element solver for each cycle.","UEL (f42_mixed_uel.for) — phase-field response and history at Gauss points.","UEXTERNALDB — commits trial history at the end of an accepted increment.","*STATIC — fixed-load re-equilibration; one-increment target when it converges.","*STATIC, RIKS — arc-length load advance through softening.","*NODE OUTPUT / U — records displacements for transfer.","odbAccess — reads u, d and H from the output database.","Python orchestrator — maps the fields; it does not use *MAP SOLUTION."]
    for i,line in enumerate(lines):panel_text(fig,.075,.82-i*.075,"•  "+line,18,color=NAVY)
    figures.append(fig)

    for i,(fig,path) in enumerate(zip(figures,paths),1):
        fig.savefig(path,dpi=100,facecolor=fig.get_facecolor());plt.close(fig);print('Rendered',i,path,flush=True)
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','10','-i','-','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart']
    with tempfile.NamedTemporaryFile(suffix='.mp4',delete=False,dir=ROOT) as tmp: temp=pathlib.Path(tmp.name)
    try:
        proc=subprocess.Popen(cmd+[str(temp)],stdin=subprocess.PIPE)
        for index,(path,seconds) in enumerate(zip(paths,DURATIONS)):
            raw=Image.open(path).convert('RGB').tobytes()
            for frame in range(seconds*10):proc.stdin.write(before_transfer if index==5 and frame<30 else raw)
        proc.stdin.close()
        if proc.wait():raise RuntimeError('ffmpeg failed')
        temp.replace(VIDEO)
    finally:temp.unlink(missing_ok=True)
    print('Created',VIDEO,'duration',sum(DURATIONS),flush=True)


if __name__ == '__main__': main()
