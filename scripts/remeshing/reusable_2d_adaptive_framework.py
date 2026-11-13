# -*- coding: utf-8 -*-
"""
scripts/remeshing/reusable_2d_adaptive_framework.py
===================================================
Task: F1665 - REUSABLE 2D MODE-I METHOD-A FRAMEWORK AND HOLE-PILOT READINESS
Mandated by: ChatGPT independent review (HND-e7c597c4a8ee)

Unified, modular, geometry-independent 2D adaptive remeshing framework for
Mode-I phase-field fracture in Abaqus 2023.

Architecture:
1. AdaptiveConfig: Configuration loader & validator for benchmark definitions.
2. GeometryAdapter (Base): Abstract interface for geometry creation and boundary identification.
   - StraightNotchMode1Adapter: Conventional 1x1 mm edge-cracked Mode-I plate.
   - OffAxisHoleMode1Adapter: 1x1 mm plate with horizontal edge notch and off-axis circular hole.
3. MeshQualityAuditEngine: Standalone finite-element verification (signed isoparametric Jacobians,
   corner angles, aspect ratios, and spatially resolved h/l0 resolution telemetry).
4. ProductionDeckBuilder: Deterministic converter from 2D physical mesh (quads + tris) into
   authoritative 3-layer UEL + companion UMAT input decks matching f42_mixed_uel.for.
"""

from __future__ import print_function

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


# ==============================================================================
# 1. CONFIGURATION SYSTEM
# ==============================================================================

class AdaptiveConfig(object):
    """Encapsulates and validates all parameters for a 2D adaptive remeshing benchmark."""

    def __init__(self, config_data):
        self.raw = config_data
        self.benchmark_name = config_data.get("benchmark_name", "Unknown Benchmark")
        self.geometry_type = config_data.get("geometry_type", "UNKNOWN")

        geom = config_data.get("geometry", {})
        self.plate_w = float(geom.get("plate_width", 1.0))
        self.plate_h = float(geom.get("plate_height", 1.0))
        self.notch = geom.get("notch", None)
        if isinstance(self.notch, dict):
            self.notch_a = float(self.notch.get("length", 0.5))
            self.notch_y = float(self.notch.get("y", 0.5))
            self.notch_w = float(self.notch.get("slit_opening", 0.001))
        elif "notch_length" in geom and geom["notch_length"] is not None:
            self.notch_a = float(geom.get("notch_length", 0.5))
            self.notch_y = float(geom.get("notch_y", 0.5))
            self.notch_w = float(geom.get("notch_slit_opening", 0.001))
        else:
            self.notch_a = None
            self.notch_y = None
            self.notch_w = None

        self.voids = geom.get("voids", [])
        self.has_hole = bool(geom.get("has_hole", False)) or len(self.voids) > 0
        if "hole_center_x" in geom and geom["hole_center_x"] is not None:
            self.hole_x = float(geom["hole_center_x"])
            self.hole_y = float(geom["hole_center_y"])
            self.hole_r = float(geom["hole_radius"])
        elif len(self.voids) == 1:
            v0 = self.voids[0]
            self.hole_x = float(v0.get("x", 0.0))
            self.hole_y = float(v0.get("y", 0.0))
            self.hole_r = float(v0.get("r", 0.0))
        else:
            self.hole_x = None
            self.hole_y = None
            self.hole_r = None

        mat = config_data.get("material", {})
        self.E = float(mat.get("youngs_modulus_mpa", mat.get("E", 210000.0)))
        if self.E < 1000.0:  # If specified in GPa (e.g. 210.0), convert to MPa
            self.E = self.E * 1000.0
        self.nu = float(mat.get("poisson_ratio", mat.get("nu", 0.3)))
        self.l0 = float(mat.get("length_scale_l0_mm", mat.get("l0", 0.0075)))
        self.Gc = float(mat.get("gc_kn_per_mm", mat.get("Gc", 0.0027)))
        self.k_residual = float(mat.get("residual_stiffness_k", mat.get("k_residual", 1e-7)))

        load = config_data.get("loading", {})
        self.loading_type = str(load.get("loading_type", "EDGE_PULL"))
        self.bottom_u2 = float(load.get("bottom_u2", 0.0))
        self.pin_bottom_left_u1 = float(load.get("pin_bottom_left_u1", 0.0))
        self.step1_u2 = float(load.get("step1_precritical_u2", load.get("step1_disp", 0.005)))
        self.step2_u2 = float(load.get("step2_fracture_u2", load.get("step2_disp", 0.012)))
        self.kinematics = str(load.get("kinematics", "LINEAR"))
        self.lower_hole_center = tuple(load.get("lower_hole_center", [20.0, 20.0]))
        self.lower_hole_radius = float(load.get("lower_hole_radius", 5.0))
        self.upper_hole_center = tuple(load.get("upper_hole_center", [20.0, 100.0]))
        self.upper_hole_radius = float(load.get("upper_hole_radius", 5.0))

        rr = config_data.get("remeshing_rule", config_data.get("remeshing", {}))
        self.error_target = float(rr.get("error_target", rr.get("error_target_pct", 5.0)))
        self.min_h = float(rr.get("min_element_size_mm", rr.get("h_min", 0.0015)))
        self.max_h = float(rr.get("max_element_size_mm", rr.get("h_max", 0.020)))
        self.refinement_factor = int(rr.get("refinement_factor", 10))
        self.coarsening_factor = str(rr.get("coarsening_factor", "NOT_ALLOWED" if not rr.get("coarsening_allowed", False) else "DEFAULT_LIMIT"))
        self.sizing_method = str(rr.get("sizing_method", "UNIFORM_ERROR"))
        self.variable = str(rr.get("variable", rr.get("indicator", "MISESERI")))

        opts = config_data.get("deck_options", config_data.get("paths", {}))
        self.uel_subroutine = opts.get("uel_subroutine", opts.get("uel_source", "f42_mixed_uel.for"))
        self.expected_uel_sha256 = opts.get("expected_uel_sha256", opts.get("frozen_uel_sha256", FROZEN_UEL_SHA256))
        self.output_dir = opts.get("output_directory", opts.get("output_dir", "."))

        self._validate()

    def _validate(self):
        if self.plate_w <= 0.0 or self.plate_h <= 0.0:
            raise ValueError("Plate dimensions must be positive.")
        if self.notch_a is not None:
            if self.notch_a <= 0.0 or self.notch_a >= self.plate_w:
                raise ValueError("Notch length must be within (0, plate_width).")
        if self.has_hole:
            if len(self.voids) > 1:
                pass
            elif self.hole_x is None or self.hole_y is None or self.hole_r is None:
                raise ValueError("Hole coordinates and radius must be specified when has_hole=True.")
            elif self.hole_r <= 0.0:
                raise ValueError("Hole radius must be positive.")
        if self.error_target <= 0.1:
            raise ValueError("error_target %.2f is ambiguous; must be percentage points (e.g. 5.0)." % self.error_target)
        if self.min_h >= self.max_h:
            raise ValueError("min_element_size must be smaller than max_element_size.")

    @classmethod
    def from_json(cls, json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
        return cls(data)


# ==============================================================================
# 2. GEOMETRY ADAPTERS
# ==============================================================================

class GeometryAdapter(object):
    """Abstract base adapter for 2D fracture benchmark geometries."""

    def __init__(self, config):
        self.config = config

    def get_outer_polygon_points(self):
        """Returns ordered list of (x, y) vertices defining the outer notched boundary."""
        raise NotImplementedError

    def get_hole_definitions(self):
        """Returns list of (center_x, center_y, radius) tuples for internal voids."""
        raise NotImplementedError

    def is_inside_domain(self, x, y, tol=1e-6):
        """Analytical containment check."""
        raise NotImplementedError

    def classify_region(self, x, y, authentic_damage=None):
        """Classifies point (x, y) into physical fracture zones."""
        raise NotImplementedError


class StraightNotchMode1Adapter(GeometryAdapter):
    """Adapter for conventional 1x1 mm edge-cracked Mode-I benchmark."""

    def get_outer_polygon_points(self):
        w = self.config.notch_w
        return [
            (0.0, 0.0),
            (self.config.plate_w, 0.0),
            (self.config.plate_w, self.config.plate_h),
            (0.0, self.config.plate_h),
            (0.0, self.config.notch_y + w),
            (self.config.notch_a, self.config.notch_y + w),
            (self.config.notch_a, self.config.notch_y - w),
            (0.0, self.config.notch_y - w)
        ]

    def get_hole_definitions(self):
        return []

    def is_inside_domain(self, x, y, tol=1e-6):
        if x < -tol or x > self.config.plate_w + tol:
            return False
        if y < -tol or y > self.config.plate_h + tol:
            return False
        # In slit notch opening
        if x <= self.config.notch_a + tol and abs(y - self.config.notch_y) < self.config.notch_w - tol:
            return False
        return True

    def classify_region(self, x, y, authentic_damage=None):
        if authentic_damage is not None:
            if authentic_damage >= 0.80:
                return "CRACK_CORE"
            elif authentic_damage >= 0.20:
                return "ACTIVE_SOFTENING"
            elif authentic_damage >= 0.05:
                return "TRANSITION_ZONE"
            else:
                return "FAR_FIELD"
        # Geometric proxy if damage unavailable
        dx = x - self.config.notch_a
        dy = abs(y - self.config.notch_y)
        dist_tip = math.hypot(dx, dy)
        if dist_tip <= 3.0 * self.config.l0:
            return "CRACK_CORE"
        elif x >= self.config.notch_a and dy <= 3.0 * self.config.l0:
            return "PROPAGATION_CORRIDOR"
        return "FAR_FIELD"


class OffAxisHoleMode1Adapter(GeometryAdapter):
    """Adapter for 1x1 mm Mode-I plate with off-axis circular hole."""

    def get_outer_polygon_points(self):
        w = self.config.notch_w
        return [
            (0.0, 0.0),
            (self.config.plate_w, 0.0),
            (self.config.plate_w, self.config.plate_h),
            (0.0, self.config.plate_h),
            (0.0, self.config.notch_y + w),
            (self.config.notch_a, self.config.notch_y + w),
            (self.config.notch_a, self.config.notch_y - w),
            (0.0, self.config.notch_y - w)
        ]

    def get_hole_definitions(self):
        return [(self.config.hole_x, self.config.hole_y, self.config.hole_r)]

    def is_inside_domain(self, x, y, tol=1e-6):
        if x < -tol or x > self.config.plate_w + tol:
            return False
        if y < -tol or y > self.config.plate_h + tol:
            return False
        # In slit opening
        if x <= self.config.notch_a + tol and abs(y - self.config.notch_y) < self.config.notch_w - tol:
            return False
        # Inside circular hole
        dist_hole = math.hypot(x - self.config.hole_x, y - self.config.hole_y)
        if dist_hole < self.config.hole_r - tol:
            return False
        return True

    def classify_region(self, x, y, authentic_damage=None):
        if authentic_damage is not None:
            if authentic_damage >= 0.80:
                return "CRACK_CORE"
            elif authentic_damage >= 0.20:
                return "ACTIVE_SOFTENING"
            elif authentic_damage >= 0.05:
                return "TRANSITION_ZONE"
            else:
                return "FAR_FIELD"
        # Bounding box proxies for unmapped geometry
        if 0.50 <= x <= 0.65 and 0.50 <= y <= 0.65:
            return "NOTCH_TO_HOLE_LIGAMENT"
        elif 0.70 <= x <= 0.85 and 0.55 <= y <= 0.72:
            return "OPPOSITE_HOLE_FLANK"
        return "FAR_FIELD"


class MultiHolePlateAdapter(GeometryAdapter):
    """Adapter for perforated plates with multiple internal and/or edge voids."""

    def __init__(self, config):
        super(MultiHolePlateAdapter, self).__init__(config)
        self.voids = getattr(config, "voids", [])
        self.internal_holes = []
        self.edge_cutouts = []
        for v in self.voids:
            v_type = v.get("type", "circle")
            vx = float(v.get("x", 0.0))
            vy = float(v.get("y", 0.0))
            vr = float(v.get("r", 0.0))
            v_name = v.get("name", "")
            if v_type in ("circle", "hole"):
                self.internal_holes.append((vx, vy, vr, v_name))
            else:
                self.edge_cutouts.append((vx, vy, vr, v_type, v_name))

    def get_outer_polygon_points(self):
        return [
            (0.0, 0.0),
            (self.config.plate_w, 0.0),
            (self.config.plate_w, self.config.plate_h),
            (0.0, self.config.plate_h)
        ]

    def get_hole_definitions(self):
        return [(h[0], h[1], h[2]) for h in self.internal_holes]

    def is_inside_domain(self, x, y, tol=1e-6):
        if x < -tol or x > self.config.plate_w + tol:
            return False
        if y < -tol or y > self.config.plate_h + tol:
            return False
        for hx, hy, hr in self.get_hole_definitions():
            if math.hypot(x - hx, y - hy) < hr - tol:
                return False
        for cx, cy, cr, ctype, _ in self.edge_cutouts:
            if math.hypot(x - cx, y - cy) < cr - tol:
                return False
        return True

    def classify_region(self, x, y, authentic_damage=None):
        if authentic_damage is not None:
            if authentic_damage >= 0.80:
                return "CRACK_CORE"
            elif authentic_damage >= 0.20:
                return "ACTIVE_SOFTENING"
            elif authentic_damage >= 0.05:
                return "TRANSITION_ZONE"
            else:
                return "FAR_FIELD"

        # Check if 7-hole geometry
        if len(self.internal_holes) == 7:
            # Active upper fracture corridor segments connecting h1 -> h4 -> h2 -> h5 -> h3:
            segments = [
                ((0.15, 0.40), (0.30, 0.60)),
                ((0.30, 0.60), (0.50, 0.55)),
                ((0.50, 0.55), (0.70, 0.60)),
                ((0.70, 0.60), (0.85, 0.50))
            ]
            min_dist_corridor = 1e9
            for (x1, y1), (x2, y2) in segments:
                dx, dy = x2 - x1, y2 - y1
                l2 = dx*dx + dy*dy
                t = max(0.0, min(1.0, ((x - x1)*dx + (y - y1)*dy) / l2)) if l2 > 0 else 0.0
                d = math.hypot(x - (x1 + t*dx), y - (y1 + t*dy))
                if d < min_dist_corridor:
                    min_dist_corridor = d

            if min_dist_corridor <= 3.0 * self.config.l0:
                return "UPPER_CRACK_CORRIDOR"

            # Check proximity to lower shielded holes h6 (0.40, 0.35, r=0.05) and h7 (0.65, 0.35, r=0.05)
            d6 = abs(math.hypot(x - 0.40, y - 0.35) - 0.05)
            d7 = abs(math.hypot(x - 0.65, y - 0.35) - 0.05)
            if min(d6, d7) <= 3.0 * self.config.l0:
                return "LOWER_SHIELDED_HOLES"

        return "FAR_FIELD"


class NotchedPlateWithPinHolesAdapter(GeometryAdapter):
    """Adapter for Pandey & Kumar (2025) Section 4.3:
    65 x 120 mm notched plate with central hole (36.5, 51.0, R=10) and
    two pin loading/support holes at (20, 20, R=5) and (20, 100, R=5).
    """

    def __init__(self, config):
        super(NotchedPlateWithPinHolesAdapter, self).__init__(config)
        self.notch_a = float(config.notch_a if config.notch_a is not None else 10.0)
        self.notch_y = float(config.notch_y if config.notch_y is not None else 70.0)
        self.notch_w = float(config.notch_w if config.notch_w is not None else 0.2)
        self.plate_w = float(config.plate_w)
        self.plate_h = float(config.plate_h)
        self.central_hole = (36.5, 51.0, 10.0)
        self.lower_pin = (20.0, 20.0, 5.0)
        self.upper_pin = (20.0, 100.0, 5.0)

    def get_outer_polygon_points(self):
        w = self.notch_w
        return [
            (0.0, 0.0),
            (self.plate_w, 0.0),
            (self.plate_w, self.plate_h),
            (0.0, self.plate_h),
            (0.0, self.notch_y + w),
            (self.notch_a, self.notch_y + w),
            (self.notch_a, self.notch_y - w),
            (0.0, self.notch_y - w)
        ]

    def get_hole_definitions(self):
        return [
            self.central_hole,
            self.lower_pin,
            self.upper_pin
        ]

    def is_inside_domain(self, x, y, tol=1e-5):
        if x < -tol or x > self.plate_w + tol:
            return False
        if y < -tol or y > self.plate_h + tol:
            return False
        # Inside horizontal notch opening
        if x <= self.notch_a + tol and abs(y - self.notch_y) < self.notch_w - tol:
            return False
        # Inside holes
        for (hx, hy, hr) in self.get_hole_definitions():
            if math.hypot(x - hx, y - hy) < hr - tol:
                return False
        return True

    def classify_region(self, x, y, authentic_damage=None):
        if authentic_damage is not None:
            if authentic_damage >= 0.80:
                return "CRACK_CORE"
            elif authentic_damage >= 0.20:
                return "ACTIVE_SOFTENING"
            elif authentic_damage >= 0.05:
                return "TRANSITION_ZONE"
            else:
                return "FAR_FIELD"

        # Check primary ligament: corridor connecting notch tip (10, 70) to central hole perimeter ~ (27, 53)
        x1, y1 = 10.0, 70.0
        x2, y2 = 27.0, 53.0
        dx, dy = x2 - x1, y2 - y1
        l2 = dx*dx + dy*dy
        t = max(0.0, min(1.0, ((x - x1)*dx + (y - y1)*dy) / l2)) if l2 > 0 else 0.0
        d_prim = math.hypot(x - (x1 + t*dx), y - (y1 + t*dy))
        if d_prim <= 3.0 * self.config.l0:
            return "PRIMARY_LIGAMENT"

        # Check secondary crack path: right flank of central hole (46.5, 51.0) towards right edge (65.0, 51.0)
        if 46.5 <= x <= 65.0 and abs(y - 51.0) <= 3.0 * self.config.l0:
            return "SECONDARY_LIGAMENT"

        # Check central hole boundary
        d_cent = abs(math.hypot(x - 36.5, y - 51.0) - 10.0)
        if d_cent <= 2.0 * self.config.l0:
            return "CENTRAL_HOLE_BOUNDARY"

        # Check pin hole boundaries
        d_low = abs(math.hypot(x - 20.0, y - 20.0) - 5.0)
        d_upp = abs(math.hypot(x - 20.0, y - 100.0) - 5.0)
        if min(d_low, d_upp) <= 2.0 * self.config.l0:
            return "PIN_HOLE_ZONES"

        return "FAR_FIELD"


def get_geometry_adapter(config):
    """Factory to instantiate the appropriate geometry adapter."""
    gtype = getattr(config, "geometry_type", "").upper()
    if gtype in ("NOTCHED_PLATE_WITH_PIN_HOLES", "SEC43_PLATE", "NOTCHED_HOLE_PLATE"):
        return NotchedPlateWithPinHolesAdapter(config)
    elif len(getattr(config, "voids", [])) > 1 or gtype in ("MULTI_HOLE_PLATE", "SEVEN_HOLE_PLATE", "FIVE_HOLE_PLATE"):
        return MultiHolePlateAdapter(config)
    elif config.has_hole:
        return OffAxisHoleMode1Adapter(config)
    else:
        return StraightNotchMode1Adapter(config)


# ==============================================================================
# 3. MESH QUALITY & RESOLUTION AUDIT ENGINE
# ==============================================================================

class MeshQualityAuditEngine(object):
    """Evaluates signed isoparametric Jacobians, aspect ratios, angles, and h/l0."""

    @staticmethod
    def parse_physical_inp(inp_path):
        nodes = {}
        quad_elems = {}
        tri_elems = {}

        in_nodes = False
        in_elements = False
        elem_type = None

        with open(inp_path, "r") as f:
            for line in f:
                l = line.strip()
                if not l or l.startswith("**"):
                    continue
                if l.startswith("*"):
                    in_nodes = False
                    in_elements = False
                    upline = l.upper()
                    if upline.startswith("*NODE"):
                        in_nodes = True
                    elif upline.startswith("*ELEMENT"):
                        in_elements = True
                        if "CPE4" in upline or "CPS4" in upline:
                            elem_type = "QUAD"
                        elif "CPE3" in upline or "CPS3" in upline:
                            elem_type = "TRI"
                        else:
                            elem_type = "OTHER"
                    continue

                parts = [p.strip() for p in l.split(",") if p.strip()]
                if in_nodes and len(parts) >= 3:
                    try:
                        nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass
                elif in_elements and len(parts) >= 4:
                    try:
                        int_parts = [int(p) for p in parts]
                        eid = int_parts[0]
                        conn = int_parts[1:]
                        if elem_type == "QUAD" or len(conn) == 4:
                            quad_elems[eid] = tuple(conn[:4])
                        else:
                            tri_elems[eid] = tuple(conn[:3])
                    except ValueError:
                        pass

        return nodes, quad_elems, tri_elems

    @classmethod
    def evaluate_mesh(cls, inp_path, l0_mm=0.0075, authentic_damage_lookup=None, adapter=None):
        nodes, quad_elems, tri_elems = cls.parse_physical_inp(inp_path)
        total_elems = len(quad_elems) + len(tri_elems)
        total_nodes = len(nodes)

        edge_lengths_um = []
        edge_lengths_mm = []
        area_values_mm2 = []
        h_area_mm = []
        h_area_um = []
        jacobians = []
        non_positive_jacobians = 0
        distorted_elements = 0
        aspect_ratios = []
        corner_angles_deg = []

        crack_core_edges = []
        softening_edges = []
        far_field_edges = []

        process_zone_h_area_mm = []
        far_field_h_area_mm = []
        process_zone_h_edge_mm = []
        far_field_h_edge_mm = []

        # 1. Quads
        gp_xi = [-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)]
        for eid, conn in quad_elems.items():
            pts = [nodes[nid] for nid in conn]
            edges = [
                math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]),
                math.hypot(pts[2][0] - pts[1][0], pts[2][1] - pts[1][1]),
                math.hypot(pts[3][0] - pts[2][0], pts[3][1] - pts[2][1]),
                math.hypot(pts[0][0] - pts[3][0], pts[0][1] - pts[3][1]),
            ]
            h_max_m = max(edges)
            h_max_um = h_max_m * 1000.0
            edge_lengths_mm.append(h_max_m)
            edge_lengths_um.append(h_max_um)

            # Area via Shoelace
            area = 0.5 * abs(
                (pts[0][0]*pts[1][1] - pts[1][0]*pts[0][1]) +
                (pts[1][0]*pts[2][1] - pts[2][0]*pts[1][1]) +
                (pts[2][0]*pts[3][1] - pts[3][0]*pts[2][1]) +
                (pts[3][0]*pts[0][1] - pts[0][0]*pts[3][1])
            )
            area_values_mm2.append(area)
            ha = math.sqrt(max(area, 1e-18))
            h_area_mm.append(ha)
            h_area_um.append(ha * 1000.0)

            # Aspect ratio
            min_e = max(min(edges), 1e-12)
            aspect_ratios.append(max(edges) / min_e)

            # Signed 2x2 Gauss Jacobians
            elem_det_j = []
            for xi in gp_xi:
                for eta in gp_xi:
                    dN_dxi = [
                        -0.25 * (1.0 - eta),
                         0.25 * (1.0 - eta),
                         0.25 * (1.0 + eta),
                        -0.25 * (1.0 + eta)
                    ]
                    dN_deta = [
                        -0.25 * (1.0 - xi),
                        -0.25 * (1.0 + xi),
                         0.25 * (1.0 + xi),
                         0.25 * (1.0 - xi)
                    ]
                    dx_dxi = sum(dN_dxi[i] * pts[i][0] for i in range(4))
                    dy_dxi = sum(dN_dxi[i] * pts[i][1] for i in range(4))
                    dx_deta = sum(dN_deta[i] * pts[i][0] for i in range(4))
                    dy_deta = sum(dN_deta[i] * pts[i][1] for i in range(4))
                    det_j = dx_dxi * dy_deta - dy_dxi * dx_deta
                    elem_det_j.append(det_j)
            min_det = min(elem_det_j)
            jacobians.append(min_det)
            if min_det <= 0.0:
                non_positive_jacobians += 1

            # Corner angles
            for i in range(4):
                p_prev = pts[(i - 1) % 4]
                p_curr = pts[i]
                p_next = pts[(i + 1) % 4]
                v1 = (p_prev[0] - p_curr[0], p_prev[1] - p_curr[1])
                v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
                dot = v1[0] * v2[0] + v1[1] * v2[1]
                m1 = math.hypot(v1[0], v1[1])
                m2 = math.hypot(v2[0], v2[1])
                cos_theta = max(min(dot / max(m1 * m2, 1e-12), 1.0), -1.0)
                angle_deg = math.degrees(math.acos(cos_theta))
                corner_angles_deg.append(angle_deg)
                if angle_deg < 15.0 or angle_deg > 165.0:
                    distorted_elements += 1

            # Regional damage classification
            cx = sum(p[0] for p in pts) / 4.0
            cy = sum(p[1] for p in pts) / 4.0
            if authentic_damage_lookup:
                d = authentic_damage_lookup.get(eid, 0.0)
                if d >= 0.80:
                    crack_core_edges.append(h_max_um)
                elif d >= 0.20:
                    softening_edges.append(h_max_um)
                else:
                    far_field_edges.append(h_max_um)

            if adapter is not None:
                reg = adapter.classify_region(cx, cy, authentic_damage=authentic_damage_lookup.get(eid) if authentic_damage_lookup else None)
                if reg in ("FAR_FIELD", "LOWER_SHIELDED_HOLES", "PIN_HOLE_ZONES"):
                    far_field_h_area_mm.append(ha)
                    far_field_h_edge_mm.append(h_max_m)
                else:
                    process_zone_h_area_mm.append(ha)
                    process_zone_h_edge_mm.append(h_max_m)

        # 2. Tris
        for eid, conn in tri_elems.items():
            pts = [nodes[nid] for nid in conn]
            edges = [
                math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]),
                math.hypot(pts[2][0] - pts[1][0], pts[2][1] - pts[1][1]),
                math.hypot(pts[0][0] - pts[2][0], pts[0][1] - pts[2][1])
            ]
            h_max_m = max(edges)
            h_max_um = h_max_m * 1000.0
            edge_lengths_mm.append(h_max_m)
            edge_lengths_um.append(h_max_um)

            # Area
            area = 0.5 * abs(pts[0][0]*(pts[1][1] - pts[2][1]) + pts[1][0]*(pts[2][1] - pts[0][1]) + pts[2][0]*(pts[0][1] - pts[1][1]))
            area_values_mm2.append(area)
            ha = math.sqrt(max(area, 1e-18))
            h_area_mm.append(ha)
            h_area_um.append(ha * 1000.0)

            aspect_ratios.append(max(edges) / max(min(edges), 1e-12))

            # Triangle 2x area = Jacobian
            det_j = (pts[1][0] - pts[0][0]) * (pts[2][1] - pts[0][1]) - (pts[2][0] - pts[0][0]) * (pts[1][1] - pts[0][1])
            jacobians.append(det_j)
            if det_j <= 0.0:
                non_positive_jacobians += 1

            for i in range(3):
                p_prev = pts[(i - 1) % 3]
                p_curr = pts[i]
                p_next = pts[(i + 1) % 3]
                v1 = (p_prev[0] - p_curr[0], p_prev[1] - p_curr[1])
                v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
                dot = v1[0] * v2[0] + v1[1] * v2[1]
                m1 = math.hypot(v1[0], v1[1])
                m2 = math.hypot(v2[0], v2[1])
                cos_theta = max(min(dot / max(m1 * m2, 1e-12), 1.0), -1.0)
                angle_deg = math.degrees(math.acos(cos_theta))
                corner_angles_deg.append(angle_deg)
                if angle_deg < 15.0 or angle_deg > 165.0:
                    distorted_elements += 1

            cx = sum(p[0] for p in pts) / 3.0
            cy = sum(p[1] for p in pts) / 3.0
            if authentic_damage_lookup:
                d = authentic_damage_lookup.get(eid, 0.0)
                if d >= 0.80:
                    crack_core_edges.append(h_max_um)
                elif d >= 0.20:
                    softening_edges.append(h_max_um)
                else:
                    far_field_edges.append(h_max_um)

            if adapter is not None:
                reg = adapter.classify_region(cx, cy, authentic_damage=authentic_damage_lookup.get(eid) if authentic_damage_lookup else None)
                if reg in ("FAR_FIELD", "LOWER_SHIELDED_HOLES", "PIN_HOLE_ZONES"):
                    far_field_h_area_mm.append(ha)
                    far_field_h_edge_mm.append(h_max_m)
                else:
                    process_zone_h_area_mm.append(ha)
                    process_zone_h_edge_mm.append(h_max_m)

        edge_lengths_um.sort()
        edge_lengths_mm.sort()
        h_area_mm.sort()
        h_area_um.sort()

        ret = {
            "total_elements": total_elems,
            "total_nodes": total_nodes,
            "quad_count": len(quad_elems),
            "tri_count": len(tri_elems),
            "quad_percent": (float(len(quad_elems)) / total_elems) * 100.0 if total_elems > 0 else 0.0,
            "non_positive_jacobians": non_positive_jacobians,
            "min_det_j": min(jacobians) if jacobians else 0.0,
            "distorted_elements": distorted_elements,
            "median_aspect_ratio": sorted(aspect_ratios)[len(aspect_ratios) // 2] if aspect_ratios else 0.0,
            "max_aspect_ratio": max(aspect_ratios) if aspect_ratios else 0.0,
            "min_corner_angle_deg": min(corner_angles_deg) if corner_angles_deg else 0.0,
            "max_corner_angle_deg": max(corner_angles_deg) if corner_angles_deg else 0.0,
            # Dual element size metrics: h_edge (maximum edge length)
            "h_edge_min_mm": edge_lengths_mm[0] if edge_lengths_mm else 0.0,
            "h_edge_median_mm": edge_lengths_mm[len(edge_lengths_mm) // 2] if edge_lengths_mm else 0.0,
            "h_edge_mean_mm": sum(edge_lengths_mm) / len(edge_lengths_mm) if edge_lengths_mm else 0.0,
            "h_edge_p95_mm": edge_lengths_mm[int(0.95 * len(edge_lengths_mm))] if edge_lengths_mm else 0.0,
            "h_edge_max_mm": edge_lengths_mm[-1] if edge_lengths_mm else 0.0,
            "h_min_um": edge_lengths_um[0] if edge_lengths_um else 0.0,
            "h_median_um": edge_lengths_um[len(edge_lengths_um) // 2] if edge_lengths_um else 0.0,
            "h_p95_um": edge_lengths_um[int(0.95 * len(edge_lengths_um))] if edge_lengths_um else 0.0,
            "h_max_um": edge_lengths_um[-1] if edge_lengths_um else 0.0,
            # Dual element size metrics: h_area = sqrt(Area)
            "h_area_min_mm": h_area_mm[0] if h_area_mm else 0.0,
            "h_area_median_mm": h_area_mm[len(h_area_mm) // 2] if h_area_mm else 0.0,
            "h_area_mean_mm": sum(h_area_mm) / len(h_area_mm) if h_area_mm else 0.0,
            "h_area_p95_mm": h_area_mm[int(0.95 * len(h_area_mm))] if h_area_mm else 0.0,
            "h_area_max_mm": h_area_mm[-1] if h_area_mm else 0.0,
            "h_area_min_um": h_area_um[0] if h_area_um else 0.0,
            "h_area_median_um": h_area_um[len(h_area_um) // 2] if h_area_um else 0.0,
            "h_area_max_um": h_area_um[-1] if h_area_um else 0.0,
            "elements_hl0_le_1": sum(1 for h in h_area_mm if h <= l0_mm),
            "elements_hl0_le_half": sum(1 for h in h_area_mm if h <= 0.5 * l0_mm),
            "elements_le_1p5um": sum(1 for h in edge_lengths_um if h <= 1.50),
            "elements_le_2p5um": sum(1 for h in edge_lengths_um if h <= 2.50),
            "elements_le_3p75um": sum(1 for h in edge_lengths_um if h <= 3.75),
        }

        if process_zone_h_area_mm:
            ret["process_zone_elements"] = len(process_zone_h_area_mm)
            ret["process_zone_h_area_min_mm"] = min(process_zone_h_area_mm)
            ret["process_zone_h_area_mean_mm"] = sum(process_zone_h_area_mm) / len(process_zone_h_area_mm)
            ret["process_zone_h_area_max_mm"] = max(process_zone_h_area_mm)
            ret["process_zone_hl0_mean"] = ret["process_zone_h_area_mean_mm"] / l0_mm
            ret["process_zone_hl0_min"] = ret["process_zone_h_area_min_mm"] / l0_mm
        if far_field_h_area_mm:
            ret["far_field_elements"] = len(far_field_h_area_mm)
            ret["far_field_h_area_min_mm"] = min(far_field_h_area_mm)
            ret["far_field_h_area_mean_mm"] = sum(far_field_h_area_mm) / len(far_field_h_area_mm)
            ret["far_field_h_area_max_mm"] = max(far_field_h_area_mm)
        if process_zone_h_area_mm and far_field_h_area_mm:
            ret["refinement_ratio_mean"] = ret["far_field_h_area_mean_mm"] / ret["process_zone_h_area_mean_mm"]

        if authentic_damage_lookup is not None:
            ret["crack_core_count"] = len(crack_core_edges)
            ret["crack_core_h_median_um"] = sorted(crack_core_edges)[len(crack_core_edges) // 2] if crack_core_edges else None
            ret["crack_core_le_1p5um"] = sum(1 for h in crack_core_edges if h <= 1.50)

        return ret


# ==============================================================================
# 4. PRODUCTION DECK BUILDER (3-LAYER UEL + UMAT)
# ==============================================================================

class ProductionDeckBuilder(object):
    """Deterministically transforms physical mesh into 3-layer UEL + UMAT input deck."""

    @staticmethod
    def verify_uel_subroutine(subroutine_path, expected_hash=FROZEN_UEL_SHA256):
        if not os.path.exists(subroutine_path):
            raise FileNotFoundError("UEL subroutine not found: %s" % subroutine_path)
        digest = hashlib.sha256()
        with open(subroutine_path, "rb") as f:
            for chunk in iter(lambda: f.read(1048576), b""):
                digest.update(chunk)
        actual_hash = digest.hexdigest().upper()
        if actual_hash != expected_hash.upper():
            raise ValueError("Frozen UEL integrity violation!\nExpected: %s\nActual:   %s" % (
                expected_hash.upper(), actual_hash
            ))
        return True

    @classmethod
    def build_deck(cls, src_phys_inp, dst_uel_inp, job_name, config, step1_only=False):
        cls.verify_uel_subroutine(config.uel_subroutine, config.expected_uel_sha256)

        nodes, quad_elems, tri_elems = MeshQualityAuditEngine.parse_physical_inp(src_phys_inp)
        num_quads = len(quad_elems)
        num_tris = len(tri_elems)
        num_phys_elems = num_quads + num_tris
        num_nodes = len(nodes)

        is_pin_hole = (getattr(config, "loading_type", "EDGE_PULL").upper() == "PIN_HOLE_PULL")
        rp_nid = 999999

        if is_pin_hole:
            low_x, low_y = config.lower_hole_center
            low_r = config.lower_hole_radius
            upp_x, upp_y = config.upper_hole_center
            upp_r = config.upper_hole_radius
            r_tol = 0.05
            lower_nodes = [nid for nid, (x, y) in nodes.items() if abs(math.hypot(x - low_x, y - low_y) - low_r) < r_tol]
            upper_nodes = [nid for nid, (x, y) in nodes.items() if abs(math.hypot(x - upp_x, y - upp_y) - upp_r) < r_tol]
            rp_x, rp_y = upp_x, upp_y
            bottom_nodes, top_nodes, pin_node = [], [], None
        else:
            tol = 1e-4
            bottom_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.0) < tol]
            top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - config.plate_h) < tol]
            pin_candidates = [nid for nid in bottom_nodes if abs(nodes[nid][0] - 0.0) < tol]
            pin_node = min(pin_candidates) if pin_candidates else bottom_nodes[0]
            rp_x, rp_y = 0.5 * config.plate_w, config.plate_h
            lower_nodes, upper_nodes = [], []

        with open(dst_uel_inp, "w") as f:
            f.write("*HEADING\n")
            f.write("** Production Deck: %s (%s)\n" % (job_name, config.benchmark_name))
            f.write("** Physical elements: %d (%d quads, %d tris), Nodes: %d\n" % (
                num_phys_elems, num_quads, num_tris, num_nodes
            ))
            f.write("** Parameters: E=%.1f GPa, nu=%.2f, l0=%.4f mm, Gc=%.4f kN/mm, k=%.1e\n" % (
                config.E / 1000.0, config.nu, config.l0, config.Gc, config.k_residual
            ))
            f.write("** UEL Subroutine: %s (SHA256: %s)\n" % (config.uel_subroutine, config.expected_uel_sha256))
            f.write("** ----------------------------------------------------------\n")

            # UEL Interface definitions matching f42_mixed_uel.for
            f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
            if num_tris > 0:
                f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
                f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")

            # Node coordinates
            f.write("*NODE\n")
            for nid in sorted(nodes.keys()):
                x, y = nodes[nid]
                f.write("%d, %.9e, %.9e\n" % (nid, x, y))
            f.write("%d, %.9e, %.9e\n" % (rp_nid, rp_x, rp_y))

            # Layer 1: Phase field (DOF 3)
            if quad_elems:
                f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
                for eid in sorted(quad_elems.keys()):
                    f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in quad_elems[eid])))
            if tri_elems:
                f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
                for eid in sorted(tri_elems.keys()):
                    f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in tri_elems[eid])))

            # Layer 2: Displacement (DOF 1, 2)
            offset_disp = num_phys_elems
            if quad_elems:
                f.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
                for eid in sorted(quad_elems.keys()):
                    f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in quad_elems[eid])))
            if tri_elems:
                f.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
                for eid in sorted(tri_elems.keys()):
                    f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in tri_elems[eid])))

            # Layer 3: Companion UMAT for visualization (CPE4 / CPE3)
            offset_umat = 2 * num_phys_elems
            if quad_elems:
                f.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
                for eid in sorted(quad_elems.keys()):
                    f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in quad_elems[eid])))
            if tri_elems:
                f.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
                for eid in sorted(tri_elems.keys()):
                    f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in tri_elems[eid])))

            # Element sets
            f.write("*ELSET, ELSET=All_elem\nUMAT_QUADS\n")
            if num_tris > 0:
                f.write("UMAT_TRIS\n")
            f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

            # Node sets
            if is_pin_hole:
                f.write("*NSET, NSET=N_LOWER_HOLE\n")
                for i, nid in enumerate(sorted(lower_nodes)):
                    f.write("%d%s" % (nid, ",\n" if (i + 1) % 16 == 0 and i + 1 < len(lower_nodes) else (", " if i + 1 < len(lower_nodes) else "\n")))
                f.write("*NSET, NSET=N_UPPER_HOLE\n")
                for i, nid in enumerate(sorted(upper_nodes)):
                    f.write("%d%s" % (nid, ",\n" if (i + 1) % 16 == 0 and i + 1 < len(upper_nodes) else (", " if i + 1 < len(upper_nodes) else "\n")))
                f.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)
            else:
                f.write("*NSET, NSET=N_BOTTOM\n")
                for i, nid in enumerate(sorted(bottom_nodes)):
                    f.write("%d%s" % (nid, ",\n" if (i + 1) % 16 == 0 and i + 1 < len(bottom_nodes) else (", " if i + 1 < len(bottom_nodes) else "\n")))
                f.write("*NSET, NSET=N_TOP\n")
                for i, nid in enumerate(sorted(top_nodes)):
                    f.write("%d%s" % (nid, ",\n" if (i + 1) % 16 == 0 and i + 1 < len(top_nodes) else (", " if i + 1 < len(top_nodes) else "\n")))
                f.write("*NSET, NSET=N_PIN\n%d\n" % pin_node)
                f.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)

            # UEL Property cards matching authentic f42_mixed_uel.for ABI:
            # PROPS: (1)=l0, (2)=Gc, (3)=E, (4)=nu, (5)=k_residual, (6)=N_phys
            E_kn = config.E / 1000.0
            num_phys_f = float(num_phys_elems)

            if quad_elems:
                f.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n")
                f.write("%.4f, %.4f, %.1f, %.2f, %.1e, %.1f\n" % (
                    config.l0, config.Gc, E_kn, config.nu, config.k_residual, num_phys_f
                ))
                f.write("*UEL PROPERTY, ELSET=DISP_QUAD\n")
                f.write("%.4f, %.4f, %.1f, %.2f, %.1e, %.1f\n" % (
                    config.l0, config.Gc, E_kn, config.nu, config.k_residual, num_phys_f
                ))
            if tri_elems:
                f.write("*UEL PROPERTY, ELSET=PHASE_TRI\n")
                f.write("%.4f, %.4f, %.1f, %.2f, %.1e, %.1f\n" % (
                    config.l0, config.Gc, E_kn, config.nu, config.k_residual, num_phys_f
                ))
                f.write("*UEL PROPERTY, ELSET=DISP_TRI\n")
                f.write("%.4f, %.4f, %.1f, %.2f, %.1e, %.1f\n" % (
                    config.l0, config.Gc, E_kn, config.nu, config.k_residual, num_phys_f
                ))

            # Companion Material (Visualizer UMAT) matching ABI:
            f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT\n1.0\n")
            f.write("*MATERIAL, NAME=DUMMY_MAT\n")
            sub_name = str(config.uel_subroutine).lower()
            if "f1720" in sub_name or "f1721" in sub_name or "direct_coupling" in sub_name:
                f.write("*USER MATERIAL, CONSTANTS=4\n")
                f.write("%.1f, %.2f, %.1f, 1.0\n" % (E_kn, config.nu, num_phys_f))
            else:
                f.write("*USER MATERIAL, CONSTANTS=3\n")
                f.write("%.1f, %.2f, %.1f\n" % (E_kn, config.nu, num_phys_f))
            f.write("*DEPVAR\n20\n")

            # Rigid tie equations:
            f.write("** ----------------------------------------------------------\n")
            if is_pin_hole:
                f.write("** EQUATIONS (Upper pin hole tied to RP in DOF 2)\n")
                f.write("** ----------------------------------------------------------\n")
                for nid in sorted(upper_nodes):
                    f.write("*EQUATION\n2\n")
                    f.write("%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))
            else:
                f.write("** ----------------------------------------------------------\n")
                f.write("** EQUATIONS (Rigid top tensile pull tied to RP in DOF 2)\n")
                f.write("** ----------------------------------------------------------\n")
                for nid in sorted(top_nodes):
                    f.write("*EQUATION\n2\n")
                    f.write("%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))

            # Step 1: Precritical / Linear loading to step1_u2
            f.write("** ----------------------------------------------------------\n")
            f.write("** STEP 1: Linear Loading to u = %.4f mm\n" % config.step1_u2)
            f.write("** ----------------------------------------------------------\n")
            f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=10000\n")
            f.write("*STATIC\n0.02, 1.0, 1.0e-7, 0.02\n")
            f.write("*BOUNDARY\n")
            if is_pin_hole:
                f.write("N_LOWER_HOLE, 1, 2, 0.0\n")
                f.write("N_UPPER_HOLE, 1, 1, 0.0\n")
            else:
                f.write("N_BOTTOM, 2, 2, 0.0\n")
                f.write("N_PIN, 1, 1, 0.0\n")
                f.write("N_TOP, 1, 1, 0.0\n")
            f.write("N_RP, 2, 2, %.4f\n" % config.step1_u2)
            f.write("*RESTART, WRITE, FREQUENCY=1\n")
            f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
            f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
            f.write("*ELEMENT OUTPUT, ELSET=umatelem\nMISESERI, MISESAVG, S, E, SDV\n")
            f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
            f.write("*END STEP\n")

            if not step1_only:
                f.write("** ----------------------------------------------------------\n")
                f.write("** STEP 2: Fracture Propagation to u = %.4f mm\n" % config.step2_u2)
                f.write("** ----------------------------------------------------------\n")
                f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=20000\n")
                f.write("*STATIC\n0.002, 1.0, 1.0e-8, 0.002\n")
                f.write("*BOUNDARY\n")
                f.write("N_RP, 2, 2, %.4f\n" % config.step2_u2)
                f.write("*RESTART, WRITE, FREQUENCY=1\n")
                f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
                f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
                f.write("*ELEMENT OUTPUT, ELSET=umatelem\nMISESERI, MISESAVG, S, E, SDV\n")
                f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
                f.write("*END STEP\n")

        return {
            "deck_path": dst_uel_inp,
            "total_physical_elements": num_phys_elems,
            "total_layered_elements": 3 * num_phys_elems,
            "total_nodes": num_nodes + 1,
            "uel_hash_verified": True
        }


# ==============================================================================
# 5. CLI INTERFACE
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Reusable 2D Adaptive Framework Engine")
    parser.add_argument("--config", type=str, required=True, help="Path to benchmark JSON configuration")
    parser.add_argument("--audit-mesh", type=str, default=None, help="Audit FE quality of physical INP deck")
    parser.add_argument("--build-deck", type=str, default=None, help="Convert physical INP deck to 3-layer UEL deck")
    parser.add_argument("--output-deck", type=str, default=None, help="Target path for 3-layer UEL deck")
    parser.add_argument("--step1-only", action="store_true", default=False, help="Build Step 1 only")
    args = parser.parse_args()

    cfg = AdaptiveConfig.from_json(args.config)
    adapter = get_geometry_adapter(cfg)
    print("Loaded Benchmark: %s (Type: %s)" % (cfg.benchmark_name, cfg.geometry_type))

    if args.audit_mesh:
        print("\nAuditing mesh: %s" % args.audit_mesh)
        res = MeshQualityAuditEngine.evaluate_mesh(args.audit_mesh, l0_mm=cfg.l0)
        print("Audit Results:")
        for k, v in res.items():
            print("  %s: %s" % (k, str(v)))

    if args.build_deck and args.output_deck:
        print("\nBuilding 3-layer UEL production deck...")
        job_name = Path(args.output_deck).stem
        res = ProductionDeckBuilder.build_deck(
            args.build_deck, args.output_deck, job_name, cfg, step1_only=args.step1_only
        )
        print("Built UEL Deck: %s (%d layered elements)" % (res["deck_path"], res["total_layered_elements"]))


if __name__ == "__main__":
    main()
