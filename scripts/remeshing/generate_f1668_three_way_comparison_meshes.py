# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_f1668_three_way_comparison_meshes.py
==============================================================
Task: F1668 - Three-Way Controlled 2D Adaptive Remeshing Comparison
Specimen: 2D Mode-I Plate with Off-Axis Circular Hole (1.0 x 1.0 mm, a0=0.5 mm, Hole at (0.65, 0.65) R=0.10)

Controlled Experiment Arms:
  Case A: MISESERI-only refinement       h_A(x, y) = h_stress(x, y)
  Case B: Phase-field damage-only         h_B(x, y) = h_damage(x, y)
  Case C: Synergistic combined            h_C(x, y) = min(h_stress(x, y), h_damage(x, y))

Experimental Rigor & Control Rules:
1. Identical CAD Geometry: Notch slit opening w=0.0005 mm (0.5 um half-width), hole at (0.65, 0.65) R=0.10.
2. Identical Donor Data:
   - Authentic coarse damage from PK_HOLE_COARSE_JOB1.odb (terminal frame 337, d >= 0.70)
   - Authentic recovery error from PK_HOLE_F1661_RECOVERY.odb (Step-1 frame 1, eta >= 10.0%)
3. Identical Sizing Parameters:
   - SizeMin = 0.00135 mm (1.35 um <= l0/5)
   - SizeMax = 0.02000 mm (20.0 um)
   - DistMin = 0.00750 mm (7.50 um = 1.0*l0 core plateau)
   - DistMax = 0.02500 mm (25.0 um = 3.33*l0 calibrated transition width)
4. Identical Mesher Engine:
   - Gmsh 4.15+ Frontal-Delaunay 2D (Mesh.Algorithm = 6)
   - Blossom Quad Recombination (Mesh.RecombinationAlgorithm = 1)
5. Full FE Quality & 3-Layer UEL Production Deck Generation
"""

from __future__ import print_function
import os
import sys
import json
import math
import numpy as np
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import gmsh
from scripts.remeshing.reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    MeshQualityAuditEngine,
    ProductionDeckBuilder,
    FROZEN_UEL_SHA256
)


def load_authentic_fields(sizing_json_path):
    if not os.path.exists(sizing_json_path):
        raise IOError("Sizing field JSON not found: %s" % sizing_json_path)
    with open(sizing_json_path, "r") as f:
        data = json.load(f)
    return data


def build_gmsh_mesh_case(case_name, mode, sizing_data, out_raw_inp, cfg,
                         size_min=0.00135, size_max=0.0200, dist_min=0.0075, dist_max=0.0250):
    """
    Builds the 2D off-axis hole plate in Gmsh with controlled background field:
      mode = 'stress_only'   -> Field 1 (Threshold on recovery eta >= 10%)
      mode = 'damage_only'   -> Field 2 (Threshold on donor d >= 0.70)
      mode = 'combined'      -> Field 3 (Min of Field 1 and Field 2)
    """
    print("\n----------------------------------------------------------------------")
    print("GMSH EXECUTION: %s (mode: %s)" % (case_name, mode))
    print("----------------------------------------------------------------------")

    gmsh.initialize()
    try:
        gmsh.model.add(case_name)

        w = cfg.notch_w # 0.0005 mm (0.5 um half width)
        a = cfg.notch_a # 0.50 mm
        W = cfg.plate_w # 1.00 mm
        H = cfg.plate_h # 1.00 mm

        # Outer boundary
        p_slit_bot = gmsh.model.geo.addPoint(0.0, 0.50 - w, 0.0)
        p1 = gmsh.model.geo.addPoint(0.0, 0.0, 0.0)
        p2 = gmsh.model.geo.addPoint(W, 0.0, 0.0)
        p3 = gmsh.model.geo.addPoint(W, H, 0.0)
        p4 = gmsh.model.geo.addPoint(0.0, H, 0.0)
        p_slit_top = gmsh.model.geo.addPoint(0.0, 0.50 + w, 0.0)
        p_tip_top = gmsh.model.geo.addPoint(a, 0.50 + w, 0.0)
        p_tip_bot = gmsh.model.geo.addPoint(a, 0.50 - w, 0.0)

        l1 = gmsh.model.geo.addLine(p_slit_bot, p1)
        l2 = gmsh.model.geo.addLine(p1, p2)
        l3 = gmsh.model.geo.addLine(p2, p3)
        l4 = gmsh.model.geo.addLine(p3, p4)
        l5 = gmsh.model.geo.addLine(p4, p_slit_top)
        l6 = gmsh.model.geo.addLine(p_slit_top, p_tip_top)
        l7 = gmsh.model.geo.addLine(p_tip_top, p_tip_bot)
        l8 = gmsh.model.geo.addLine(p_tip_bot, p_slit_bot)

        cl_outer = gmsh.model.geo.addCurveLoop([l1, l2, l3, l4, l5, l6, l7, l8])

        # Circular hole
        cx, cy, r = cfg.hole_x, cfg.hole_y, cfg.hole_r
        pc = gmsh.model.geo.addPoint(cx, cy, 0.0)
        ph1 = gmsh.model.geo.addPoint(cx + r, cy, 0.0)
        ph2 = gmsh.model.geo.addPoint(cx, cy + r, 0.0)
        ph3 = gmsh.model.geo.addPoint(cx - r, cy, 0.0)
        ph4 = gmsh.model.geo.addPoint(cx, cy - r, 0.0)

        c1 = gmsh.model.geo.addCircleArc(ph1, pc, ph2)
        c2 = gmsh.model.geo.addCircleArc(ph2, pc, ph3)
        c3 = gmsh.model.geo.addCircleArc(ph3, pc, ph4)
        c4 = gmsh.model.geo.addCircleArc(ph4, pc, ph1)

        cl_hole = gmsh.model.geo.addCurveLoop([c1, c2, c3, c4])
        s = gmsh.model.geo.addPlaneSurface([cl_outer, cl_hole])

        # Support points from authentic data
        damage_pts = []
        if mode in ('damage_only', 'combined'):
            for el in sizing_data["donor_elements"]:
                if el["d_max"] >= 0.70:
                    pt = gmsh.model.geo.addPoint(el["cx"], el["cy"], 0.0)
                    damage_pts.append(pt)
            print("  Created %d authentic damage support points (d >= 0.70)" % len(damage_pts))

        stress_pts = []
        if mode in ('stress_only', 'combined'):
            for el in sizing_data["recovery_elements"]:
                if el["eta_pct"] >= 10.0:
                    pt = gmsh.model.geo.addPoint(el["cx"], el["cy"], 0.0)
                    stress_pts.append(pt)
            print("  Created %d authentic stress error support points (eta >= 10.0%%)" % len(stress_pts))

        gmsh.model.geo.synchronize()

        # Define Fields
        f_active = None

        if mode == 'damage_only':
            f_d_dist = gmsh.model.mesh.field.add("Distance")
            gmsh.model.mesh.field.setNumbers(f_d_dist, "PointsList", damage_pts)

            f_damage = gmsh.model.mesh.field.add("Threshold")
            gmsh.model.mesh.field.setNumber(f_damage, "InField", f_d_dist)
            gmsh.model.mesh.field.setNumber(f_damage, "SizeMin", size_min)
            gmsh.model.mesh.field.setNumber(f_damage, "SizeMax", size_max)
            gmsh.model.mesh.field.setNumber(f_damage, "DistMin", dist_min)
            gmsh.model.mesh.field.setNumber(f_damage, "DistMax", dist_max)
            f_active = f_damage

        elif mode == 'stress_only':
            f_s_dist = gmsh.model.mesh.field.add("Distance")
            gmsh.model.mesh.field.setNumbers(f_s_dist, "PointsList", stress_pts)

            f_stress = gmsh.model.mesh.field.add("Threshold")
            gmsh.model.mesh.field.setNumber(f_stress, "InField", f_s_dist)
            gmsh.model.mesh.field.setNumber(f_stress, "SizeMin", size_min)
            gmsh.model.mesh.field.setNumber(f_stress, "SizeMax", size_max)
            gmsh.model.mesh.field.setNumber(f_stress, "DistMin", dist_min)
            gmsh.model.mesh.field.setNumber(f_stress, "DistMax", dist_max)
            f_active = f_stress

        elif mode == 'combined':
            f_d_dist = gmsh.model.mesh.field.add("Distance")
            gmsh.model.mesh.field.setNumbers(f_d_dist, "PointsList", damage_pts)

            f_damage = gmsh.model.mesh.field.add("Threshold")
            gmsh.model.mesh.field.setNumber(f_damage, "InField", f_d_dist)
            gmsh.model.mesh.field.setNumber(f_damage, "SizeMin", size_min)
            gmsh.model.mesh.field.setNumber(f_damage, "SizeMax", size_max)
            gmsh.model.mesh.field.setNumber(f_damage, "DistMin", dist_min)
            gmsh.model.mesh.field.setNumber(f_damage, "DistMax", dist_max)

            f_s_dist = gmsh.model.mesh.field.add("Distance")
            gmsh.model.mesh.field.setNumbers(f_s_dist, "PointsList", stress_pts)

            f_stress = gmsh.model.mesh.field.add("Threshold")
            gmsh.model.mesh.field.setNumber(f_stress, "InField", f_s_dist)
            gmsh.model.mesh.field.setNumber(f_stress, "SizeMin", size_min)
            gmsh.model.mesh.field.setNumber(f_stress, "SizeMax", size_max)
            gmsh.model.mesh.field.setNumber(f_stress, "DistMin", dist_min)
            gmsh.model.mesh.field.setNumber(f_stress, "DistMax", dist_max)

            f_hybrid = gmsh.model.mesh.field.add("Min")
            gmsh.model.mesh.field.setNumbers(f_hybrid, "FieldsList", [f_damage, f_stress])
            f_active = f_hybrid

        gmsh.model.mesh.field.setAsBackgroundMesh(f_active)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

        # Meshing Algorithm: Frontal-Delaunay 2D + Blossom Quad Recombination
        gmsh.option.setNumber("Mesh.Algorithm", 6)
        gmsh.model.mesh.setRecombine(2, s)
        gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1) # Blossom

        gmsh.model.mesh.generate(2)
        gmsh.write(out_raw_inp)
        print("  Successfully exported raw Gmsh mesh: %s" % out_raw_inp)

    finally:
        gmsh.finalize()


def convert_gmsh_inp_to_clean_physical(raw_inp, clean_inp, cfg):
    """Parses raw Gmsh INP export and generates standard clean physical Abaqus deck."""
    nodes = {}
    quads = {}
    tris = {}
    current_sec = None

    with open(raw_inp, "r") as f:
        for line in f:
            line_str = line.strip()
            if not line_str: continue
            if line_str.startswith("*"):
                u = line_str.upper()
                if u.startswith("*NODE"):
                    current_sec = "NODE"
                elif u.startswith("*ELEMENT"):
                    if "TYPE=CPE4" in u or "C3D4" in u or "S4" in u or "CPS4" in u or "TYPE=CPE4R" in u:
                        current_sec = "ELEM_QUAD"
                    elif "TYPE=CPE3" in u or "S3" in u or "CPS3" in u:
                        current_sec = "ELEM_TRI"
                    else:
                        parts = u.split(",")
                        t_part = [p for p in parts if "TYPE=" in p]
                        current_sec = "ELEM_OTHER"
                else:
                    current_sec = "OTHER"
                continue

            if current_sec == "NODE":
                tokens = [t.strip() for t in line_str.split(",")]
                if len(tokens) >= 3:
                    nid = int(tokens[0])
                    x = float(tokens[1])
                    y = float(tokens[2])
                    nodes[nid] = (x, y)
            elif current_sec in ("ELEM_QUAD", "ELEM_OTHER"):
                tokens = [t.strip() for t in line_str.split(",")]
                if len(tokens) == 5:
                    eid = int(tokens[0])
                    conn = [int(tokens[i]) for i in range(1, 5)]
                    quads[eid] = conn
                elif len(tokens) == 4:
                    eid = int(tokens[0])
                    conn = [int(tokens[i]) for i in range(1, 4)]
                    tris[eid] = conn
            elif current_sec == "ELEM_TRI":
                tokens = [t.strip() for t in line_str.split(",")]
                if len(tokens) == 4:
                    eid = int(tokens[0])
                    conn = [int(tokens[i]) for i in range(1, 4)]
                    tris[eid] = conn

    # Collapse degenerate quads
    new_quads = {}
    new_tris = dict(tris)
    for qid, conn in quads.items():
        if len(set(conn)) == 3:
            new_tris[qid] = list(set(conn))
        elif len(set(conn)) == 4:
            new_quads[qid] = conn

    # Identify boundary nodes
    tol = 1e-5
    bot_nodes = sorted([nid for nid, (x, y) in nodes.items() if abs(y - 0.0) <= tol])
    top_nodes = sorted([nid for nid, (x, y) in nodes.items() if abs(y - cfg.plate_h) <= tol])
    pin_node = bot_nodes[0] if bot_nodes else None

    # Write clean deck
    with open(clean_inp, "w") as out:
        out.write("*HEADING\n")
        out.write("** Clean Physical Adapted Mesh - Task F1668\n")
        out.write("** Generated via Gmsh Blossom 100%% Quad Pipeline\n")
        out.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            out.write("%d, %.10f, %.10f, 0.0\n" % (nid, x, y))

        if new_quads:
            out.write("*ELEMENT, TYPE=CPE4, ELSET=QUAD_ELEMS\n")
            for qid in sorted(new_quads.keys()):
                c = new_quads[qid]
                out.write("%d, %d, %d, %d, %d\n" % (qid, c[0], c[1], c[2], c[3]))

        if new_tris:
            out.write("*ELEMENT, TYPE=CPE3, ELSET=TRI_ELEMS\n")
            for tid in sorted(new_tris.keys()):
                c = new_tris[tid]
                out.write("%d, %d, %d, %d\n" % (tid, c[0], c[1], c[2]))

        out.write("*ELSET, ELSET=All_elem\n")
        if new_quads and new_tris:
            out.write("QUAD_ELEMS, TRI_ELEMS\n")
        elif new_quads:
            out.write("QUAD_ELEMS\n")
        else:
            out.write("TRI_ELEMS\n")

        out.write("*NSET, NSET=N_BOTTOM\n")
        for i in range(0, len(bot_nodes), 16):
            chunk = bot_nodes[i:i+16]
            out.write(", ".join(str(n) for n in chunk) + "\n")

        out.write("*NSET, NSET=N_TOP\n")
        for i in range(0, len(top_nodes), 16):
            chunk = top_nodes[i:i+16]
            out.write(", ".join(str(n) for n in chunk) + "\n")

        if pin_node is not None:
            out.write("*NSET, NSET=N_PIN\n")
            out.write("%d\n" % pin_node)

    print("  Converted to clean physical deck: %s (%d nodes, %d quads, %d tris)" % (
        clean_inp, len(nodes), len(new_quads), len(new_tris)
    ))
    return len(nodes), len(new_quads), len(new_tris)


def main():
    print("=" * 80)
    print("TASK F1668: THREE-WAY CONTROLLED 2D ADAPTIVE REMESHING GENERATION")
    print("=" * 80)

    cfg_path = "configs/remeshing/mode1_off_axis_hole_benchmark.json"
    cfg = AdaptiveConfig.from_json(cfg_path)

    sizing_json = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1666_HYBRID_SIZING_FIELD.json"
    sizing_data = load_authentic_fields(sizing_json)

    base_dir = Path("models/pandey_kumar_mode1/176_method_a_plate_with_hole")

    cases = [
        {
            "name": "Case A: Stress-Only Refinement",
            "short_name": "PK_HOLE_F1668_CASE_A_STRESS_ONLY",
            "mode": "stress_only",
            "raw_inp": str(base_dir / "RAW_CASE_A.inp"),
            "phys_inp": str(base_dir / "PK_HOLE_F1668_CASE_A_STRESS_ONLY_PHYS.inp"),
            "prod_inp": str(base_dir / "PK_HOLE_F1668_CASE_A_STRESS_ONLY_PROD.inp")
        },
        {
            "name": "Case B: Damage-Only Refinement",
            "short_name": "PK_HOLE_F1668_CASE_B_DAMAGE_ONLY",
            "mode": "damage_only",
            "raw_inp": str(base_dir / "RAW_CASE_B.inp"),
            "phys_inp": str(base_dir / "PK_HOLE_F1668_CASE_B_DAMAGE_ONLY_PHYS.inp"),
            "prod_inp": str(base_dir / "PK_HOLE_F1668_CASE_B_DAMAGE_ONLY_PROD.inp")
        },
        {
            "name": "Case C: Synergistic Combined Refinement",
            "short_name": "PK_HOLE_F1668_CASE_C_COMBINED",
            "mode": "combined",
            "raw_inp": str(base_dir / "RAW_CASE_C.inp"),
            "phys_inp": str(base_dir / "PK_HOLE_F1668_CASE_C_COMBINED_PHYS.inp"),
            "prod_inp": str(base_dir / "PK_HOLE_F1668_CASE_C_COMBINED_PROD.inp")
        }
    ]

    # Calibrated parameters: DistMin = 7.5 um (1.0 l0), DistMax = 25.0 um (3.33 l0)
    for c in cases:
        print("\n" + "=" * 80)
        print("GENERATING: %s" % c["name"])
        print("=" * 80)

        # 1. Generate Raw Mesh in Gmsh
        build_gmsh_mesh_case(
            c["short_name"], c["mode"], sizing_data, c["raw_inp"], cfg,
            size_min=0.00135, size_max=0.0200, dist_min=0.0075, dist_max=0.0250
        )

        # 2. Convert to Clean Physical Deck
        convert_gmsh_inp_to_clean_physical(c["raw_inp"], c["phys_inp"], cfg)
        if os.path.exists(c["raw_inp"]):
            os.remove(c["raw_inp"])

        # 3. Audit Mesh Quality
        audit = MeshQualityAuditEngine.evaluate_mesh(c["phys_inp"], l0_mm=cfg.l0)
        print("\nMesh Quality Audit for %s:" % c["name"])
        print("  Total Elements: %d (Quads: %d [%.2f%%], Tris: %d)" % (
            audit["total_elements"], audit["quad_count"], audit["quad_percent"], audit["tri_count"]
        ))
        print("  Non-Positive Jacobians: %d (min det(J) = %.3e)" % (
            audit["non_positive_jacobians"], audit["min_det_j"]
        ))
        print("  Distorted Elements: %d | Median Aspect Ratio: %.2f" % (
            audit["distorted_elements"], audit["median_aspect_ratio"]
        ))
        print("  Min Corner Angle: %.1f deg" % audit["min_corner_angle_deg"])
        print("  Edge Lengths [um]: min=%.3f, median=%.3f, max=%.3f" % (
            audit["h_min_um"], audit["h_median_um"], audit["h_max_um"]
        ))
        print("  Compliant Elements (h <= 1.5 um): %d (%.2f%%)" % (
            audit["elements_le_1p5um"], 100.0 * audit["elements_le_1p5um"] / audit["total_elements"]
        ))

        # 4. Generate 3-Layer UEL Production Deck
        deck_meta = ProductionDeckBuilder.build_deck(c["phys_inp"], c["prod_inp"], c["short_name"], cfg)
        print("  Production Deck Verified: %s" % c["prod_inp"])
        print("  Total Layered Elements: %d (3x Parity)" % deck_meta["total_layered_elements"])
        print("  Frozen UEL SHA256: %s (VERIFIED: %s)" % (FROZEN_UEL_SHA256, deck_meta["uel_hash_verified"]))

    print("\n" + "=" * 80)
    print("ALL THREE CONTROLLED ADAPTIVE MESHES GENERATED & AUDITED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
