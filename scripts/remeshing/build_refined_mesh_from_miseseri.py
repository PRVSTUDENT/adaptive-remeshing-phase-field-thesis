#!/usr/bin/env python3
"""Build refined physical mesh from MISESERI CSV (local offline remesh).

Self-contained (no PyYAML). Compatible with older and newer CPython.
No Abaqus/Standard solve.

Marking rule (documented):
  errorTarget is a *relative* indicator threshold (e.g. 0.05 = 5% of max
  MISESERI on the mesh), matching the frozen proposal wording "5% relative
  von Mises recovery-error indicator". It is **not** an absolute raw-MISESERI
  cutoff (raw MISESERI on the continuum pre-analysis reaches ~1e3).

  mark if  MISESERI / max(MISESERI)  >  errorTarget

Then retain only the notch-dominant connected component of marked elements
(seeded at the highest-MISESERI marked element near the notch tip).

Axis grading uses a *bounded* refined window on both X and Y so minElementSize
is not applied from the notch to the far right boundary of the plate.
"""

from __future__ import print_function

import argparse
import csv
import json
import math
import sys
from collections import defaultdict, deque
from pathlib import Path

TOL = 1.0e-10
LC = 0.015
H0_NPHYS = 3930
H1_NPHYS = 12064
H2_NPHYS = 33852
# Controlled failure if adaptive mesh is still unreasonably global
MAX_ALLOWED_ELEMENTS = H2_NPHYS  # must stay below H2-PUB for this Stage C path
MAX_MARK_FRACTION = 0.50  # proposal falsification: >50% is wrong


class AxisSpacing(object):
    def __init__(self, coordinates, spacings):
        self.coordinates = coordinates
        self.spacings = spacings


def _round_coord(value):
    rounded = round(value, 10)
    return 0.0 if abs(rounded) < 5.0e-9 else rounded


def _graded_sizes_to_refined(length, local_h, global_h, ratio):
    if length <= TOL:
        return []
    transition = []
    size = local_h
    while size < global_h - TOL:
        transition.append(size)
        size *= ratio
    if not transition or transition[-1] < global_h - TOL:
        transition.append(global_h)
    transition_sum = sum(transition)
    if transition_sum >= length - TOL:
        n = max(1, int(round(length / max(local_h, TOL))))
        return [length / float(n)] * n
    remaining = length - transition_sum
    coarse_count = max(1, int((remaining + global_h - TOL) // global_h))
    coarse = [remaining / float(coarse_count)] * coarse_count
    return coarse + list(reversed(transition))


def _axis_with_refined_region(start, refined_min, refined_max, end, local_h, global_h, ratio):
    """Coarse | graded | fine | graded | coarse — min size only inside [rmin,rmax]."""
    refined_min = max(start, min(end, refined_min))
    refined_max = max(start, min(end, refined_max))
    if refined_max < refined_min:
        refined_min, refined_max = refined_max, refined_min
    left_sizes = _graded_sizes_to_refined(refined_min - start, local_h, global_h, ratio)
    refined_len = refined_max - refined_min
    refined_count = max(1, int(round(refined_len / local_h))) if refined_len > TOL else 0
    refined_sizes = [local_h] * refined_count
    # adjust last refined spacing to land exactly on refined_max
    if refined_sizes:
        # rebuild refined block to exact length
        refined_sizes = [refined_len / float(refined_count)] * refined_count
    right_sizes = list(
        reversed(_graded_sizes_to_refined(end - refined_max, local_h, global_h, ratio))
    )
    sizes = left_sizes + refined_sizes + right_sizes
    if not sizes:
        sizes = [end - start]
    coords = [start]
    for size in sizes:
        coords.append(_round_coord(coords[-1] + size))
    coords[-1] = _round_coord(end)
    return AxisSpacing(
        coords, [round(coords[i + 1] - coords[i], 10) for i in range(len(coords) - 1)]
    )


def make_axis_spacings(local_h, refined_zone, global_h=0.025, ratio=1.5):
    """Bounded refined window on both axes (local, not global min-size)."""
    x_axis = _axis_with_refined_region(
        -0.5,
        float(refined_zone["x_min"]),
        float(refined_zone["x_max"]),
        0.5,
        local_h,
        global_h,
        ratio,
    )
    y_axis = _axis_with_refined_region(
        -0.5,
        float(refined_zone["y_min"]),
        float(refined_zone["y_max"]),
        0.5,
        local_h,
        global_h,
        ratio,
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
            self.node_coords[self.next_node] = (
                self.x_axis.coordinates[i],
                self.y_axis.coordinates[j],
            )
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
        zero_j = min(
            range(len(self.y_axis.coordinates)),
            key=lambda j: abs(self.y_axis.coordinates[j]),
        )
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
    # Py2/3 safe: avoid newline= on older interpreters that open CSV via Path
    path = str(csv_path)
    try:
        stream = open(path, "r", newline="", encoding="utf-8")
    except TypeError:
        stream = open(path, "r")
    try:
        return list(csv.DictReader(stream))
    finally:
        stream.close()


def apply_marks(rows, rule):
    """Relative MISESERI marking: mark if M/Mmax > errorTarget."""
    error_target = float(rule["errorTarget"])
    refinement_factor = float(rule["refinementFactor"])
    min_h = float(rule["minElementSize_mm"])
    max_h = float(rule["maxElementSize_mm"])
    if rule.get("coarsening", False):
        raise RuntimeError("coarsening must be disabled")

    mvals = []
    for row in rows:
        mvals.append(float(row["MISESERI"]))
    mmax = max(mvals) if mvals else 0.0
    if mmax <= 0.0:
        raise RuntimeError("MISESERI field is non-positive; cannot normalize")

    n_marked = 0
    for row, m in zip(rows, mvals):
        h = float(row["h_mean"])
        m_norm = m / mmax
        row["normalized_MISESERI"] = "%.12g" % m_norm
        # Correct relative rule (proposal: errorTarget is 5% relative)
        if m_norm > error_target:
            row["marked_for_refinement"] = "1"
            row["target_h"] = str(max(min_h, min(max_h, h / refinement_factor)))
            n_marked += 1
        else:
            row["marked_for_refinement"] = "0"
            row["target_h"] = str(h)
            # do not enlarge (coarsening disabled): target_h = current h
    frac = (n_marked / float(len(rows))) if rows else 0.0
    return {
        "marking_rule": "relative_MISESERI_over_max_gt_errorTarget",
        "marking_formula": "MISESERI / max(MISESERI) > errorTarget",
        "legacy_incorrect_rule": "raw MISESERI > errorTarget (absolute)",
        "max_MISESERI": mmax,
        "absolute_equivalent_threshold": error_target * mmax,
        "n_marked": n_marked,
        "fraction_marked": frac,
        "errorTarget": error_target,
        "refinementFactor": refinement_factor,
        "minElementSize_mm": min_h,
        "maxElementSize_mm": max_h,
        "fraction_mark_limit": MAX_MARK_FRACTION,
        "fraction_mark_exceeds_limit": frac > MAX_MARK_FRACTION,
    }


def _element_id(row, default_i):
    for key in ("physical_element_label", "element_id", "elem", "id"):
        if key in row and row[key] not in (None, ""):
            try:
                return int(float(row[key]))
            except Exception:
                pass
    return default_i


def notch_dominant_marked_component(rows):
    """Keep only the connected marked component seeded at max-MISESERI marked elem.

    Connectivity: two elements are adjacent if they share an edge (node pair).
    """
    marked_idx = []
    for i, r in enumerate(rows):
        if r.get("marked_for_refinement") in ("1", 1, True, "True"):
            marked_idx.append(i)
    if not marked_idx:
        return {
            "n_marked_raw": 0,
            "n_marked_component": 0,
            "seed_element": None,
            "method": "no_marked_elements",
        }

    # Build node-pair → element indices for marked elements
    edge_to_elems = defaultdict(list)
    for i in marked_idx:
        r = rows[i]
        try:
            nodes = [
                int(float(r["n1"])),
                int(float(r["n2"])),
                int(float(r["n3"])),
                int(float(r["n4"])),
            ]
        except Exception:
            # no connectivity: fall back to keep all marked
            return {
                "n_marked_raw": len(marked_idx),
                "n_marked_component": len(marked_idx),
                "seed_element": None,
                "method": "no_connectivity_keep_all_marked",
            }
        for a, b in ((0, 1), (1, 2), (2, 3), (3, 0)):
            e = tuple(sorted((nodes[a], nodes[b])))
            edge_to_elems[e].append(i)

    adj = defaultdict(set)
    for elems in edge_to_elems.values():
        for a in elems:
            for b in elems:
                if a != b:
                    adj[a].add(b)

    # Seed: highest MISESERI among marked; prefer near notch tip (0,0)
    def seed_key(i):
        r = rows[i]
        m = float(r["MISESERI"])
        xc = float(r.get("xc", r.get("centroid_x", 0.0)))
        yc = float(r.get("yc", r.get("centroid_y", 0.0)))
        # prioritize high indicator, then proximity to notch tip
        return (m, -math.hypot(xc, yc))

    seed = max(marked_idx, key=seed_key)

    # BFS component
    seen = set([seed])
    q = deque([seed])
    while q:
        u = q.popleft()
        for v in adj.get(u, ()):
            if v not in seen:
                seen.add(v)
                q.append(v)

    # Unmark outside component
    for i in marked_idx:
        if i not in seen:
            rows[i]["marked_for_refinement"] = "0"
            rows[i]["target_h"] = rows[i].get("h_mean", rows[i].get("target_h", "0.005"))

    seed_row = rows[seed]
    return {
        "n_marked_raw": len(marked_idx),
        "n_marked_component": len(seen),
        "seed_element": _element_id(seed_row, seed + 1),
        "seed_centroid": (
            float(seed_row.get("xc", seed_row.get("centroid_x", 0.0))),
            float(seed_row.get("yc", seed_row.get("centroid_y", 0.0))),
        ),
        "seed_MISESERI": float(seed_row["MISESERI"]),
        "method": "connected_component_max_MISESERI_seed",
    }


def refined_zone_from_rows(rows, min_h):
    marked = []
    for r in rows:
        if r.get("marked_for_refinement") in ("1", 1, True, "True"):
            marked.append((float(r["xc"]), float(r["yc"])))
    if not marked:
        return {
            "x_min": -0.02,
            "x_max": 0.05,
            "y_min": -0.01,
            "y_max": 0.01,
            "source": "fallback_default_notch_patch_no_marked_elements",
            "n_marked_points": 0,
        }
    xs = [p[0] for p in marked]
    ys = [p[1] for p in marked]
    pad = max(min_h * 4.0, 0.01)
    zone = {
        "x_min": max(-0.5, min(xs) - pad),
        "x_max": min(0.5, max(xs) + pad),
        "y_min": max(-0.5, min(ys) - pad),
        "y_max": min(0.5, max(ys) + pad),
        "source": "miseseri_notch_component_bbox_padded",
        "n_marked_points": len(marked),
    }
    # Ensure a minimal refined patch around the notch if bbox collapses
    if zone["x_max"] - zone["x_min"] < 2.0 * min_h:
        zone["x_min"] = max(-0.5, zone["x_min"] - min_h)
        zone["x_max"] = min(0.5, zone["x_max"] + min_h)
    if zone["y_max"] - zone["y_min"] < 2.0 * min_h:
        zone["y_min"] = max(-0.5, zone["y_min"] - min_h)
        zone["y_max"] = min(0.5, zone["y_max"] + min_h)
    return zone


def build_mesh(local_h, refined_zone, global_h):
    x_axis, y_axis = make_axis_spacings(local_h, refined_zone, global_h=global_h, ratio=1.5)
    mesh = MeshBuilder(x_axis, y_axis)
    mesh.build_nodes()
    return mesh.node_coords, mesh.element_connectivity(), x_axis, y_axis


def corridor_stats(nodes, conn, zone):
    edges = []
    all_edges = []
    for n1, n2, n3, n4 in conn:
        pts = [nodes[n1], nodes[n2], nodes[n3], nodes[n4]]
        xc = sum(p[0] for p in pts) / 4.0
        yc = sum(p[1] for p in pts) / 4.0
        local = []
        for i in range(4):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % 4]
            e = math.hypot(x1 - x0, y1 - y0)
            local.append(e)
            all_edges.append(e)
        if zone["x_min"] <= xc <= zone["x_max"] and zone["y_min"] <= yc <= zone["y_max"]:
            edges.extend(local)
    def _stats(arr):
        if not arr:
            return None
        arr = sorted(arr)
        mid = len(arr) // 2
        if len(arr) % 2:
            med = arr[mid]
        else:
            med = 0.5 * (arr[mid - 1] + arr[mid])
        return {"min": arr[0], "median": med, "max": arr[-1], "count": len(arr)}

    return {"refined_zone": _stats(edges), "global": _stats(all_edges)}


def far_field_coarse_retained(nodes, conn, zone, max_h, min_h):
    """True if some elements outside refined zone have h well above min size."""
    far_h = []
    for n1, n2, n3, n4 in conn:
        pts = [nodes[n1], nodes[n2], nodes[n3], nodes[n4]]
        xc = sum(p[0] for p in pts) / 4.0
        yc = sum(p[1] for p in pts) / 4.0
        if zone["x_min"] <= xc <= zone["x_max"] and zone["y_min"] <= yc <= zone["y_max"]:
            continue
        # mean edge length
        elen = []
        for i in range(4):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % 4]
            elen.append(math.hypot(x1 - x0, y1 - y0))
        far_h.append(sum(elen) / 4.0)
    if not far_h:
        return False, None
    med = sorted(far_h)[len(far_h) // 2]
    # far-field should be substantially coarser than min_h
    ok = med >= max(2.0 * min_h, 0.5 * max_h * 0.2)
    return ok, {"n_far": len(far_h), "median_h_far": med}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    csv_path = args.csv
    config_path = args.config
    out_dir = args.out

    config = json.loads(config_path.read_text(encoding="utf-8"))
    rule = config["rule"]
    rows = load_rows(csv_path)
    for r in rows:
        if "h_mean" not in r or r["h_mean"] in ("", None):
            try:
                r["h_mean"] = math.sqrt(float(r["EVOL"])) if float(r["EVOL"]) > 0 else 0.005
            except Exception:
                r["h_mean"] = 0.005
        if "xc" not in r or r["xc"] in ("", None):
            r["xc"] = r.get("centroid_x", 0)
            r["yc"] = r.get("centroid_y", 0)

    sizing = apply_marks(rows, rule)
    component = notch_dominant_marked_component(rows)
    # recompute marked fraction after component filter
    n_marked = sum(
        1 for r in rows if r.get("marked_for_refinement") in ("1", 1, True, "True")
    )
    sizing["n_marked_after_component"] = n_marked
    sizing["fraction_marked_after_component"] = (
        n_marked / float(len(rows)) if rows else 0.0
    )
    sizing["component"] = component

    min_h = float(rule["minElementSize_mm"])
    max_h = float(rule["maxElementSize_mm"])
    zone = refined_zone_from_rows(rows, min_h)

    out_dir.mkdir(parents=True, exist_ok=True)

    # Write mark map / size map before mesh build (evidence even on failure)
    marked_csv = out_dir / "marked_elements.csv"
    with open(str(marked_csv), "w") as stream:
        stream.write(
            "physical_element_label,xc,yc,MISESERI,normalized_MISESERI,"
            "marked_for_refinement,target_h,h_mean\n"
        )
        for i, r in enumerate(rows):
            stream.write(
                "%s,%s,%s,%s,%s,%s,%s,%s\n"
                % (
                    _element_id(r, i + 1),
                    r.get("xc"),
                    r.get("yc"),
                    r.get("MISESERI"),
                    r.get("normalized_MISESERI", ""),
                    r.get("marked_for_refinement"),
                    r.get("target_h"),
                    r.get("h_mean"),
                )
            )

    fail_reasons = []
    frac_comp = float(sizing.get("fraction_marked_after_component", 1.0))
    if frac_comp > MAX_MARK_FRACTION:
        fail_reasons.append(
            "component_mark_fraction_%.3f_exceeds_%.2f" % (frac_comp, MAX_MARK_FRACTION)
        )

    nodes, conn, x_axis, y_axis = build_mesh(min_h, zone, max_h)
    n_elem = len(conn)
    n_nodes = len(nodes)

    nodes_csv = out_dir / "refined_mesh_nodes.csv"
    elems_csv = out_dir / "refined_mesh_elements.csv"
    physical_inp = out_dir / "refined_physical.inp"
    with open(str(nodes_csv), "w") as stream:
        stream.write("node_id,x,y\n")
        for nid in sorted(nodes):
            stream.write("%s,%s,%s\n" % (nid, nodes[nid][0], nodes[nid][1]))
    with open(str(elems_csv), "w") as stream:
        stream.write("element_id,n1,n2,n3,n4\n")
        for i, c in enumerate(conn, start=1):
            stream.write("%s,%s,%s,%s,%s\n" % (i, c[0], c[1], c[2], c[3]))
    lines = ["*Heading", "** Refined physical mesh (local MISESERI offline)", "*Node"]
    for nid in sorted(nodes):
        lines.append("%s, %.10g, %.10g" % (nid, nodes[nid][0], nodes[nid][1]))
    lines.append("*Element, type=CPS4, elset=physical")
    for i, c in enumerate(conn, start=1):
        lines.append("%s, %s, %s, %s, %s" % (i, c[0], c[1], c[2], c[3]))
    with open(str(physical_inp), "w") as stream:
        stream.write("\n".join(lines) + "\n")

    stats = corridor_stats(nodes, conn, zone)
    corridor = stats["refined_zone"]
    global_h_stats = stats["global"]
    target_ok = bool(
        corridor and abs(corridor["median"] - min_h) <= 0.25 * min_h
    )
    far_ok, far_info = far_field_coarse_retained(nodes, conn, zone, max_h, min_h)

    if n_elem > MAX_ALLOWED_ELEMENTS:
        fail_reasons.append(
            "n_elements_%d_exceeds_max_allowed_%d" % (n_elem, MAX_ALLOWED_ELEMENTS)
        )
    if not far_ok:
        fail_reasons.append("far_field_coarse_region_not_retained")
    if not target_ok:
        fail_reasons.append("corridor_h_not_near_minElementSize")

    # Zone should be localized (area fraction of plate)
    zone_area = max(0.0, zone["x_max"] - zone["x_min"]) * max(
        0.0, zone["y_max"] - zone["y_min"]
    )
    plate_area = 1.0  # 1 mm x 1 mm
    zone_frac = zone_area / plate_area
    if zone_frac > 0.35:
        fail_reasons.append("refined_zone_area_fraction_%.3f_too_large" % zone_frac)

    status = "pass" if not fail_reasons else "fail_adaptive_efficiency"
    prefer_below_h1 = n_elem < H1_NPHYS

    guards = {
        "minimum_size_reached_near_notch": bool(target_ok),
        "far_field_coarse_region_retained": bool(far_ok),
        "refined_region_spatially_localized": zone_frac <= 0.35,
        "physical_element_count_below_H1_preferred": prefer_below_h1,
        "physical_element_count_below_H2": n_elem < H2_NPHYS,
        "physical_element_count_far_below_160400": n_elem < 40000,
    }

    manifest = {
        "status": status,
        "fail_reasons": fail_reasons,
        "sizing": sizing,
        "refined_zone": zone,
        "zone_area_fraction": zone_frac,
        "n_nodes": n_nodes,
        "n_elements": n_elem,
        "n_elements_reference": {
            "H0": H0_NPHYS,
            "H1": H1_NPHYS,
            "H2_PUB": H2_NPHYS,
            "prior_over_refined_C2C": 160400,
        },
        "ratios": {
            "vs_H0": n_elem / float(H0_NPHYS),
            "vs_H1": n_elem / float(H1_NPHYS),
            "vs_H2_PUB": n_elem / float(H2_NPHYS),
        },
        "corridor_h": corridor,
        "global_h": global_h_stats,
        "far_field": far_info,
        "corridor_h_near_minElementSize": target_ok,
        "guards": guards,
        "claim_boundary": "custom_MISESERI_offline_pre_refinement_not_native_abaqus_adaptive",
        "marking_rule_version": 2,
        "axis_grading": "bounded_refined_window_both_axes",
    }
    (out_dir / "remeshing_rule_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    # size map summary
    (out_dir / "size_map_summary.json").write_text(
        json.dumps(
            {
                "local_h_mm": min_h,
                "global_h_mm": max_h,
                "refined_zone": zone,
                "x_spacings_minmax": (
                    min(x_axis.spacings),
                    max(x_axis.spacings),
                ),
                "y_spacings_minmax": (
                    min(y_axis.spacings),
                    max(y_axis.spacings),
                ),
                "n_x_intervals": len(x_axis.spacings),
                "n_y_intervals": len(y_axis.spacings),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    if status != "pass":
        return 14
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
