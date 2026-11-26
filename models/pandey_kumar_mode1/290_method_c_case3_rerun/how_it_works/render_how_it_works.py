"""Generate a silent, schematic Method C explainer; no solver data are rendered.

Run from the repository root. Requires matplotlib, Pillow and ffmpeg. Geometry
and reported Case 3 milestones are read from committed JSON; the eight-cell mesh
is an illustrative toy and is not a reconstruction of a simulation result.
"""
import io
import json
import pathlib
import subprocess
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
from PIL import Image, ImageDraw, ImageFont
import numpy as np

REV = "860f462a95c27a3c936fb282916206b7dfcfc4a3"
ROOT = pathlib.Path("models/pandey_kumar_mode1/290_method_c_case3_rerun")
FRAMES = ROOT / "how_it_works/frames"
VIDEO = ROOT / "video_method_c_how_it_works.mp4"
DURATIONS = [3, 5, 7, 5, 7, 8, 9, 9, 6, 8, 6, 7, 7]
OLD_REV = "ec16cbf84e5daa33245f8501f9c9bab812274567"
NAVY, BLUE, TEAL, PAPER = "#152a40", "#2079aa", "#087f75", "#f5f8fb"
CMAP = matplotlib.colormaps["turbo"]


def committed(path):
    return json.loads(subprocess.check_output(["git", "show", f"{REV}:{path}"]))


def page(number, title, caption, tag=None, caption_size=19):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=PAPER)
    fig.patches.append(Rectangle((0, .895), 1, .105, transform=fig.transFigure, facecolor=NAVY, zorder=-1))
    fig.text(.04, .94, title, fontsize=27, color="white", weight="bold", va="center")
    fig.text(.96, .94, f"{number:02d} / 13", fontsize=16, color="#c5d4e1", va="center", ha="right")
    if tag:
        fig.text(.04, .86, tag, fontsize=15, color="#28729c", weight="bold")
    fig.patches.append(Rectangle((.035, .035), .93, .15, transform=fig.transFigure, facecolor="#e5eef5", edgecolor="none", zorder=-1))
    fig.text(.055, .11, caption, fontsize=caption_size, color=NAVY, va="center", linespacing=1.4)
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


def interpolation_scene():
    caption = ("Each new node takes the value interpolated from the old mesh AT ITS POSITION (bilinear interpolation in Case 3).\n"
               "Corners keep their value; new nodes on edges and in the centre take averages. Gauss-point history (H) is\n"
               "interpolated the same way, from the old Gauss points to the new ones. Displacement (u) is nodal and transfers like damage (d).")
    fig=page(6,"One element becomes four — what happens to the values?",caption,
             "SIMPLIFIED CONCEPTUAL EXAMPLE • VALUES ARE NODAL")
    nodes={(0.,1.):.90,(1.,1.):.80,(0.,0.):.70,(1.,0.):.60,
           (.5,1.):.85,(0.,.5):.80,(1.,.5):.70,(.5,0.):.65,(.5,.5):.75}
    assert abs(nodes[(.5,1.)]-(.90+.80)/2)<1e-12
    assert abs(nodes[(0.,.5)]-(.90+.70)/2)<1e-12
    assert abs(nodes[(1.,.5)]-(.80+.60)/2)<1e-12
    assert abs(nodes[(.5,0.)]-(.70+.60)/2)<1e-12
    assert abs(nodes[(.5,.5)]-(.90+.80+.70+.60)/4)<1e-12
    # Rows are bottom-to-top; imshow interpolates the same bilinear field.
    z=np.array([[.70,.60],[.90,.80]])
    for axis,subdivide in [([.08,.36,.34,.40],False),([.57,.36,.34,.40],True)]:
        ax=fig.add_axes(axis);ax.set_xlim(-.16,1.16);ax.set_ylim(-.15,1.15);ax.set_aspect('equal');ax.axis('off')
        ax.imshow(z,extent=(0,1,0,1),origin='lower',interpolation='bilinear',cmap=CMAP,vmin=0,vmax=1)
        ax.add_patch(Rectangle((0,0),1,1,fill=False,edgecolor=NAVY,lw=2))
        if subdivide:
            ax.plot([.5,.5],[0,1],color='white',lw=2);ax.plot([0,1],[.5,.5],color='white',lw=2)
        for (x,y),value in nodes.items():
            if not subdivide and x not in (0.,1.):continue
            if not subdivide and y not in (0.,1.):continue
            ax.plot(x,y,'o',color=NAVY,markeredgecolor='white',markersize=8,zorder=4)
            ax.annotate(f'{value:.2f}',(x,y),xytext=(7,7),textcoords='offset points',fontsize=14,weight='bold',color=NAVY,
                        bbox=dict(boxstyle='round,pad=.15',facecolor='white',edgecolor='none',alpha=.9),zorder=5)
    panel_text(fig,.105,.80,'One coarse element (donor)',20,weight='bold')
    panel_text(fig,.58,.80,'Same element, subdivided into four',20,weight='bold')
    panel_text(fig,.08,.325,'Values live at the NODES — a gradient, not one number.',15,color='#435f73')
    panel_text(fig,.52,.325,'The four new elements do NOT all get the same value.',15,color='#435f73',weight='bold')
    panel_text(fig,.52,.295,'Their average damage is 0.83 / 0.78 / 0.73 / 0.68',15,color='#435f73')
    panel_text(fig,.52,.268,'(top-left / top-right / bottom-left / bottom-right) — they follow the gradient.',13.5,color='#435f73')
    cbar(fig,[.10,.29,.32,.017])
    panel_text(fig,.06,.205,"Later campaigns use cKDTree nearest-neighbour instead of bilinear — same idea, each new node takes the nearest old node's value.",13.5,color='#536f82')
    # Check the requested values, with conventional decimal half-up rounding.
    from decimal import Decimal, ROUND_HALF_UP
    groups=[['.90','.85','.80','.75'],['.85','.80','.75','.70'],['.80','.75','.70','.65'],['.75','.70','.65','.60']]
    means=[sum(Decimal(x) for x in group)/4 for group in groups]
    assert means==list(map(Decimal,['.825','.775','.725','.675']))
    assert [x.quantize(Decimal('.01'),rounding=ROUND_HALF_UP) for x in means]==list(map(Decimal,['.83','.78','.73','.68']))
    return fig


def main():
    # Unchanged scenes are copied byte-for-byte from the previous committed
    # version, with their file names shifted after the new sixth scene.
    dest=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT
    frames=dest/'how_it_works/frames';video=dest/'video_method_c_how_it_works.mp4';frames.mkdir(parents=True,exist_ok=True)
    paths=[frames/f'scene_{i:02}.png' for i in range(1,14)]
    if video.exists() or any(p.exists() for p in paths):raise FileExistsError('Output exists; use an empty staging directory')
    oldprefix='models/pandey_kumar_mode1/290_method_c_case3_rerun/how_it_works/frames/'
    for new in list(range(1,5))+list(range(8,14)):
        old=new if new<=4 else new-1
        paths[new-1].write_bytes(subprocess.check_output(['git','show',f'{OLD_REV}:{oldprefix}scene_{old:02}.png']))
    caption5=("The mesh generator rebuilds the mesh from scratch. Inside the corridor it places small elements of fixed size h_ref;\n"
              "outside, coarse background elements (h_bg). The count grows because the corridor — which was coarse — is now packed\n"
              "with small elements. The elements themselves never get smaller. (In this toy demo the refinement looks like splitting;\n"
              "the real framework regenerates the whole mesh each cycle.)")
    fig=page(5,'Cycle 1 | Remesh',caption5,'SIMPLIFIED CONCEPTUAL MESH')
    toy_main(fig,refined=1);fig.savefig(paths[4],dpi=100,facecolor=fig.get_facecolor());plt.close(fig)
    fig=interpolation_scene();fig.savefig(paths[5],dpi=100,facecolor=fig.get_facecolor());plt.close(fig)
    caption7=("Python interpolates nodal displacement (u) and damage (d), and Gauss-point history (H), from the old mesh to\n"
              "the new mesh — node by node, as in the previous scene. The transfer is not Abaqus *MAP SOLUTION.")
    fig=page(7,'Transfer damage and history',caption7,'SIMPLIFIED CONCEPTUAL MESH • INHERITANCE IS ILLUSTRATIVE')
    left=axblank(fig,[.045,.32,.39,.38]);toy(left);right=axblank(fig,[.565,.32,.39,.38]);toy(right,refined=1,pale=True)
    panel_text(fig,.11,.75,'Old mesh | 8 elements',18,weight='bold');panel_text(fig,.63,.75,'New mesh | 14 elements',18,weight='bold')
    fig.add_artist(FancyArrowPatch((.46,.51),(.55,.51),transform=fig.transFigure,arrowstyle='-|>',mutation_scale=28,lw=3,color=BLUE))
    panel_text(fig,.465,.58,'u, d, H',16,color=BLUE,weight='bold')
    panel_text(fig,.57,.285,'New nodes take interpolated values — see previous scene.',14,color='#435f73')
    cbar(fig,[.12,.235,.32,.018])
    before=io.BytesIO();fig.savefig(before,format='png',dpi=100,facecolor=fig.get_facecolor());before.seek(0);before_transfer=Image.open(before).convert('RGB').copy()
    toy(right,refined=1);fig.savefig(paths[6],dpi=100,facecolor=fig.get_facecolor());plt.close(fig)
    # Preserve the unchanged PNGs; correct their embedded old scene numbers
    # in the video only, without altering the committed artwork.
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',23)
    def numbering(im,i):
        im=im.copy();d=ImageDraw.Draw(im);d.rectangle((1680,38,1890,90),fill=NAVY);d.text((1843,65),f'{i:02} / 13',font=font,fill='#c5d4e1',anchor='rm');return im.tobytes()
    before_raw=numbering(before_transfer,7)
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','10','-i','-','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart']
    with tempfile.NamedTemporaryFile(suffix='.mp4',delete=False,dir=dest) as tmp:temp=pathlib.Path(tmp.name)
    try:
        proc=subprocess.Popen(cmd+[str(temp)],stdin=subprocess.PIPE)
        for index,(path,seconds) in enumerate(zip(paths,DURATIONS),1):
            raw=numbering(Image.open(path).convert('RGB'),index)
            for frame in range(seconds*10):proc.stdin.write(before_raw if index==7 and frame<30 else raw)
        proc.stdin.close()
        if proc.wait():raise RuntimeError('ffmpeg failed')
        temp.replace(video)
    finally:temp.unlink(missing_ok=True)
    print('Created',video,'duration',sum(DURATIONS),'seconds',flush=True)


if __name__=='__main__':main()
