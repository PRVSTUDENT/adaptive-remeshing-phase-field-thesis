#!/usr/bin/env python3
"""Build refined physical mesh from MISESERI element-field CSV (system Python).

Used after CAE ODB extraction in Stage C Job 3. No Abaqus/Standard solve.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/model_generation"))

from build_molnar_lc015_h_convergence import MeshBuilder, paper_like_config  # noqa: E402
from estimate_molnar_paper_mesh import make_axis_spacings  # noqa: E402


def load_rows(csv_path: Path) -> list[dict]:
    with csv_path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def apply_marks(rows: list[dict], rule: dict) -> dict:
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
        "fraction_marked": n_marked / len(rows) if rows else 0.0,
        "errorTarget": error_target,
        "refinementFactor": refinement_factor,
        "minElementSize_mm": min_h,
        "maxElementSize_mm": max_h,
    }


def refined_zone_from_rows(rows: list[dict], min_h: float) -> dict:
    marked = [
        (float(r["xc"]), float(r["yc"]))
        for r in rows
        if r.get("marked_for_refinement") in ("1", 1, True, "True")
    ]
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


def build_mesh(local_h: float, refined_zone: dict, global_h: float) -> tuple[dict, list]:
    study = {
        "mesh_recipe": {
            "refined_zone": refined_zone,
            "global_element_size_mm": global_h,
            "maximum_neighbouring_size_ratio": 1.5,
        }
    }
    cfg = paper_like_config(local_h, study)
    cfg["mesh"]["recipe"]["refined_zone"] = refined_zone
    x_axis, y_axis = make_axis_spacings(cfg)
    mesh = MeshBuilder(x_axis, y_axis)
    mesh.build_nodes()
    return mesh.node_coords, mesh.element_connectivity()


def corridor_stats(nodes: dict, conn: list, zone: dict) -> dict | None:
    edges: list[float] = []
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
    med = edges[mid] if len(edges) % 2 else 0.5 * (edges[mid - 1] + edges[mid])
    return {"min": edges[0], "median": med, "max": edges[-1], "count": len(edges)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    rule = config["rule"]
    rows = load_rows(args.csv)
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
            stream.write(f"{nid},{nodes[nid][0]},{nodes[nid][1]}\n")
    with elems_csv.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("element_id,n1,n2,n3,n4\n")
        for i, c in enumerate(conn, start=1):
            stream.write(f"{i},{c[0]},{c[1]},{c[2]},{c[3]}\n")
    lines = ["*Heading", "** Refined physical mesh", "*Node"]
    for nid in sorted(nodes):
        lines.append(f"{nid}, {nodes[nid][0]:.10g}, {nodes[nid][1]:.10g}")
    lines.append("*Element, type=CPS4, elset=physical")
    for i, c in enumerate(conn, start=1):
        lines.append(f"{i}, {c[0]}, {c[1]}, {c[2]}, {c[3]}")
    physical_inp.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    # rewrite marked CSV
    marked_csv = args.out / "miseseri_element_field_marked.csv"
    with marked_csv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)

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
        "paths": {
            "nodes_csv": str(nodes_csv.as_posix()),
            "elements_csv": str(elems_csv.as_posix()),
            "physical_inp": str(physical_inp.as_posix()),
        },
    }
    (args.out / "remeshing_rule_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if target_ok else 14


if __name__ == "__main__":
    raise SystemExit(main())
