"""Render the original Case 3 local-run mesh and nodal damage, without Abaqus.

Run from the repo root.  Uses committed state JSONs and the two original local
input decks at D:/mc3_local/full_run; SHA-256 checks bind those read-only decks
to the evidence examined for this visualization. Requires matplotlib, numpy,
Pillow, and ffmpeg. No solver or scheduler is invoked.
"""
import hashlib
import io
import json
import pathlib
import subprocess
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle, Rectangle
from matplotlib.tri import Triangulation
import numpy as np
from PIL import Image

REV = "1d50f6a5940708083f9acb3624bd39509ec1ebc3"
BASE = "models/pandey_kumar_mode1/290_method_c_case3/"
OUTPUT = pathlib.Path("models/pandey_kumar_mode1/290_method_c_case3_rerun")
LOCAL = pathlib.Path("D:/mc3_local/full_run")
HASHES = [None, "5cb9ffdf7a1a16ada3286f28b065eb4466ecbbb1bc3df7ef815694e29a7f4ebc", "0799aa6af94e61de2b11ce2bdb55f4829d5634e72f1fc2ca35f730da4bae782a"]
ELEMENTS = [4671, 6835, 8687]


def git_blob(path):
    return subprocess.check_output(["git", "show", f"{REV}:{path}"])


def read_deck(cycle):
    if cycle == 0:
        return git_blob(BASE + "PK_METHOD_C_CASE3_COARSE_JOB1.inp").decode("utf-8")
    raw = (LOCAL / f"PK_METHOD_C_CASE3_CYCLE{cycle}.inp").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == HASHES[cycle], "Local deck hash changed"
    return raw.decode("utf-8")


def parse_deck(deck):
    nodes, elements, section = {}, [], None
    for line in deck.splitlines():
        line = line.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            upper = line.upper()
            section = "node" if upper.split(",")[0] == "*NODE" else (
                "element" if upper.startswith("*ELEMENT,") and "ELSET=PHASE_" in upper else None)
            continue
        if section:
            v = [x.strip() for x in line.split(",") if x.strip()]
            if section == "node":
                nodes[int(v[0])] = (float(v[1]), float(v[2]))
            else:
                conn = [int(x) for x in v[1:]]
                assert len(conn) in (3, 4)
                elements.append(conn)
    return nodes, elements


def base_figure(title, subtitle):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor="#f6f8fb")
    fig.text(.035, .955, title, fontsize=26, weight="bold", color="#14283c", va="top")
    fig.text(.035, .905, subtitle, fontsize=16, color="#445c72", va="top")
    return fig


def schematic(path):
    fig = base_figure("Method C Case 3 | Geometry and boundary conditions", "PIN_HOLE_PULL • 65 × 120 mm plate")
    ax = fig.add_axes([.20, .09, .60, .74]); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 65, 120, facecolor="white", edgecolor="#25384c", lw=2.4))
    ax.plot([0, 10], [70, 70], color="#bd3845", lw=4)
    for x, y, r in [(36.5, 51, 10), (20, 20, 5), (20, 100, 5)]:
        ax.add_patch(Circle((x, y), r, facecolor="#f6f8fb", edgecolor="#25384c", lw=2))
    ax.annotate("", (20, 116), (20, 103), arrowprops=dict(arrowstyle="-|>", color="#187ba1", lw=3))
    ax.annotate("Upper pin: vertical pull u₂; u₁ = 0", (20, 100), (-45, 120), fontsize=15, arrowprops=dict(arrowstyle="->"))
    ax.annotate("Lower pin fixed: u₁ = u₂ = 0", (20, 20), (-50, 11), fontsize=15, arrowprops=dict(arrowstyle="->"))
    ax.annotate("Notch a₀ = 10 mm\nat y = 70 mm", (9, 70), (-47, 69), fontsize=15, arrowprops=dict(arrowstyle="->"))
    ax.annotate("Central hole: (36.5, 51) mm\nR = 10 mm", (46.5, 51), (76, 50), fontsize=15, arrowprops=dict(arrowstyle="->"))
    ax.annotate("Pin holes: (20, 20) and (20, 100) mm\nR = 5 mm", (25, 100), (76, 99), fontsize=15, arrowprops=dict(arrowstyle="->"))
    ax.set_xlim(-52, 153); ax.set_ylim(-5, 128)
    fig.text(.06, .12, "E = 210 GPa   ν = 0.3\nℓ₀ = 0.285 mm   Gc = 0.00228 kN/mm", fontsize=17, color="#25384c", linespacing=1.6)
    fig.savefig(path, dpi=100, facecolor=fig.get_facecolor()); plt.close(fig)


def render(cycle, records, path):
    nodes, elements = parse_deck(read_deck(cycle))
    suffix = "COARSE_JOB1" if cycle == 0 else f"CYCLE{cycle}"
    state = json.loads(git_blob(BASE + f"local_windows_full_run/PK_METHOD_C_CASE3_{suffix}_state.json"))
    r = records[cycle]; damage = {int(k): float(v) for k, v in state["d_nodal"].items()}
    assert r["cycle_idx"] == cycle and len(elements) == ELEMENTS[cycle]
    assert set(nodes) == set(damage), "Deck and damage node sets differ"
    far_id, far_x, far_y = r["far_side_node"]
    assert np.allclose(nodes[far_id], [far_x, far_y], atol=1e-5)
    tip = np.array([state["tip_x"], state["tip_y"]])
    tip_id = min((nid for nid in nodes if nid != 999999), key=lambda n: np.linalg.norm(np.array(nodes[n])-tip))
    assert np.linalg.norm(np.array(nodes[tip_id])-tip) < 1e-4 and damage[tip_id] >= .95
    assert abs(state["max_damage"] - r["d_max"]) < 1e-5
    node_ids = sorted(n for n in nodes if n != 999999); index = {n: i for i, n in enumerate(node_ids)}
    xy = np.array([nodes[n] for n in node_ids]); d = np.array([damage[n] for n in node_ids])
    triangles, edges = [], set()
    for conn in elements:
        for a, b in zip(conn, conn[1:] + conn[:1]): edges.add(tuple(sorted((a, b))))
        triangles.append([index[n] for n in conn[:3]])
        if len(conn) == 4: triangles.append([index[conn[j]] for j in (0, 2, 3)])
    segments = [[nodes[a], nodes[b]] for a, b in edges]
    title = "Coarse (Cycle 0)" if cycle == 0 else f"Cycle {cycle}"
    fig = base_figure(f"Method C Case 3 | {title}", f"{len(elements):,} physical elements     u₂ = {r['actual_terminal_u2']:.4f} mm     RF2 = {r['terminal_rf2_kN']:.4f} kN     d_max = {r['d_max']:.4f}")
    left = fig.add_axes([.08, .11, .37, .73]); right = fig.add_axes([.53, .11, .37, .73])
    for ax in (left, right):
        ax.set_aspect("equal"); ax.set_xlim(0, 65); ax.set_ylim(0, 120); ax.set_xlabel("x (mm)", fontsize=14); ax.set_ylabel("y (mm)", fontsize=14); ax.tick_params(labelsize=12)
    left.add_collection(LineCollection(segments, colors="#667687", linewidths=.24)); left.set_title("Physical mesh", fontsize=19, weight="bold", pad=10)
    tri = Triangulation(xy[:, 0], xy[:, 1], np.array(triangles))
    contour = right.tripcolor(tri, d, shading="gouraud", cmap="turbo", vmin=0, vmax=1, rasterized=True)
    right.set_facecolor("white"); right.set_title("Spatial damage", fontsize=19, weight="bold", pad=10)
    bar = fig.colorbar(contour, ax=right, fraction=.046, pad=.03); bar.set_label("damage d", fontsize=14); bar.ax.tick_params(labelsize=12)
    fig.savefig(path, dpi=100, facecolor=fig.get_facecolor()); plt.close(fig)
    print(f"Cycle {cycle}: {len(elements)} elements; {len(nodes)} matching nodes; tip node {tip_id}; {r['terminal_rf2_kN']:.4f} kN")


def main():
    records = json.loads(git_blob(BASE + "local_windows_full_run/METHOD_C_CASE3_LOCAL_FULL_RUN_COMPLETED_SUMMARY.json"))
    frames = OUTPUT / "frames"; frames.mkdir(exist_ok=True)
    paths = [frames / "schematic_geometry_bc.png", frames / "frame_coarse.png", frames / "frame_cycle1.png", frames / "frame_cycle2.png"]
    out = OUTPUT / "video_case3_geometry_bc_adaptive_remesh.mp4"
    if any(p.exists() for p in paths + [out]): raise FileExistsError("Output already exists; refusing overwrite")
    schematic(paths[0])
    for cycle in range(3): render(cycle, records, paths[cycle + 1])
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", "10", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False, dir=OUTPUT) as tmp: temp = pathlib.Path(tmp.name)
    try:
        proc = subprocess.Popen(cmd + [str(temp)], stdin=subprocess.PIPE)
        for i, p in enumerate(paths):
            raw = Image.open(p).convert("RGB").tobytes()
            for _ in range(30 if i == 0 else 20): proc.stdin.write(raw)
        proc.stdin.close()
        if proc.wait(): raise RuntimeError("ffmpeg failed")
        temp.replace(out)
    finally:
        temp.unlink(missing_ok=True)
    print("Created", out)


if __name__ == "__main__": main()
