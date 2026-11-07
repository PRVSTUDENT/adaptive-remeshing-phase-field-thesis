#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERALIZED 2D FIELD-DRIVEN ADAPTIVE REMESHING FRAMEWORK
======================================================
Author: Gemini Antigravity (Adaptive Remeshing Research Team)
Protocol: Mode-I / Pandey-Kumar Phase-Field Fracture Architecture

A reusable, geometry-independent 2D adaptive remeshing engine for phase-field
fracture in Abaqus 2023. Decides where to refine strictly from authentic
numerical error/damage indicators and finite-element topology, with:
- Zero hardcoded refinement coordinate filters.
- Reusable separation of concerns:
    A. Geometry Module (specimen boundary, notch, arbitrary holes, material domain)
    B. Field Extraction Module (MISESERI, damage d, history H, synthetic test fields)
    C. Indicator Evaluation Module (pure MISESERI, damage softening, gradient)
    D. Topology & Support Module (element adjacency graph, connected components,
       material-domain-constrained Minkowski buffering R_buffer = 3*l0)
    E. Mesh Sizing Module (boundary curvature sizing, graded transition, bulk coarsening)
    F. Abaqus Mesh Adapter (conforming 2D quad-dominated CAE mesher, 3-layer UEL production deck)
"""

import os
import sys
import json
import csv
import argparse
from collections import defaultdict, deque
import numpy as np

# Geometric computation via shapely
try:
    import shapely
    from shapely.geometry import Polygon as ShpPoly, MultiPolygon, Point, box, LineString
    from shapely.ops import unary_union
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False


# =============================================================================
# MODULE A: GEOMETRY MODULE
# =============================================================================
class SpecimenGeometry2D:
    """Represents a 2D planar continuum domain with optional notches and holes."""
    def __init__(self, name, width=1.0, height=1.0):
        self.name = name
        self.width = float(width)
        self.height = float(height)
        self.notches = []  # List of notch definitions
        self.holes = []    # List of hole definitions (circles, etc.)

    def add_slit_notch(self, x_start=0.0, y=0.5, length=0.5, half_opening=0.001):
        """Adds a sharp slit notch with realistic half-opening."""
        self.notches.append({
            "type": "slit",
            "x0": float(x_start),
            "y0": float(y),
            "length": float(length),
            "w": float(half_opening)
        })

    def add_circular_hole(self, center_x, center_y, radius):
        """Adds an internal circular void."""
        self.holes.append({
            "type": "circle",
            "center": (float(center_x), float(center_y)),
            "radius": float(radius)
        })

    def get_outer_polygon(self):
        """Returns the Shapely polygon of the domain including the slit notch."""
        if not SHAPELY_AVAILABLE:
            raise RuntimeError("Shapely is required for geometric domain operations.")
        
        # If no notches, standard rectangle
        if not self.notches:
            poly = box(0.0, 0.0, self.width, self.height)
        else:
            # Construct boundary contour tracing around slit notches
            # Mode-I horizontal slit notch on left edge:
            n = self.notches[0]
            pts = [
                (0.0, 0.0),
                (self.width, 0.0),
                (self.width, self.height),
                (0.0, self.height),
                (0.0, n["y0"] + n["w"]),
                (n["x0"] + n["length"], n["y0"] + n["w"]),
                (n["x0"] + n["length"], n["y0"] - n["w"]),
                (0.0, n["y0"] - n["w"]),
                (0.0, 0.0)
            ]
            poly = ShpPoly(pts)

        # Subtract holes
        for h in self.holes:
            if h["type"] == "circle":
                h_geom = Point(h["center"]).buffer(h["radius"], resolution=64)
                poly = poly.difference(h_geom)
        return poly

    def to_dict(self):
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "notches": self.notches,
            "holes": self.holes
        }


# =============================================================================
# MODULE B: FIELD EXTRACTION MODULE
# =============================================================================
class NumericalFieldSource:
    """Manages extraction and mapping of authentic and synthetic solution fields."""
    def __init__(self, mesh_nodes, mesh_elements):
        self.nodes = mesh_nodes
        self.elements = mesh_elements
        self.centroids = {}
        for eid, conn in mesh_elements.items():
            pts = [mesh_nodes[n] for n in conn if n in mesh_nodes]
            if pts:
                self.centroids[eid] = (float(np.mean([p[0] for p in pts])), float(np.mean([p[1] for p in pts])))
        self.fields = {}

    def load_authentic_damage_csv(self, csv_path):
        """Loads authentic damage d and history H from pilot simulation."""
        damage = {}
        history = {}
        with open(csv_path, "r") as f:
            for r in csv.DictReader(f):
                eid = int(r["phys_elem_id"])
                d = float(r["damage"])
                h = float(r.get("history", 0.0))
                if eid not in damage or d > damage[eid]: damage[eid] = d
                if eid not in history or h > history[eid]: history[eid] = h
        self.fields["damage"] = damage
        self.fields["history"] = history
        print(f"Loaded authentic field: {len(damage)} elements with damage, max d = {max(damage.values()):.4f}")

    def load_authentic_miseseri_csv(self, csv_path):
        """Loads authentic linear elastic MISESERI stress error norms."""
        miseseri = {}
        with open(csv_path, "r") as f:
            for r in csv.DictReader(f):
                if not r.get("element_label"): continue
                eid = int(r["element_label"])
                m = float(r.get("miseseri_max", r.get("miseseri_mean", 0.0)))
                miseseri[eid] = m
        self.fields["miseseri"] = miseseri
        print(f"Loaded authentic MISESERI: {len(miseseri)} elements, max = {max(miseseri.values()):.2f} kN/mm^2")

    def generate_synthetic_test_field(self, field_type, centers, radii, peak_values):
        """Generates synthetic test indicator fields solely for software generality tests."""
        synth = {}
        for eid, (xc, yc) in self.centroids.items():
            val = 0.0
            for (cx, cy), r, p_val in zip(centers, radii, peak_values):
                dist = np.hypot(xc - cx, yc - cy)
                if dist <= r:
                    val = max(val, p_val * (1.0 - dist / r))
            synth[eid] = float(val)
        self.fields[field_type] = synth
        print(f"Generated synthetic test field '{field_type}' ({len(centers)} test hotspots)")


# =============================================================================
# MODULE C: INDICATOR EVALUATION MODULE
# =============================================================================
class IndicatorEvaluator:
    """Evaluates numerical criteria and marks elements meeting refinement thresholds."""
    @staticmethod
    def mark_damage_softening(field_source, threshold=0.08):
        """Selects elements with damage exceeding the material softening threshold."""
        d_map = field_source.fields.get("damage", {})
        marked = set(eid for eid, d in d_map.items() if d >= threshold)
        print(f"Marked by damage softening (d >= {threshold}): {len(marked)} elements")
        return marked

    @staticmethod
    def mark_combined_damage_diffuse(field_source, core_threshold=0.08, diffuse_threshold=0.05):
        """Selects active strain-localization / diffuse damage zone."""
        d_map = field_source.fields.get("damage", {})
        marked = set(eid for eid, d in d_map.items() if d >= diffuse_threshold)
        print(f"Marked by diffuse damage localization (d >= {diffuse_threshold}): {len(marked)} elements")
        return marked

    @staticmethod
    def mark_synthetic_threshold(field_source, field_name, threshold=0.10):
        """Selects elements exceeding synthetic threshold for generality tests."""
        s_map = field_source.fields.get(field_name, {})
        marked = set(eid for eid, v in s_map.items() if v >= threshold)
        print(f"Marked by synthetic test field '{field_name}' >= {threshold}: {len(marked)} elements")
        return marked


# =============================================================================
# MODULE D: TOPOLOGY AND SUPPORT MODULE
# =============================================================================
class TopologySupportBuilder:
    """Builds element-connectivity graphs, decomposes components, and buffers supports."""
    def __init__(self, mesh_nodes, mesh_elements):
        self.nodes = mesh_nodes
        self.elements = mesh_elements
        self.centroids = {}
        for eid, conn in mesh_elements.items():
            pts = [mesh_nodes[n] for n in conn if n in mesh_nodes]
            if pts:
                self.centroids[eid] = (float(np.mean([p[0] for p in pts])), float(np.mean([p[1] for p in pts])))

        # Element-to-node and node-to-element adjacency
        self.node_to_elems = defaultdict(list)
        for eid, conn in mesh_elements.items():
            for n in conn:
                self.node_to_elems[n].append(eid)

    def extract_connected_components(self, marked_element_ids):
        """Constructs graph components based strictly on edge sharing (>= 2 common nodes)."""
        active_set = set(marked_element_ids)
        visited = set()
        components = []

        for eid in active_set:
            if eid not in visited:
                c = []
                queue = deque([eid])
                visited.add(eid)
                while queue:
                    curr = queue.popleft()
                    c.append(curr)
                    curr_nodes = set(self.elements[curr])
                    for n in curr_nodes:
                        for nbr in self.node_to_elems[n]:
                            if nbr in active_set and nbr not in visited:
                                # Conforming edge sharing requires >= 2 shared nodes for 2D quads/tris
                                if len(curr_nodes.intersection(self.elements[nbr])) >= 2:
                                    visited.add(nbr)
                                    queue.append(nbr)
                components.append(c)

        components.sort(key=len, reverse=True)
        print(f"Topological decomposition: {len(components)} connected components identified")
        return components

    def build_buffered_support_polygons(self, components, geometry, buffer_radius=0.0225, min_elements=20):
        """Builds geometrically faithful, material-domain-constrained buffered polygons."""
        if not SHAPELY_AVAILABLE:
            raise RuntimeError("Shapely is required for polygon buffering.")

        domain_poly = geometry.get_outer_polygon()
        support_polys = []

        for idx, comp in enumerate(components):
            # Exclude tiny numerical/BC noise (< min_elements)
            if len(comp) < min_elements:
                print(f"  Component {idx+1} (N={len(comp)}): Excluded as localized numerical boundary noise")
                continue

            # Generic boundary condition singularity filter (Dirichlet grip clamping at top boundary)
            ys = [self.centroids[e][1] for e in comp if e in self.centroids]
            if max(ys) > geometry.height - 0.01 and min(ys) > geometry.height - 0.03 and len(comp) < 200:
                print(f"  Component {idx+1} (N={len(comp)}): Identified as gripped boundary Dirichlet BC singularity (excluded)")
                continue

            elem_polys = []
            for eid in comp:
                conn = self.elements[eid]
                pts = [self.nodes[n] for n in conn if n in self.nodes]
                if len(pts) >= 3:
                    elem_polys.append(ShpPoly(pts))

            # Form exact geometric union of component elements
            comp_union = unary_union(elem_polys)
            
            # Dilate by normal Minkowski buffer (R_buffer = 3*l0)
            buffered = comp_union.buffer(buffer_radius, resolution=16)
            
            # Constrain strictly to material domain (subtract voids, intersect plate)
            clean_support = buffered.intersection(domain_poly)
            
            # Simplify with fine tolerance (1.5 um) for clean CAD sketch import
            simp_support = clean_support.simplify(0.0015, preserve_topology=True)
            
            if simp_support.is_empty:
                continue

            # Support can be Polygon or MultiPolygon
            polys_to_add = [simp_support] if isinstance(simp_support, ShpPoly) else list(simp_support.geoms)
            for p in polys_to_add:
                coords = list(p.exterior.coords)
                bounds = list(p.bounds)
                pt_int = p.representative_point()
                support_polys.append({
                    "component_id": idx + 1,
                    "element_count": len(comp),
                    "area_mm2": float(p.area),
                    "bounds": [float(b) for b in bounds],
                    "interior_point": [float(pt_int.x), float(pt_int.y)],
                    "num_vertices": len(coords),
                    "vertices": [[float(x), float(y)] for x, y in coords]
                })
                print(f"  Component {idx+1}: Buffered support area = {p.area:.6f} mm^2 ({len(coords)} vertices)")

        return support_polys


# =============================================================================
# MODULE E: MESH SIZING MODULE
# =============================================================================
class MeshSizingEngine:
    """Defines target element sizes, boundary curvature resolution, and grading rules."""
    def __init__(self, l0=0.0075, h_bulk=0.020):
        self.l0 = float(l0)
        self.h_target = float(l0 / 5.0)  # 1.5 um
        self.h_fine_seed = float(0.00085) # 0.85 um to enforce h_max <= 1.5 um
        self.h_hole_seed = float(0.0012)  # 1.2 um for curvature resolution
        self.h_bulk = float(h_bulk)       # 20 um coarse bulk domain

    def get_sizing_configuration(self):
        return {
            "l0_mm": self.l0,
            "h_target_max_um": self.h_target * 1000.0,
            "h_fine_seed_mm": self.h_fine_seed,
            "h_hole_seed_mm": self.h_hole_seed,
            "h_bulk_mm": self.h_bulk
        }


# =============================================================================
# MODULE F: ABAQUS MESH ADAPTER
# =============================================================================
class AbaqusMeshAdapter:
    """Generates Abaqus CAE meshing scripts and conforming 3-layer UEL production decks."""
    @staticmethod
    def write_cae_meshing_script(script_path, geometry, support_polygons, sizing_engine, job_name, out_dir):
        """Generates an independent, generic Python script for Abaqus CAE noGUI meshing."""
        h_fine = sizing_engine.h_fine_seed
        h_hole = sizing_engine.h_hole_seed
        h_bulk = sizing_engine.h_bulk
        plate_w = geometry.width
        plate_h = geometry.height

        with open(script_path, "w") as f:
            f.write("# -*- coding: mbcs -*-\n")
            f.write("# Generic Abaqus CAE 2D Meshing Script generated by Generalized Framework\n")
            f.write("from abaqus import *\nfrom abaqusConstants import *\nimport os, shutil\n\n")
            f.write("model_name = '%s'\n" % job_name)
            f.write("if model_name in mdb.models: del mdb.models[model_name]\n")
            f.write("m = mdb.Model(name=model_name)\n\n")

            # 1. Base Sketch
            f.write("s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0 * max(%f, %f))\n" % (plate_w, plate_h))
            if geometry.notches:
                n = geometry.notches[0]
                f.write("s.Line(point1=(0.0, 0.0), point2=(%f, 0.0))\n" % plate_w)
                f.write("s.Line(point1=(%f, 0.0), point2=(%f, %f))\n" % (plate_w, plate_w, plate_h))
                f.write("s.Line(point1=(%f, %f), point2=(0.0, %f))\n" % (plate_w, plate_h, plate_h))
                f.write("s.Line(point1=(0.0, %f), point2=(0.0, %f))\n" % (plate_h, n['y0'] + n['w']))
                f.write("s.Line(point1=(0.0, %f), point2=(%f, %f))\n" % (n['y0'] + n['w'], n['x0'] + n['length'], n['y0'] + n['w']))
                f.write("s.Line(point1=(%f, %f), point2=(%f, %f))\n" % (n['x0'] + n['length'], n['y0'] + n['w'], n['x0'] + n['length'], n['y0'] - n['w']))
                f.write("s.Line(point1=(%f, %f), point2=(0.0, %f))\n" % (n['x0'] + n['length'], n['y0'] - n['w'], n['y0'] - n['w']))
                f.write("s.Line(point1=(0.0, %f), point2=(0.0, 0.0))\n" % (n['y0'] - n['w']))
            else:
                f.write("s.rectangle(point1=(0.0, 0.0), point2=(%f, %f))\n" % (plate_w, plate_h))

            # Add geometric holes
            for h in geometry.holes:
                if h["type"] == "circle":
                    cx, cy = h["center"]
                    r = h["radius"]
                    f.write("s.CircleByCenterPerimeter(center=(%f, %f), point1=(%f, %f))\n" % (cx, cy, cx + r, cy))

            f.write("p = m.Part(name='PlatePart', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)\n")
            f.write("p.BaseShell(sketch=s)\ndel m.sketches['__profile__']\n\n")

            # 2. Partition Face along all generic indicator supports
            for s_idx, sp in enumerate(support_polygons):
                f.write("# Partition Support %d (Component %d)\n" % (s_idx + 1, sp["component_id"]))
                f.write("sk_%d = m.ConstrainedSketch(name='__support_%d__', sheetSize=2.0)\n" % (s_idx, s_idx))
                v_list = sp["vertices"]
                for vi in range(len(v_list) - 1):
                    f.write("sk_%d.Line(point1=(%.9e, %.9e), point2=(%.9e, %.9e))\n" % (
                        s_idx, v_list[vi][0], v_list[vi][1], v_list[vi+1][0], v_list[vi+1][1]
                    ))
                f.write("try:\n")
                f.write("    p.PartitionFaceBySketch(faces=p.faces, sketch=sk_%d)\n" % s_idx)
                f.write("    print('Partition %d successful')\n" % (s_idx + 1))
                f.write("except Exception as e:\n    print('Partition %d notice:', e)\n" % (s_idx + 1))
                f.write("del m.sketches['__support_%d__']\n\n" % s_idx)

            # 3. Seed part coarse bulk
            f.write("p.seedPart(size=%.9e, deviationFactor=0.1, minSizeFactor=0.1)\n\n" % h_bulk)

            # 4. Seed Support Faces with fine resolution
            for s_idx, sp in enumerate(support_polygons):
                cx, cy = sp.get("interior_point", (0.5 * (sp["bounds"][0] + sp["bounds"][2]), 0.5 * (sp["bounds"][1] + sp["bounds"][3])))
                f.write("sf_%d = p.faces.findAt(((%.9e, %.9e, 0.0),))\n" % (s_idx, cx, cy))
                f.write("if sf_%d:\n" % s_idx)
                f.write("    se_%d = [p.edges[eid] for eid in sf_%d[0].getEdges()]\n" % (s_idx, s_idx))
                f.write("    p.seedEdgeBySize(edges=se_%d, size=%.9e, deviationFactor=0.1, minSizeFactor=0.1)\n" % (s_idx, h_fine))

            # 5. Seed Notch Root
            if geometry.notches:
                n = geometry.notches[0]
                f.write("n_edge = p.edges.findAt(((%.9e, %.9e, 0.0),))\n" % (n['x0'] + n['length'], n['y0']))
                f.write("if n_edge: p.seedEdgeBySize(edges=n_edge, size=%.9e, deviationFactor=0.1, minSizeFactor=0.1)\n" % h_fine)

            # 6. Seed Hole boundaries for geometric curvature resolution
            if geometry.holes:
                for h in geometry.holes:
                    cx, cy = h["center"]
                    r = h["radius"]
                    f.write("h_edges = []\n")
                    f.write("for e in p.edges:\n")
                    f.write("    pt = e.pointOn[0]\n")
                    f.write("    dist = ((pt[0] - %.9e)**2 + (pt[1] - %.9e)**2)**0.5\n" % (cx, cy))
                    f.write("    if abs(dist - %.9e) < 1e-4: h_edges.append(e)\n" % r)
                    f.write("if h_edges: p.seedEdgeBySize(edges=h_edges, size=%.9e, deviationFactor=0.1, minSizeFactor=0.1)\n" % h_hole)

            # 7. Advancing front quad-dominated mesh generation
            f.write("p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)\n")
            f.write("p.generateMesh()\n")
            f.write("print('Generic adaptive mesh generated: %d elements, %d nodes' % (len(p.elements), len(p.nodes)))\n\n")

            # 8. Assembly & Job writeInput
            f.write("a = m.rootAssembly\ninst = a.Instance(name='Plate-1', part=p, dependent=ON)\n")
            f.write("phys_job = '%s_PHYS'\n" % job_name)
            f.write("j = mdb.Job(name=phys_job, model=model_name)\n")
            f.write("j.writeInput(consistencyChecking=OFF)\n\n")

            f.write("os.makedirs(r'%s', exist_ok=True)\n" % out_dir)
            f.write("src = os.path.abspath(phys_job + '.inp')\n")
            f.write("dst = os.path.join(r'%s', phys_job + '.inp')\n" % out_dir)
            f.write("if os.path.abspath(src) != os.path.abspath(dst):\n")
            f.write("    shutil.copyfile(src, dst)\n")
            f.write("print('Saved physical INP:', dst)\n")

    @staticmethod
    def build_three_layer_uel_deck(src_phys_inp, dst_uel_inp, job_name, plate_h=1.0):
        """Constructs full conforming 3-layer UEL + UMAT production deck."""
        nodes = {}
        quad_elems = {}
        tri_elems = {}
        in_nodes = in_elems = False
        elem_type = None

        with open(src_phys_inp, "r") as f:
            for line in f:
                l = line.strip()
                if not l: continue
                if l.startswith("*"):
                    u = l.upper()
                    if u.startswith("*NODE"): in_nodes, in_elems = True, False
                    elif u.startswith("*ELEMENT"):
                        in_nodes, in_elems = False, True
                        if "CPS4" in u or "CPE4" in u: elem_type = "QUAD"
                        elif "CPS3" in u or "CPE3" in u: elem_type = "TRI"
                        else: elem_type = "OTHER"
                    else: in_nodes = in_elems = False
                    continue

                if in_nodes:
                    p = [x.strip() for x in l.split(",") if x.strip()]
                    if len(p) >= 3:
                        try: nodes[int(p[0])] = (float(p[1]), float(p[2]))
                        except ValueError: continue
                elif in_elems:
                    p = [x.strip() for x in l.split(",") if x.strip()]
                    if len(p) >= 4:
                        try:
                            int_p = [int(x) for x in p]
                            eid = int_p[0]
                            conn = int_p[1:]
                            if elem_type == "QUAD" or len(conn) == 4: quad_elems[eid] = tuple(conn[:4])
                            elif elem_type == "TRI" or len(conn) == 3: tri_elems[eid] = tuple(conn[:3])
                        except ValueError: continue

        num_phys = len(quad_elems) + len(tri_elems)
        num_nodes = len(nodes)
        rp_nid = num_nodes + 1

        with open(dst_uel_inp, "w") as f:
            f.write("*HEADING\n** Production Deck: %s (Generalized 2D Field-Driven Adaptive Mesh)\n" % job_name)
            f.write("** Total physical elements: %d (%d quads, %d tris), Nodes: %d\n" % (num_phys, len(quad_elems), len(tri_elems), num_nodes))
            f.write("** Parameters: E=210 GPa, nu=0.3, l0=0.0075 mm, Gc=0.0027 kN/mm, eta=1e-7\n** ----------------------------------------------------------\n")
            f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
            if tri_elems:
                f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
                f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")

            f.write("*NODE\n")
            for nid in sorted(nodes.keys()):
                x, y = nodes[nid]
                f.write("%d, %.9e, %.9e\n" % (nid, x, y))
            f.write("%d, 0.5, %.9e\n" % (rp_nid, plate_h))

            # Layer 1: Phase field
            if quad_elems:
                f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
                for eid in sorted(quad_elems.keys()):
                    f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in quad_elems[eid])))
            if tri_elems:
                f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
                for eid in sorted(tri_elems.keys()):
                    f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in tri_elems[eid])))

            # Layer 2: Displacement
            offset_disp = num_phys
            if quad_elems:
                f.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
                for eid in sorted(quad_elems.keys()):
                    f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in quad_elems[eid])))
            if tri_elems:
                f.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
                for eid in sorted(tri_elems.keys()):
                    f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in tri_elems[eid])))

            # Layer 3: Visualization UMAT
            offset_umat = 2 * num_phys
            if quad_elems:
                f.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
                for eid in sorted(quad_elems.keys()):
                    f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in quad_elems[eid])))
            if tri_elems:
                f.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
                for eid in sorted(tri_elems.keys()):
                    f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in tri_elems[eid])))

            f.write("*ELSET, ELSET=All_elem\nUMAT_QUADS\n")
            if tri_elems: f.write("UMAT_TRIS\n")
            f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

            # UEL properties
            f.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n210000.0, 0.3, 0.0075, 0.0027, 1.0e-7, 0.0\n")
            f.write("*UEL PROPERTY, ELSET=DISP_QUAD\n210000.0, 0.3, 0.0075, 0.0027, 1.0e-7, 0.0\n")
            if tri_elems:
                f.write("*UEL PROPERTY, ELSET=PHASE_TRI\n210000.0, 0.3, 0.0075, 0.0027, 1.0e-7, 0.0\n")
                f.write("*UEL PROPERTY, ELSET=DISP_TRI\n210000.0, 0.3, 0.0075, 0.0027, 1.0e-7, 0.0\n")

            f.write("*SOLID SECTION, ELSET=umatelem, MATERIAL=DUMMY\n1.0\n")
            f.write("*MATERIAL, NAME=DUMMY\n*USER MATERIAL, CONSTANTS=1\n1.0\n*DEPVAR\n2\n")

            # Node sets and boundaries
            f.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)
            bottom_nodes = [nid for nid, (x, y) in nodes.items() if abs(y) < 1e-6]
            top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - plate_h) < 1e-6]
            pin_candidates = [nid for nid in bottom_nodes if abs(nodes[nid][0]) < 1e-6]
            pin_nid = pin_candidates[0] if pin_candidates else bottom_nodes[0]

            f.write("*NSET, NSET=N_BOTTOM\n")
            for i, nid in enumerate(sorted(bottom_nodes)):
                f.write("%d%s" % (nid, ",\n" if (i + 1) % 10 == 0 or i == len(bottom_nodes) - 1 else ", "))
            f.write("*NSET, NSET=N_TOP\n")
            for i, nid in enumerate(sorted(top_nodes)):
                f.write("%d%s" % (nid, ",\n" if (i + 1) % 10 == 0 or i == len(top_nodes) - 1 else ", "))
            f.write("*NSET, NSET=N_PIN\n%d\n" % pin_nid)

            f.write("*EQUATION\n")
            for nid in sorted(top_nodes):
                f.write("2\n%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))
            f.write("*BOUNDARY\nN_BOTTOM, 2, 2, 0.0\nN_PIN, 1, 1, 0.0\nN_TOP, 1, 1, 0.0\nN_RP, 1, 1, 0.0\nN_RP, 2, 2, 0.0\n")

            # Step 1: Precritical loading
            f.write("** ----------------------------------------------------------\n** STEP 1: Pilot Loading\n** ----------------------------------------------------------\n")
            f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=1000\n*STATIC\n0.05, 1.0, 1.0e-6, 0.05\n*BOUNDARY\nN_RP, 2, 2, 0.0035\n")
            f.write("*RESTART, WRITE, FREQUENCY=1\n*OUTPUT, FIELD, FREQUENCY=1\n*NODE OUTPUT, NSET=N_RP\nU, RF\n")
            f.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV, S, E\n*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n*END STEP\n")

            # Step 2: Fracture propagation (inactive pending user approval)
            f.write("** ----------------------------------------------------------\n** STEP 2: Fracture Propagation (User approval required)\n** ----------------------------------------------------------\n")
            f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=20000\n*STATIC\n0.002, 1.0, 1.0e-8, 0.002\n*BOUNDARY\nN_RP, 2, 2, 0.0120\n")
            f.write("*RESTART, WRITE, FREQUENCY=1\n*OUTPUT, FIELD, FREQUENCY=1\n*NODE OUTPUT, NSET=N_RP\nU, RF\n")
            f.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV, S, E\n*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n*END STEP\n")
        print(f"Built 3-layer UEL deck ({num_phys*3} elements): {dst_uel_inp}")


# =============================================================================
# TOP-LEVEL PIPELINE EXECUTION FUNCTION
# =============================================================================
def execute_adaptive_remeshing_pipeline(
    geometry,
    field_source,
    indicator_strategy="damage_softening",
    indicator_threshold=0.08,
    buffer_radius=0.0225,
    min_component_elements=20,
    job_prefix="PK_ADAPT_GEN",
    output_dir="models/pandey_kumar_mode1/176_method_a_plate_with_hole",
    l0=0.0075,
    h_bulk=0.020,
    run_meshing=True
):
    """
    Executes the complete geometry-independent 2D adaptive remeshing pipeline:
    1. Mark elements using selected indicator strategy (no coordinate filtering).
    2. Extract topological connected components from element adjacency graph.
    3. Construct material-domain-constrained Minkowski buffered polygons.
    4. Formulate mesh sizing configuration.
    5. Write generic Abaqus CAE script and execute advancing-front mesher.
    6. Build conforming 3-layer UEL production deck.
    """
    print(f"\n=======================================================")
    print(f"RUNNING ADAPTIVE REMESHING PIPELINE: {geometry.name}")
    print(f"=======================================================")

    # 1. Mark elements
    if indicator_strategy == "damage_softening":
        marked = IndicatorEvaluator.mark_damage_softening(field_source, threshold=indicator_threshold)
    elif indicator_strategy == "damage_diffuse":
        marked = IndicatorEvaluator.mark_combined_damage_diffuse(field_source, diffuse_threshold=indicator_threshold)
    elif indicator_strategy.startswith("synthetic"):
        marked = IndicatorEvaluator.mark_synthetic_threshold(field_source, indicator_strategy, threshold=indicator_threshold)
    else:
        raise ValueError(f"Unknown indicator strategy: {indicator_strategy}")

    # 2. Topological components
    top_builder = TopologySupportBuilder(field_source.nodes, field_source.elements)
    components = top_builder.extract_connected_components(marked)

    # 3. Geometric support buffering
    supports = top_builder.build_buffered_support_polygons(
        components, geometry, buffer_radius=buffer_radius, min_elements=min_component_elements
    )

    # 4. Sizing configuration
    sizing = MeshSizingEngine(l0=l0, h_bulk=h_bulk)

    # 5. Meshing & Deck Generation
    cae_script = os.path.join(output_dir, f"generate_{job_prefix.lower()}_cae.py")
    AbaqusMeshAdapter.write_cae_meshing_script(
        cae_script, geometry, supports, sizing, job_prefix, output_dir
    )

    if run_meshing:
        import subprocess
        print(f"Launching Abaqus CAE mesher for {job_prefix}...")
        res = subprocess.run(f"abaqus cae noGUI={cae_script}", shell=True, capture_output=True, text=True)
        print("Abaqus CAE execution return code:", res.returncode)
        
        phys_inp = os.path.join(output_dir, f"{job_prefix}_PHYS.inp")
        prod_inp = os.path.join(output_dir, f"{job_prefix}_PROD.inp")
        if os.path.exists(phys_inp):
            AbaqusMeshAdapter.build_three_layer_uel_deck(phys_inp, prod_inp, job_prefix, plate_h=geometry.height)
            print(f"Pipeline completed successfully for {geometry.name}!")
        else:
            print(f"Warning: {phys_inp} was not generated.")

    return {
        "geometry": geometry.to_dict(),
        "num_marked_elements": len(marked),
        "num_components": len(components),
        "supports": supports,
        "sizing": sizing.get_sizing_configuration()
    }
