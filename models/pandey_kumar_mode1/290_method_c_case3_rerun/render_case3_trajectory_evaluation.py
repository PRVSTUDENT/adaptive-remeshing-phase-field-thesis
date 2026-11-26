"""Create a data-only Case 3 review video from committed summaries.

This does not invoke Abaqus or depict reconstructed adaptive meshes.  Requires
matplotlib, Pillow and ffmpeg.  Run from the repository root.
"""
import io
import json
import pathlib
import subprocess
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from PIL import Image

BASE = "models/pandey_kumar_mode1/290_method_c_case3"
DEST = pathlib.Path(BASE + "_rerun/video_case3_trajectory_evaluation.mp4")
REV = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def committed(path):
    return json.loads(subprocess.check_output(["git", "show", f"{REV}:{path}"]))


def canvas(title, subtitle):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor="#f6f8fb")
    fig.text(.045, .94, title, fontsize=28, weight="bold", color="#14283c")
    fig.text(.045, .895, subtitle, fontsize=15, color="#445c72")
    return fig


def image_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB").tobytes()


def main():
    records = committed(BASE + "/local_windows_full_run/METHOD_C_CASE3_LOCAL_FULL_RUN_COMPLETED_SUMMARY.json")
    evaluation = committed(BASE + "_rerun/METHOD_C_CASE3_RERUN_SUMMARY.json")
    assert len(records) == 57 and [r["cycle_idx"] for r in records] == list(range(57))
    assert evaluation["evaluation_mode"] == "RE_EVALUATION_OF_ORIGINAL_TRAJECTORY_UNDER_FIXED_STOPPING_LOGIC"
    original, fixed = evaluation["original_run"], evaluation["improved_framework_rerun"]
    assert (original["adaptive_remesh_steps"], fixed["adaptive_remesh_steps"], fixed["terminal_cycle"]) == (56, 53, 53)

    fig = canvas("Method C Case 3 | Geometry and loading", "65 × 120 mm notched plate with three holes • PIN_HOLE_PULL")
    ax = fig.add_axes([.29, .09, .35, .73]); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 65, 120, facecolor="white", edgecolor="#25384c", lw=2.4))
    ax.plot([0, 10], [70, 70], color="#bc3944", lw=4)
    for x, y, radius in [(36.5, 51, 10), (20, 20, 5), (20, 100, 5)]:
        ax.add_patch(Circle((x, y), radius, facecolor="#f6f8fb", edgecolor="#25384c", lw=2))
    ax.annotate("", (20, 116), (20, 103), arrowprops=dict(arrowstyle="-|>", color="#187ba1", lw=3))
    ax.annotate("Lower pin fixed: uₓ = uᵧ = 0", (20, 20), (-31, 8), fontsize=14, arrowprops=dict(arrowstyle="->"))
    ax.annotate("Upper pin: uᵧ pull; uₓ = 0", (20, 100), (-45, 120), fontsize=14, arrowprops=dict(arrowstyle="->"))
    ax.annotate("Notch a₀ = 10 mm\nat y = 70 mm", (8, 70), (-42, 69), fontsize=14, arrowprops=dict(arrowstyle="->"))
    ax.annotate("Central hole R = 10 mm", (46.5, 51), (73, 55), fontsize=14, arrowprops=dict(arrowstyle="->"))
    ax.annotate("Pin holes R = 5 mm", (25, 100), (73, 96), fontsize=14, arrowprops=dict(arrowstyle="->"))
    ax.set_xlim(-45, 128); ax.set_ylim(-3, 125)
    fig.text(.12, .15, "Plate: 65 × 120 mm\nE = 210 GPa   ν = 0.3\nℓ₀ = 0.285 mm   Gc = 0.00228 kN/mm", fontsize=17, color="#25384c", linespacing=1.7)
    first = image_bytes(fig)

    fig = canvas("Original trajectory | First three states", "Committed local-run summary • terminal values; no reconstructed mesh or damage field")
    ax = fig.add_axes([.10, .19, .53, .62]); x = [r["cycle_idx"] for r in records[:3]]
    rf = [r["terminal_rf2_kN"] for r in records[:3]]
    ax.plot(x, rf, "o-", lw=3, markersize=10, color="#187ba1"); ax.set_xticks(x, ["Coarse C0", "Cycle 1", "Cycle 2"])
    ax.set_ylabel("Terminal RF2 (kN)", fontsize=17); ax.set_ylim(0, 5); ax.grid(axis="y", alpha=.25); ax.tick_params(labelsize=14)
    for i, r in enumerate(records[:3]):
        ax.annotate(f"{rf[i]:.4f} kN\nu₂ = {r['actual_terminal_u2']:.4f} mm\ndₘₐₓ = {r['d_max']:.4f}", (i, rf[i]), xytext=(0, 14), textcoords="offset points", ha="center", fontsize=13)
    fig.text(.69, .75, "First two adaptive steps", fontsize=20, weight="bold", color="#14283c", va="top")
    fig.text(.69, .68, "Cycle 1 hold jump: −11.31%\nCycle 2 terminated on cutback\n\nMesh/damage overlays omitted:\nmatching source meshes not verified.", fontsize=17, color="#445c72", linespacing=1.6, va="top")
    second = image_bytes(fig)

    fig = canvas("Stopping-logic re-evaluation", "Same original trajectory re-evaluated • no new Abaqus cycles executed")
    ax = fig.add_axes([.19, .25, .45, .53]); bars = ax.barh([1, 0], [original["adaptive_remesh_steps"], fixed["adaptive_remesh_steps"]], color=["#7e91a2", "#187ba1"], height=.48)
    ax.set_yticks([1, 0], ["Original", "Fixed stopping logic"]); ax.set_xlim(0, 64); ax.set_xlabel("Adaptive remesh steps", fontsize=17); ax.tick_params(labelsize=15); ax.grid(axis="x", alpha=.2); ax.set_axisbelow(True)
    for b in bars: ax.text(b.get_width()+.7, b.get_y()+b.get_height()/2, f"{int(b.get_width())}", va="center", fontsize=19, weight="bold")
    fig.text(.68, .73, "3 fewer steps (−5.36%)", fontsize=22, color="#126988", weight="bold")
    fig.text(.68, .58, f"Cycle 53 stopping state\nRF2 = {fixed['terminal_rf2_kN']:.6f} kN\n{fixed['terminal_rf2_ratio_pct']:.3f}% of peak\nTip x = {fixed['terminal_tip_x_mm']:.1f} mm", fontsize=18, color="#25384c", linespacing=1.65)
    fig.text(.10, .12, "The revised stopping rule removes three post-severance steps from the recorded trajectory.", fontsize=16, color="#445c72")
    third = image_bytes(fig)

    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", "10", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(DEST)]
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False, dir=DEST.parent) as tmp:
        temporary = pathlib.Path(tmp.name)
    cmd[-1] = str(temporary)
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for img in (first, second, third):
            for _ in range(30):
                proc.stdin.write(img)
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("ffmpeg failed")
        if DEST.exists():
            raise FileExistsError(DEST)
        temporary.replace(DEST)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Created {DEST} from committed revision {REV}")


if __name__ == "__main__":
    main()
