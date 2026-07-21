#!/usr/bin/env python3
"""Generate a diagnostic H0-scale notched quad mesh with configurable notch length.

Notch from x=-0.5 to x=tip_x on y=0 with doubled free faces.
Default diagnostic: tip_x = -0.05 → notch length 0.45 mm on 1 mm plate.
"""
from __future__ import print_function

import argparse
import json
import math
from pathlib import Path

TOL = 1e-10


def build_mesh(notch_length_mm=0.45, h=0.025):
    # plate [-0.5,0.5]^2, notch from left edge length L → tip at -0.5+L
    tip_x = -0.5 + float(notch_length_mm)
    # uniform-ish grid
    n = max(20, int(round(1.0 / h)))
    xs = [-0.5 + i * (1.0 / n) for i in range(n + 1)]
    ys = [-0.5 + j * (1.0 / n) for j in range(n + 1)]
    # force tip station and y=0
    if not any(abs(x - tip_x) < 1e-12 for x in xs):
        xs.append(tip_x)
        xs = sorted(set(round(x, 12) for x in xs))
    if not any(abs(y) < 1e-12 for y in ys):
        ys.append(0.0)
        ys = sorted(set(round(y, 12) for y in ys))
    xs = [0.0 if abs(x) < 1e-12 else x for x in xs]
    ys = [0.0 if abs(y) < 1e-12 else y for y in ys]
    # ensure endpoints
    xs[0], xs[-1] = -0.5, 0.5
    ys[0], ys[-1] = -0.5, 0.5

    # nodes with notch split: y=0 and -0.5 <= x < tip_x → lower/upper
    nodes = {}  # key -> id
    coords = {}
    nid = 1

    def add(x, y, side="shared"):
        nonlocal nid
        key = (round(x, 12), round(y, 12), side)
        if key not in nodes:
            nodes[key] = nid
            coords[nid] = (x, y)
            nid += 1
        return nodes[key]

    def node_at(i, j, side="shared"):
        x, y = xs[i], ys[j]
        if abs(y) < TOL and -0.5 - TOL <= x < tip_x - TOL:
            return add(x, y, side)
        return add(x, y, "shared")

    # create all nodes
    zero_j = min(range(len(ys)), key=lambda j: abs(ys[j]))
    for j in range(len(ys)):
        for i in range(len(xs)):
            x, y = xs[i], ys[j]
            if abs(y) < TOL and -0.5 - TOL <= x < tip_x - TOL:
                node_at(i, j, "lower")
                node_at(i, j, "upper")
            else:
                node_at(i, j, "shared")

    conn = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            if j == zero_j:
                n1 = node_at(i, j, "upper")
                n2 = node_at(i + 1, j, "upper")
            else:
                n1 = node_at(i, j)
                n2 = node_at(i + 1, j)
            if j + 1 == zero_j:
                n3 = node_at(i + 1, j + 1, "lower")
                n4 = node_at(i, j + 1, "lower")
            else:
                n3 = node_at(i + 1, j + 1)
                n4 = node_at(i, j + 1)
            conn.append((n1, n2, n3, n4))

    # nsets
    bottom = [i for i, (x, y) in coords.items() if abs(y + 0.5) < 1e-8]
    top = [i for i, (x, y) in coords.items() if abs(y - 0.5) < 1e-8]
    # notch faces
    lower_face = []
    upper_face = []
    for key, i in nodes.items():
        x, y, side = key
        if abs(y) < TOL and -0.5 - TOL <= x < tip_x - TOL:
            if side == "lower":
                lower_face.append(i)
            elif side == "upper":
                upper_face.append(i)

    return {
        "coords": coords,
        "conn": conn,
        "bottom": sorted(bottom),
        "top": sorted(top),
        "bottoml": [min(bottom, key=lambda i: coords[i][0])] if bottom else [],
        "topl": [min(top, key=lambda i: coords[i][0])] if top else [],
        "notch_lower": sorted(lower_face),
        "notch_upper": sorted(upper_face),
        "tip_x": tip_x,
        "notch_length_mm": notch_length_mm,
        "n_elements": len(conn),
        "n_nodes": len(coords),
        "has_y0": any(abs(y) < 1e-12 for _, y in coords.values()),
        "notch_split": len(lower_face) > 0 and len(upper_face) > 0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notch-length-mm", type=float, default=0.45)
    ap.add_argument("--h", type=float, default=0.025)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    mesh = build_mesh(args.notch_length_mm, args.h)
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "refined_mesh_nodes.csv").open("w") as f:
        f.write("node_id,x,y\n")
        for i in sorted(mesh["coords"]):
            x, y = mesh["coords"][i]
            f.write("%s,%s,%s\n" % (i, x, y))
    with (args.out / "refined_mesh_elements.csv").open("w") as f:
        f.write("element_id,n1,n2,n3,n4\n")
        for ei, c in enumerate(mesh["conn"], 1):
            f.write("%s,%s,%s,%s,%s\n" % (ei, c[0], c[1], c[2], c[3]))
    meta = {k: mesh[k] for k in mesh if k not in ("coords", "conn")}
    (args.out / "mesh_meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print(json.dumps(meta, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
