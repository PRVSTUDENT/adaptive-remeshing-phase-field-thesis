#!/usr/bin/env python3
"""Build refined physical mesh from MISESERI CSV.

Self-contained (no PyYAML). Compatible with older and newer CPython.
No Abaqus/Standard solve.
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path

TOL = 1.0e-10
LC = 0.015


class AxisSpacing(object):
    def __init__(self, coordinates, spacings):
        self.coordinates = coordinates
        self.spacings = spacings


def _round_coord(value):
    rounded = round(value, 10)
    return 0.0 if abs(rounded) < 5.0e-9 else rounded


def _graded_sizes_to_refined(length, local_h, global_h, ratio):
    transition = []
    size = local_h
    while size < global_h:
        transition.append(size)
        size *= ratio
    if not transition or transition[-1] < global_h:
        transition.append(global_h)
    transition_sum = sum(transition)
    if transition_sum >= length:
        n = max(1, int(round(length / local_h)))
        return [length / float(n)] * n
    remaining = length - transition_sum
    coarse_count = max(1, int((remaining + global_h - TOL) // global_h))
    coarse = [remaining / float(coarse_count)] * coarse_count
    return coarse + list(reversed(transition))


def _axis_with_refined_region(start, refined_min, refined_max, end, local_h, global_h, ratio):
    left_sizes = _graded_sizes_to_refined(refined_min - start, local_h, global_h, ratio)
    refined_count = int(round((refined_max - refined_min) / local_h))
    refined_sizes = [local_h] * refined_count
    right_sizes = list(reversed(_graded_sizes_to_refined(end - refined_max, local_h, global_h, ratio)))
    sizes = left_sizes + refined_sizes + right_sizes
    coords = [start]
    for size in sizes:
        coords.append(_round_coord(coords[-1] + size))
    coords[-1] = _round_coord(end)
    return AxisSpacing(coords, [round(coords[i + 1] - coords[i], 10) for i in range(len(coords) - 1)])


def _axis_refined_to_end(start, refined_min, end, local_h, global_h, ratio):
    left_sizes = _graded_sizes_to_refined(refined_min - start, local_h, global_h, ratio)
    refined_count = int(round((end - refined_min) / local_h))
    sizes = left_sizes + [local_h] * refined_count
    coords = [start]
    for size in sizes:
        coords.append(_round_coord(coords[-1] + size))
    coords[-1] = _round_coord(end)
    return AxisSpacing(coords, [round(coords[i + 1] - coords[i], 10) for i in range(len(coords) - 1)])


def make_axis_spacings(local_h, refined_zone, global_h=0.025, ratio=1.5):
    x_axis = _axis_refined_to_end(-0.5, float(refined_zone["x_min"]), 0.5, local_h, global_h, ratio)
    y_axis = _axis_with_refined_region(
        -0.5, float(refined_zone["y_min"]), float(refined_zone["y_max"]), 0.5, local_h, global_h, ratio
    )
    return x_axis, y_axis


class MeshBuilder(object):
    def __init__(self, x_axis, y_axis):
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.nodes = {}
        self.node_coords = {}
        self.next_node = 1

    def _node_key(self, i, j, side="shared"):
        x = self.x_axis.coordinates[i]
        y = self.y_axis.coordinates[j]
        if abs(y) < TOL and -0.5 <= x < 0.0:
            return (i, j, side)
        return (i, j, "shared")

    def node(self, i, j, side="shared"):
        key = self._node_key(i, j, side)
        if key not in self.nodes:
            self.nodes[key] = self.next_node
            self.node_coords[self.next_node] = (self.x_axis.coordinates[i], self.y_axis.coordinates[j])
            self.next_node += 1
        return self.nodes[key]

    def build_nodes(self):
        for j in range(len(self.y_axis.coordinates)):
            for i in range(len(self.x_axis.coordinates)):
                y = self.y_axis.coordinates[j]
                x = self.x_axis.coordinates[i]
                if abs(y) < TOL and -0.5 <= x < 0.0:
                    self.node(i, j, "lower")
                    self.node(i, j, "upper")
                else:
                    self.node(i, j)

    def element_connectivity(self):
        zero_j = min(range(len(self.y_axis.coordinates)), key=lambda j: abs(self.y_axis.coordinates[j]))
        conn = []
        for j in range(len(self.y_axis.coordinates) - 1):
            for i in range(len(self.x_axis.coordinates) - 1):
                if j == zero_j:
                    n1 = self.node(i, j, "upper")
                    n2 = self.node(i + 1, j, "upper")
                else:
                    n1 = self.node(i, j)
                    n2 = self.node(i + 1, j)
                if j + 1 == zero_j:
                    n3 = self.node(i + 1, j + 1, "lower")
                    n4 = self.node(i, j + 1, "lower")
                else:
                    n3 = self.node(i + 1, j + 1)
                    n4 = self.node(i, j + 1)
                conn.append((n1, n2, n3, n4))
        return conn


def load_rows(csv_path):
    with csv_path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def apply_marks(rows, rule):
    error_target = float(rule["errorTarget"])
    refinement_factor = float(rule["refinementFactor"])
    min_h = float(rule["minElementSize_mm"])
    max_h = float(rule["maxElementSize_mm"])
    if rule.get("coarsening", False):
        raise RuntimeError("coarsening must be disabled")
    n_marked = 0
    for row in rows:
        m = float(row["MISESERI"])
        h = float(row["h_mean"])
        if m > error_target:
            row["marked_for_refinement"] = "1"
            row["target_h"] = str(max(min_h, min(max_h, h / refinement_factor)))
            n_marked += 1
        else:
            row["marked_for_refinement"] = "0"
            row["target_h"] = str(h)
    return {
        "n_marked": n_marked,
        "fraction_marked": (n_marked / float(len(rows))) if rows else 0.0,
        "errorTarget": error_target,
        "refinementFactor": refinement_factor,
        "minElementSize_mm": min_h,
        "maxElementSize_mm": max_h,
    }


def refined_zone_from_rows(rows, min_h):
    marked = []
    for r in rows:
        if r.get("marked_for_refinement") in ("1", 1, True, "True"):
            marked.append((float(r["xc"]), float(r["yc"])))
    if not marked:
        return {
            "x_min": -0.02,
            "x_max": 0.5,
            "y_min": -0.005,
            "y_max": 0.005,
            "source": "fallback_default_corridor_no_marked_elements",
        }
    xs = [p[0] for p in marked]
    ys = [p[1] for p in marked]
    pad = max(min_h * 4.0, 0.01)
    return {
        "x_min": max(-0.5, min(xs) - pad),
        "x_max": min(0.5, max(xs) + pad),
        "y_min": max(-0.5, min(ys) - pad),
        "y_max": min(0.5, max(ys) + pad),
        "source": "miseseri_marked_bounding_box_padded",
        "n_marked_points": len(marked),
    }


def build_mesh(local_h, refined_zone, global_h):
    x_axis, y_axis = make_axis_spacings(local_h, refined_zone, global_h=global_h, ratio=1.5)
    mesh = MeshBuilder(x_axis, y_axis)
    mesh.build_nodes()
    return mesh.node_coords, mesh.element_connectivity()


def corridor_stats(nodes, conn, zone):
    edges = []
    for n1, n2, n3, n4 in conn:
        pts = [nodes[n1], nodes[n2], nodes[n3], nodes[n4]]
        xc = sum(p[0] for p in pts) / 4.0
        yc = sum(p[1] for p in pts) / 4.0
        if zone["x_min"] <= xc <= zone["x_max"] and zone["y_min"] <= yc <= zone["y_max"]:
            for i in range(4):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % 4]
                edges.append(math.hypot(x1 - x0, y1 - y0))
    if not edges:
        return None
    edges.sort()
    mid = len(edges) // 2
    if len(edges) % 2:
        med = edges[mid]
    else:
        med = 0.5 * (edges[mid - 1] + edges[mid])
    return {"min": edges[0], "median": med, "max": edges[-1], "count": len(edges)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    rule = config["rule"]
    rows = load_rows(args.csv)
    # ensure h_mean
    for r in rows:
        if "h_mean" not in r or r["h_mean"] in ("", None):
            try:
                r["h_mean"] = math.sqrt(float(r["EVOL"])) if float(r["EVOL"]) > 0 else 0.005
            except Exception:
                r["h_mean"] = 0.005
        if "xc" not in r:
            r["xc"] = r.get("centroid_x", 0)
            r["yc"] = r.get("centroid_y", 0)
    sizing = apply_marks(rows, rule)
    min_h = float(rule["minElementSize_mm"])
    max_h = float(rule["maxElementSize_mm"])
    zone = refined_zone_from_rows(rows, min_h)
    nodes, conn = build_mesh(min_h, zone, max_h)
    args.out.mkdir(parents=True, exist_ok=True)

    nodes_csv = args.out / "refined_mesh_nodes.csv"
    elems_csv = args.out / "refined_mesh_elements.csv"
    physical_inp = args.out / "refined_physical.inp"
    with nodes_csv.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("node_id,x,y\n")
        for nid in sorted(nodes):
            stream.write("%s,%s,%s\n" % (nid, nodes[nid][0], nodes[nid][1]))
    with elems_csv.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("element_id,n1,n2,n3,n4\n")
        for i, c in enumerate(conn, start=1):
            stream.write("%s,%s,%s,%s,%s\n" % (i, c[0], c[1], c[2], c[3]))
    lines = ["*Heading", "** Refined physical mesh", "*Node"]
    for nid in sorted(nodes):
        lines.append("%s, %.10g, %.10g" % (nid, nodes[nid][0], nodes[nid][1]))
    lines.append("*Element, type=CPS4, elset=physical")
    for i, c in enumerate(conn, start=1):
        lines.append("%s, %s, %s, %s, %s" % (i, c[0], c[1], c[2], c[3]))
    physical_inp.write_text("\n".join(lines) + "\n", encoding="utf-8")

    corridor = corridor_stats(nodes, conn, zone)
    target_ok = bool(corridor and abs(corridor["median"] - min_h) <= 0.25 * min_h)
    manifest = {
        "status": "pass" if target_ok else "fail_mesh_size_target",
        "sizing": sizing,
        "refined_zone": zone,
        "n_nodes": len(nodes),
        "n_elements": len(conn),
        "corridor_h": corridor,
        "corridor_h_near_minElementSize": target_ok,
    }
    (args.out / "remeshing_rule_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if target_ok else 14


if __name__ == "__main__":
    raise SystemExit(main())
