# -*- coding: utf-8 -*-
"""
scripts/remeshing/reusable_2d_adaptive_framework.py
===================================================
Task: F1728 - UNIFIED PHYSICS-DRIVEN METHOD A ADAPTIVE REMESHING ENGINE
Unified, modular, geometry-independent 2D adaptive remeshing framework for
Mode-I phase-field fracture in Abaqus 2023 on HPC and local environments.

Supports all Five Mandatory Benchmark Geometries:
  - Case 1: Straight-Notch Mode-I Edge-Cracked Plate (Pandey & Kumar 2025, Sec. 4.1, 13,941 el)
  - Case 2: Original Master Thesis Off-Axis Circular Hole Plate (1x1 mm, hole at (0.65, 0.65))
  - Case 3: Rectangular Notched Plate with Hole and Pin Holes (Sec. 4.3, 65x120 mm, dual corridors)
  - Case 4: Square Plate with Five Holes (Sec. 4.5, Table 5 coordinates, 12,944 el)
  - Case 5: Square Plate with Seven Holes (Sec. 4.6, Table 6 coordinates, 15,714 el)

Architecture:
1. AdaptiveConfig: Configuration loader & validator for benchmark definitions.
2. GeometryAdapter (Base): Abstract interface for geometry creation and boundary identification.
   - StraightNotchMode1Adapter (Case 1)
   - OffAxisHoleMode1Adapter (Case 2)
   - NotchedPlateWithPinHolesAdapter (Case 3)
   - FiveHolePlateAdapter (Case 4)
   - SevenHolePlateAdapter (Case 5)
   - MultiHolePlateAdapter (General multi-void fallback)
3. MeshQualityAuditEngine: Standalone finite-element verification (signed isoparametric Jacobians,
   corner angles, aspect ratios, and spatially resolved h_area and h_max_edge metrics).
4. ProductionDeckBuilder: Deterministic converter from 2D physical mesh (quads + tris) into
   authoritative 3-layer UEL + companion UMAT input decks matching f42_mixed_uel.for.
5. AdvancingDamageEnvelopeBuilder: Synthesizes advancing damage envelopes from coupled fracture simulations
   into native Abaqus UNIFORM_ERROR sizing donors using analytical phase-field inversion laws.
6. AbaqusNativeRemeshingEngine: Native RemeshingRule and adaptiveRemesh() execution backend
   operating headlessly under Abaqus/CAE on HPC Linux and workstations.
"""

# F1849: CONSTRUCTED_DAMAGE_ENVELOPE primary sizing driver.
# Base: frozen F1779 c8d8588fb; config/adapters/CAD ported from preserved F1846.
# Full-history offline comparison; never qualifies native MISESERI.
from __future__ import print_function

import argparse
import hashlib
import json
import math
import os
import shutil
import sys

def safe_makedirs(path):
    if path and not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError:
            if not os.path.isdir(path):
                raise

def py_sum(iterable, start=0):
    """Pure-Python summation avoiding Abaqus CAE builtin sum() generator rejection."""
    s = start
    for x in iterable:
        s += x
    return s

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

try:
    from abaqus import mdb, session
    from abaqusConstants import *
    import regionToolset
    import mesh
    import odbAccess
    ABAQUS_AVAILABLE = True
except ImportError:
    ABAQUS_AVAILABLE = False


# ==============================================================================
# 1. CONFIGURATION SYSTEM
# ==============================================================================

class AdaptiveConfig(object):
    """Encapsulates and validates all parameters for arbitrary 2D adaptive remeshing."""

    def __init__(self, config_data):
        self.raw = config_data
        self.case_id = str(config_data.get("case_id", "case_unknown"))
        self.benchmark_name = config_data.get("benchmark_name", "Unknown Benchmark")
        self.geometry_type = config_data.get("geometry_type", "UNKNOWN")

        geom = config_data.get("geometry", {})
        self.plate_w = float(geom.get("plate_width", 1.0))
        self.plate_h = float(geom.get("plate_height", 1.0))
        self.width = self.plate_w
        self.height = self.plate_h
        self.thickness = float(geom.get("plate_thickness", 1.0))

        # Generic geometry definition
        self.polygon_vertices = geom.get("polygon_vertices", None)
        if self.polygon_vertices is not None:
            self.polygon_vertices = [tuple(float(c) for c in pt) for pt in self.polygon_vertices]

        self.seam_crack = geom.get("seam_crack", None)
        if self.seam_crack is not None:
            self.seam_crack = [tuple(float(c) for c in pt) for pt in self.seam_crack]

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
        self.edge_cutouts = geom.get("edge_cutouts", [])
        self.has_hole = bool(geom.get("has_hole", False)) or len(self.voids) > 0 or len(self.edge_cutouts) > 0
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
        if self.E < 1000.0:
            self.E = self.E * 1000.0
        self.nu = float(mat.get("poisson_ratio", mat.get("nu", 0.3)))
        self.l0 = float(mat.get("length_scale_l0_mm", mat.get("l0", 0.0075)))
        self.Gc = float(mat.get("gc_kn_per_mm", mat.get("Gc", 0.0027)))
        self.k_residual = float(mat.get("residual_stiffness_k", mat.get("k_residual", 1e-7)))
        self.constitutive_law = str(mat.get("constitutive_law", "ISOTROPIC_ELASTIC_PHASE_FIELD"))

        load = config_data.get("loading", {})
        self.loading_type = str(load.get("loading_type", "EDGE_PULL"))
        self.bc_type = self.loading_type
        self.bottom_u2 = float(load.get("bottom_u2", 0.0))
        self.pin_bottom_left_u1 = float(load.get("pin_bottom_left_u1", 0.0))
        self.step1_u2 = float(load.get("step1_precritical_u2", load.get("step1_disp", 0.005)))
        self.step2_u2 = float(load.get("step2_fracture_u2", load.get("step2_disp", 0.012)))
        self.kinematics = str(load.get("kinematics", "LINEAR"))
        self.lower_hole_center = tuple(load.get("lower_hole_center", [20.0, 20.0]))
        self.lower_hole_radius = float(load.get("lower_hole_radius", 5.0))
        self.upper_hole_center = tuple(load.get("upper_hole_center", [20.0, 100.0]))
        self.upper_hole_radius = float(load.get("upper_hole_radius", 5.0))
        self.top_pin_hole = {"center": list(self.upper_hole_center), "radius": self.upper_hole_radius}
        self.bottom_pin_hole = {"center": list(self.lower_hole_center), "radius": self.lower_hole_radius}

        rr = config_data.get("remeshing_rule", config_data.get("remeshing", {}))
        self.error_target = float(rr.get("error_target", rr.get("error_target_pct", 5.0)))
        self.min_h = float(rr.get("min_element_size_mm", rr.get("h_min", 0.0015)))
        self.max_h = float(rr.get("max_element_size_mm", rr.get("h_max", 0.020)))
        self.refinement_factor = int(rr.get("refinement_factor", 10))
        self.coarsening_factor = str(rr.get("coarsening_factor", "NOT_ALLOWED" if not rr.get("coarsening_allowed", False) else "DEFAULT_LIMIT"))
        self.sizing_method = str(rr.get("sizing_method", "UNIFORM_ERROR"))
        self.variable = str(rr.get("variable", rr.get("indicator", "MISESERI")))
        self.step_name = str(rr.get("step_name", "Step-1"))
        self.output_frequency = str(rr.get("output_frequency", "ALL_INCREMENTS"))

        opts = config_data.get("deck_options", config_data.get("paths", {}))
        self.uel_subroutine = opts.get("uel_subroutine", opts.get("uel_source", "f42_mixed_uel.for"))
        self.expected_uel_sha256 = opts.get("expected_uel_sha256", opts.get("frozen_uel_sha256", FROZEN_UEL_SHA256))
        self.output_dir = opts.get("output_directory", opts.get("output_dir", "."))

        pub = config_data.get("published_benchmark", {})
        self.target_elements = pub.get("target_elements", None)
        self.target_h_min_mm = pub.get("target_h_min_mm", None)

        self._validate()

    def _validate(self):
        if self.polygon_vertices is None:
            if self.plate_w <= 0.0 or self.plate_h <= 0.0:
                raise ValueError("Plate dimensions must be positive.")
            if self.notch_a is not None:
                if self.notch_a <= 0.0 or self.notch_a >= self.plate_w:
                    raise ValueError("Notch length must be within (0, plate_width).")
        else:
            if len(self.polygon_vertices) < 3:
                raise ValueError("polygon_vertices must define a closed polygon with at least 3 vertices.")
        if self.has_hole:
            if len(self.voids) > 1 or len(self.edge_cutouts) > 0 or self.polygon_vertices is not None:
                pass
            elif self.hole_x is None or self.hole_y is None or self.hole_r is None:
                raise ValueError("Hole coordinates and radius must be specified when has_hole=True.")
            elif self.hole_r <= 0.0:
                raise ValueError("Hole radius must be positive.")
        if self.error_target <= 0.05:
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
    """Abstract base adapter for 2D adaptive remeshing geometries."""

    def __init__(self, config):
        self.config = config

    def get_outer_polygon_points(self):
        """Returns ordered list of (x, y) vertices defining the outer boundary."""
        raise NotImplementedError

    def get_hole_definitions(self):
        """Returns list of (center_x, center_y, radius) tuples for internal circular voids."""
        raise NotImplementedError

    def get_seam_line(self):
        """Returns optional ((x1, y1, 0.0), (x2, y2, 0.0), (xmid, ymid, 0.0)) seam line."""
        return None

    def is_inside_domain(self, x, y, tol=1e-5):
        """Analytical containment check."""
        raise NotImplementedError

    def classify_region(self, x, y, authentic_damage=None):
        """
        Classifies point (x, y) into physical fracture zones for post-remeshing quality audits.
        NOTE: Region classification is strictly audit-only and has NO influence on remeshing rules.
        Remeshing rules operate universally on ALL_ELEM.
        """
        raise NotImplementedError


class Generic2DGeometryAdapter(GeometryAdapter):
    """
    Generalized 2D geometry adapter accepting arbitrary planar domains defined entirely
    via configuration without ANY hardcoded crack-path coordinates.
    """

    def __init__(self, config):
        super(Generic2DGeometryAdapter, self).__init__(config)
        self.polygon = config.polygon_vertices or [
            (0.0, 0.0),
            (config.plate_w, 0.0),
            (config.plate_w, config.plate_h),
            (0.0, config.plate_h)
        ]
        self.holes = []
        for v in getattr(config, "voids", []):
            self.holes.append((float(v["x"]), float(v["y"]), float(v["r"])))
        if getattr(config, "hole_x", None) is not None and getattr(config, "hole_r", None) is not None:
            h = (config.hole_x, config.hole_y, config.hole_r)
            if h not in self.holes:
                self.holes.append(h)

        self.seam = None
        if config.seam_crack is not None and len(config.seam_crack) >= 2:
            p1 = config.seam_crack[0]
            p2 = config.seam_crack[1]
            pmid = (0.5 * (p1[0] + p2[0]), 0.5 * (p1[1] + p2[1]), 0.0)
            self.seam = ((p1[0], p1[1], 0.0), (p2[0], p2[1], 0.0), pmid)

    def get_outer_polygon_points(self):
        return self.polygon

    def get_hole_definitions(self):
        return self.holes

    def get_seam_line(self):
        return self.seam

    def is_inside_domain(self, x, y, tol=1e-5):
        # Ray casting algorithm for arbitrary polygon
        n = len(self.polygon)
        inside = False
        p1x, p1y = self.polygon[0]
        for i in range(n + 1):
            p2x, p2y = self.polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        if not inside:
            return False

        # Exclude holes
        for (hx, hy, hr) in self.holes:
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

        # Check proximity to initial seam crack if defined
        if self.seam is not None:
            p1, p2, _ = self.seam
            # Distance to tip (p2)
            d_tip = math.hypot(x - p2[0], y - p2[1])
            if d_tip <= 3.0 * self.config.l0:
                return "INITIAL_NOTCH_ZONE"

        # Check proximity to holes
        for (hx, hy, hr) in self.holes:
            d_hole = abs(math.hypot(x - hx, y - hy) - hr)
            if d_hole <= 2.0 * self.config.l0:
                return "HOLE_BOUNDARY"

        # Check proximity to sharp re-entrant corners of the polygon
        n = len(self.polygon)
        for i in range(n):
            vx, vy = self.polygon[i]
            d_vert = math.hypot(x - vx, y - vy)
            if d_vert <= 3.0 * self.config.l0:
                return "CORNER_SINGULARITY_ZONE"

        return "FAR_FIELD"


class StraightNotchMode1Adapter(GeometryAdapter):
    """Adapter for Case 1: Mode-I edge-cracked plate (Sec. 4.1)."""

    def get_outer_polygon_points(self):
        w = self.config.notch_w if self.config.notch_w is not None else 0.001
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

    def get_seam_line(self):
        ny = self.config.notch_y if self.config.notch_y is not None else 0.5
        na = self.config.notch_a if self.config.notch_a is not None else 0.5
        return ((0.0, ny, 0.0), (na, ny, 0.0), (0.5 * na, ny, 0.0))

    def is_inside_domain(self, x, y, tol=1e-5):
        if x < -tol or x > self.config.plate_w + tol:
            return False
        if y < -tol or y > self.config.plate_h + tol:
            return False
        if x <= self.config.notch_a + tol and abs(y - self.config.notch_y) < (self.config.notch_w or 0.001) - tol:
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
        dx = x - self.config.notch_a
        dy = abs(y - self.config.notch_y)
        dist_tip = math.hypot(dx, dy)
        if dist_tip <= 3.0 * self.config.l0:
            return "CRACK_CORE"
        elif x >= self.config.notch_a and dy <= 3.0 * self.config.l0:
            return "PROPAGATION_CORRIDOR"
        return "FAR_FIELD"


class OffAxisHoleMode1Adapter(GeometryAdapter):
    """Adapter for Case 2: Mode-I plate with off-axis circular hole."""

    def get_outer_polygon_points(self):
        w = self.config.notch_w if self.config.notch_w is not None else 0.001
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

    def get_seam_line(self):
        ny = self.config.notch_y if self.config.notch_y is not None else 0.5
        na = self.config.notch_a if self.config.notch_a is not None else 0.5
        return ((0.0, ny, 0.0), (na, ny, 0.0), (0.5 * na, ny, 0.0))

    def is_inside_domain(self, x, y, tol=1e-5):
        if x < -tol or x > self.config.plate_w + tol:
            return False
        if y < -tol or y > self.config.plate_h + tol:
            return False
        if x <= self.config.notch_a + tol and abs(y - self.config.notch_y) < (self.config.notch_w or 0.001) - tol:
            return False
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
        if 0.50 <= x <= 0.65 and 0.50 <= y <= 0.65:
            return "NOTCH_TO_HOLE_LIGAMENT"
        elif 0.70 <= x <= 0.85 and 0.55 <= y <= 0.72:
            return "OPPOSITE_HOLE_FLANK"
        return "FAR_FIELD"


class NotchedPlateWithPinHolesAdapter(GeometryAdapter):
    """Adapter for Case 3: Pandey & Kumar (2025) Section 4.3 Notched Plate with Pins (65x120 mm)."""

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
        return [self.central_hole, self.lower_pin, self.upper_pin]

    def is_inside_domain(self, x, y, tol=1e-5):
        if x < -tol or x > self.plate_w + tol:
            return False
        if y < -tol or y > self.plate_h + tol:
            return False
        if x <= self.notch_a + tol and abs(y - self.notch_y) < self.notch_w - tol:
            return False
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
        # Primary ligament: notch tip (10, 70) to central hole perimeter (27, 53)
        x1, y1 = 10.0, 70.0
        x2, y2 = 27.0, 53.0
        dx, dy = x2 - x1, y2 - y1
        l2 = dx*dx + dy*dy
        t = max(0.0, min(1.0, ((x - x1)*dx + (y - y1)*dy) / l2)) if l2 > 0 else 0.0
        d_prim = math.hypot(x - (x1 + t*dx), y - (y1 + t*dy))
        if d_prim <= 3.0 * self.config.l0:
            return "PRIMARY_LIGAMENT"
        if 46.5 <= x <= 65.0 and abs(y - 51.0) <= 3.0 * self.config.l0:
            return "SECONDARY_LIGAMENT"
        d_cent = abs(math.hypot(x - 36.5, y - 51.0) - 10.0)
        if d_cent <= 2.0 * self.config.l0:
            return "CENTRAL_HOLE_BOUNDARY"
        d_low = abs(math.hypot(x - 20.0, y - 20.0) - 5.0)
        d_upp = abs(math.hypot(x - 20.0, y - 100.0) - 5.0)
        if min(d_low, d_upp) <= 2.0 * self.config.l0:
            return "PIN_HOLE_ZONES"
        return "FAR_FIELD"


class FiveHolePlateAdapter(GeometryAdapter):
    """Adapter for Case 4: Pandey & Kumar (2025) Section 4.5 Plate with Five Holes (1x1 mm)."""

    def __init__(self, config):
        super(FiveHolePlateAdapter, self).__init__(config)
        self.hole_1 = (0.35, 0.45, 0.10)
        self.hole_2 = (0.60, 0.55, 0.05)
        self.hole_3 = (0.75, 0.50, 0.075)
        self.left_arc = (0.0, 0.50, 0.10)
        self.right_arc = (1.0, 0.45, 0.075)

    def get_outer_polygon_points(self):
        return [
            (0.0, 0.0),
            (1.0, 0.0),
            (1.0, 0.375),
            (1.0, 0.525),
            (1.0, 1.0),
            (0.0, 1.0),
            (0.0, 0.600),
            (0.0, 0.400)
        ]

    def get_hole_definitions(self):
        return [self.hole_1, self.hole_2, self.hole_3]

    def is_inside_domain(self, x, y, tol=1e-5):
        if x < -tol or x > self.config.plate_w + tol:
            return False
        if y < -tol or y > self.config.plate_h + tol:
            return False
        if math.hypot(x - self.left_arc[0], y - self.left_arc[1]) < self.left_arc[2] - tol:
            return False
        if math.hypot(x - self.right_arc[0], y - self.right_arc[1]) < self.right_arc[2] - tol:
            return False
        for hx, hy, hr in self.get_hole_definitions():
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
        segments = [
            ((0.10, 0.50), (0.35, 0.45)),
            ((0.35, 0.45), (0.60, 0.55)),
            ((0.60, 0.55), (0.75, 0.50)),
            ((0.75, 0.50), (0.925, 0.45))
        ]
        min_d = 1e9
        for (x1, y1), (x2, y2) in segments:
            dx, dy = x2 - x1, y2 - y1
            l2 = dx*dx + dy*dy
            t = max(0.0, min(1.0, ((x - x1)*dx + (y - y1)*dy) / l2)) if l2 > 0 else 0.0
            d = math.hypot(x - (x1 + t*dx), y - (y1 + t*dy))
            if d < min_d:
                min_d = d
        if min_d <= 3.0 * self.config.l0:
            return "INTER_HOLE_LIGAMENTS"
        return "FAR_FIELD"


class SevenHolePlateAdapter(GeometryAdapter):
    """Adapter for Case 5: Pandey & Kumar (2025) Section 4.6 Plate with Seven Holes (1x1 mm)."""

    def __init__(self, config):
        super(SevenHolePlateAdapter, self).__init__(config)
        self.holes = [
            (0.15, 0.40, 0.10),
            (0.50, 0.55, 0.10),
            (0.85, 0.50, 0.10),
            (0.30, 0.60, 0.05),
            (0.70, 0.60, 0.05),
            (0.40, 0.35, 0.05),
            (0.65, 0.35, 0.05)
        ]

    def get_outer_polygon_points(self):
        return [
            (0.0, 0.0),
            (self.config.plate_w, 0.0),
            (self.config.plate_w, self.config.plate_h),
            (0.0, self.config.plate_h)
        ]

    def get_hole_definitions(self):
        return self.holes

    def is_inside_domain(self, x, y, tol=1e-5):
        if x < -tol or x > self.config.plate_w + tol:
            return False
        if y < -tol or y > self.config.plate_h + tol:
            return False
        for hx, hy, hr in self.get_hole_definitions():
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
        segments = [
            ((0.15, 0.40), (0.30, 0.60)),
            ((0.30, 0.60), (0.50, 0.55)),
            ((0.50, 0.55), (0.70, 0.60)),
            ((0.70, 0.60), (0.85, 0.50))
        ]
        min_d = 1e9
        for (x1, y1), (x2, y2) in segments:
            dx, dy = x2 - x1, y2 - y1
            l2 = dx*dx + dy*dy
            t = max(0.0, min(1.0, ((x - x1)*dx + (y - y1)*dy) / l2)) if l2 > 0 else 0.0
            d = math.hypot(x - (x1 + t*dx), y - (y1 + t*dy))
            if d < min_d:
                min_d = d
        if min_d <= 3.0 * self.config.l0:
            return "UPPER_CRACK_CORRIDOR"
        d6 = abs(math.hypot(x - 0.40, y - 0.35) - 0.05)
        d7 = abs(math.hypot(x - 0.65, y - 0.35) - 0.05)
        if min(d6, d7) <= 3.0 * self.config.l0:
            return "LOWER_SHIELDED_HOLES"
        return "FAR_FIELD"


class MultiHolePlateAdapter(GeometryAdapter):
    """General multi-void fallback adapter."""

    def __init__(self, config):
        super(MultiHolePlateAdapter, self).__init__(config)
        self.voids = getattr(config, "voids", [])
        self.internal_holes = []
        for v in self.voids:
            self.internal_holes.append((float(v.get("x", 0.0)), float(v.get("y", 0.0)), float(v.get("r", 0.0))))

    def get_outer_polygon_points(self):
        return [
            (0.0, 0.0),
            (self.config.plate_w, 0.0),
            (self.config.plate_w, self.config.plate_h),
            (0.0, self.config.plate_h)
        ]

    def get_hole_definitions(self):
        return self.internal_holes

    def is_inside_domain(self, x, y, tol=1e-5):
        if x < -tol or x > self.config.plate_w + tol:
            return False
        if y < -tol or y > self.config.plate_h + tol:
            return False
        for hx, hy, hr in self.get_hole_definitions():
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
        return "FAR_FIELD"


def get_geometry_adapter(config):
    """Factory to instantiate the appropriate geometry adapter."""
    gtype = getattr(config, "geometry_type", "").upper()
    cid = getattr(config, "case_id", "").lower()

    if getattr(config, "polygon_vertices", None) is not None or gtype == "GENERIC_2D":
        return Generic2DGeometryAdapter(config)
    elif gtype in ("NOTCHED_PLATE_WITH_PIN_HOLES", "SEC43_PLATE", "NOTCHED_HOLE_PLATE") or cid == "case_3":
        return NotchedPlateWithPinHolesAdapter(config)
    elif gtype == "FIVE_HOLE_PLATE" or cid == "case_4":
        return FiveHolePlateAdapter(config)
    elif gtype == "SEVEN_HOLE_PLATE" or cid == "case_5":
        return SevenHolePlateAdapter(config)
    elif gtype == "OFF_AXIS_HOLE_PLATE" or cid == "case_2":
        return OffAxisHoleMode1Adapter(config)
    elif gtype == "STRAIGHT_NOTCH_PLATE" or cid == "case_1":
        return StraightNotchMode1Adapter(config)
    elif len(getattr(config, "voids", [])) > 1:
        return MultiHolePlateAdapter(config)
    elif config.has_hole:
        return OffAxisHoleMode1Adapter(config)
    else:
        return Generic2DGeometryAdapter(config)


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

        if total_elems == 0:
            return {"error": "Empty or invalid physical mesh file", "total_elements": 0}

        min_jacobian = 1e9
        non_positive_jacobians = 0
        aspect_ratios = []
        corner_angles = []
        h_areas = []
        h_max_edges = []
        process_zone_h_areas = []
        far_field_h_areas = []

        for eid, conn in quad_elems.items():
            pts = [nodes[nid] for nid in conn if nid in nodes]
            if len(pts) != 4:
                continue

            # Quad area via Shoelace formula
            x = [p[0] for p in pts]
            y = [p[1] for p in pts]
            area = 0.5 * abs(
                (x[0]*y[1] - y[0]*x[1]) +
                (x[1]*y[2] - y[1]*x[2]) +
                (x[2]*y[3] - y[2]*x[3]) +
                (x[3]*y[0] - y[3]*x[0])
            )
            h_eq = math.sqrt(area) if area > 0 else 0.0
            h_areas.append(h_eq)

            edge_lengths = [
                math.hypot(x[(i+1)%4] - x[i], y[(i+1)%4] - y[i]) for i in range(4)
            ]
            max_edge = max(edge_lengths) if edge_lengths else 0.0
            min_edge = min(edge_lengths) if edge_lengths else 1e-9
            h_max_edges.append(max_edge)
            aspect_ratios.append(max_edge / max(min_edge, 1e-9))

            # 4 Gauss points for 2x2 integration
            gps = [-0.577350269189626, 0.577350269189626]
            for xi in gps:
                for eta in gps:
                    dNdxi = [
                        -0.25*(1-eta), 0.25*(1-eta), 0.25*(1+eta), -0.25*(1+eta)
                    ]
                    dNdeta = [
                        -0.25*(1-xi), -0.25*(1+xi), 0.25*(1+xi), 0.25*(1-xi)
                    ]
                    j11 = py_sum(dNdxi[i] * x[i] for i in range(4))
                    j12 = py_sum(dNdxi[i] * y[i] for i in range(4))
                    j21 = py_sum(dNdeta[i] * x[i] for i in range(4))
                    j22 = py_sum(dNdeta[i] * y[i] for i in range(4))
                    detJ = j11*j22 - j12*j21
                    min_jacobian = min(min_jacobian, detJ)
                    if detJ <= 0.0:
                        non_positive_jacobians += 1

            for i in range(4):
                v1 = (x[(i+3)%4] - x[i], y[(i+3)%4] - y[i])
                v2 = (x[(i+1)%4] - x[i], y[(i+1)%4] - y[i])
                dot = v1[0]*v2[0] + v1[1]*v2[1]
                m1 = math.hypot(v1[0], v1[1])
                m2 = math.hypot(v2[0], v2[1])
                if m1 > 0 and m2 > 0:
                    cos_theta = max(-1.0, min(1.0, dot / (m1*m2)))
                    corner_angles.append(math.degrees(math.acos(cos_theta)))

            cx = py_sum(x) / 4.0
            cy = py_sum(y) / 4.0
            if adapter:
                reg = adapter.classify_region(cx, cy)
                if reg != "FAR_FIELD":
                    process_zone_h_areas.append(h_eq)
                else:
                    far_field_h_areas.append(h_eq)

        for eid, conn in tri_elems.items():
            pts = [nodes[nid] for nid in conn if nid in nodes]
            if len(pts) != 3:
                continue

            x = [p[0] for p in pts]
            y = [p[1] for p in pts]
            detJ = (x[1]-x[0])*(y[2]-y[0]) - (x[2]-x[0])*(y[1]-y[0])
            area = 0.5 * abs(detJ)
            h_eq = math.sqrt(area) if area > 0 else 0.0
            h_areas.append(h_eq)

            min_jacobian = min(min_jacobian, detJ)
            if detJ <= 0.0:
                non_positive_jacobians += 1

            edge_lengths = [
                math.hypot(x[(i+1)%3] - x[i], y[(i+1)%3] - y[i]) for i in range(3)
            ]
            max_edge = max(edge_lengths) if edge_lengths else 0.0
            min_edge = min(edge_lengths) if edge_lengths else 1e-9
            h_max_edges.append(max_edge)
            aspect_ratios.append(max_edge / max(min_edge, 1e-9))

            for i in range(3):
                v1 = (x[(i+2)%3] - x[i], y[(i+2)%3] - y[i])
                v2 = (x[(i+1)%3] - x[i], y[(i+1)%3] - y[i])
                dot = v1[0]*v2[0] + v1[1]*v2[1]
                m1 = math.hypot(v1[0], v1[1])
                m2 = math.hypot(v2[0], v2[1])
                if m1 > 0 and m2 > 0:
                    cos_theta = max(-1.0, min(1.0, dot / (m1*m2)))
                    corner_angles.append(math.degrees(math.acos(cos_theta)))

            cx = py_sum(x) / 3.0
            cy = py_sum(y) / 3.0
            if adapter:
                reg = adapter.classify_region(cx, cy)
                if reg != "FAR_FIELD":
                    process_zone_h_areas.append(h_eq)
                else:
                    far_field_h_areas.append(h_eq)

        aspect_ratios.sort()
        corner_angles.sort()
        h_areas.sort()

        med_ar = aspect_ratios[len(aspect_ratios)//2] if aspect_ratios else 0.0
        max_ar = aspect_ratios[-1] if aspect_ratios else 0.0
        min_ang = corner_angles[0] if corner_angles else 0.0
        max_ang = corner_angles[-1] if corner_angles else 0.0

        n_le_l0 = py_sum(1 for h in h_areas if h <= l0_mm)
        n_le_l0_half = py_sum(1 for h in h_areas if h <= l0_mm / 2.0)
        n_le_l0_third = py_sum(1 for h in h_areas if h <= l0_mm / 3.0)

        mean_pz_h = py_sum(process_zone_h_areas)/len(process_zone_h_areas) if process_zone_h_areas else (py_sum(h_areas)/len(h_areas) if h_areas else 0.0)
        mean_ff_h = py_sum(far_field_h_areas)/len(far_field_h_areas) if far_field_h_areas else mean_pz_h
        refinement_ratio = mean_ff_h / max(mean_pz_h, 1e-9)

        return {
            "total_physical_elements": total_elems,
            "total_elements": total_elems,
            "total_nodes": total_nodes,
            "quad_count": len(quad_elems),
            "tri_count": len(tri_elems),
            "quad_percent": (float(len(quad_elems)) / total_elems) * 100.0 if total_elems > 0 else 0.0,
            "quad_fraction_pct": 100.0 * len(quad_elems) / max(total_elems, 1),
            "tri_fraction_pct": 100.0 * len(tri_elems) / max(total_elems, 1),
            "total_physical_nodes": total_nodes,
            "min_signed_jacobian": float(min_jacobian),
            "min_det_j": float(min_jacobian),
            "non_positive_jacobians": non_positive_jacobians,
            "zero_or_negative_jacobians": non_positive_jacobians,
            "distorted_elements": py_sum(1 for ar in aspect_ratios if ar > 10.0),
            "jacobian_status": "PASS" if non_positive_jacobians == 0 else "FAIL",
            "jacobian_valid": (non_positive_jacobians == 0),
            "median_aspect_ratio": float(med_ar),
            "max_aspect_ratio": float(max_ar),
            "worst_aspect_ratio": float(max_ar),
            "min_corner_angle_deg": float(min_ang),
            "max_corner_angle_deg": float(max_ang),
            "min_h_area_mm": float(h_areas[0]) if h_areas else 0.0,
            "min_h_area_um": float(h_areas[0] * 1000.0) if h_areas else 0.0,
            "max_h_area_mm": float(h_areas[-1]) if h_areas else 0.0,
            "mean_h_area_mm": float(py_sum(h_areas)/len(h_areas)) if h_areas else 0.0,
            "mean_process_zone_h_area_mm": float(mean_pz_h),
            "mean_process_zone_h_area_um": float(mean_pz_h * 1000.0),
            "mean_far_field_h_area_mm": float(mean_ff_h),
            "refinement_ratio_far_to_core": float(refinement_ratio),
            "process_zone_elements_count": len(process_zone_h_areas),
            "elements_le_l0": n_le_l0,
            "pct_elements_le_l0": 100.0 * n_le_l0 / max(total_elems, 1),
            "elements_le_l0_half": n_le_l0_half,
            "pct_elements_le_l0_half": 100.0 * n_le_l0_half / max(total_elems, 1),
            "elements_le_l0_third": n_le_l0_third,
            "pct_elements_le_l0_third": 100.0 * n_le_l0_third / max(total_elems, 1)
        }


# ==============================================================================
# 4. PRODUCTION DECK BUILDER (3-LAYER UEL ENGINE)
# ==============================================================================

class ProductionDeckBuilder(object):
    """Converts a physical mesh into an authoritative 3-layer UEL + companion UMAT deck."""

    FROZEN_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

    @classmethod
    def verify_uel_file(cls, uel_path, expected_sha=None):
        target = (expected_sha or cls.FROZEN_UEL_SHA256).lower()
        if not uel_path or not os.path.exists(uel_path):
            return False, None, target
        with open(uel_path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest().lower()
        return (digest == target), digest, target

    @classmethod
    def build_deck(cls, src_phys_inp, dst_uel_inp, job_name, config, step1_only=False, uel_source_path=None):
        nodes, quad_elems, tri_elems = MeshQualityAuditEngine.parse_physical_inp(src_phys_inp)
        num_phys_elems = len(quad_elems) + len(tri_elems)
        num_nodes = len(nodes)

        dst_dir = os.path.dirname(os.path.abspath(dst_uel_inp))
        safe_makedirs(dst_dir)

        with open(dst_uel_inp, "w") as f:
            f.write("** ==========================================================\n")
            f.write("** Abaqus Input Deck - 3-Layer Method A Phase-Field Model\n")
            f.write("** Benchmark: %s\n" % config.benchmark_name)
            f.write("** Subroutine: %s\n" % config.uel_subroutine)
            f.write("** ==========================================================\n")
            f.write("*HEADING\nMethod A Adapted Phase-Field Model: %s\n" % job_name)
            f.write("*PREPRINT, ECHO=NO, MODEL=NO, HISTORY=NO\n\n")

            # Nodes
            f.write("** ----------------------------------------------------------\n")
            f.write("** NODES\n")
            f.write("** ----------------------------------------------------------\n")
            f.write("*NODE, NSET=ALLNODES\n")
            for nid in sorted(nodes.keys()):
                coord = nodes[nid]
                f.write("%d, %.8e, %.8e\n" % (nid, coord[0], coord[1]))

            rp_nid = 999999
            if config.loading_type == "PIN_HOLE_PULL":
                rp_coord = config.upper_hole_center
            else:
                rp_coord = (0.5 * config.plate_w, config.plate_h)
            f.write("%d, %.8e, %.8e\n" % (rp_nid, rp_coord[0], rp_coord[1]))

            # Layer 1: Phase-Field UEL
            f.write("** ----------------------------------------------------------\n")
            f.write("** LAYER 1: Phase-Field User Elements (DOF 3)\n")
            f.write("** ----------------------------------------------------------\n")
            if quad_elems:
                f.write("*USER ELEMENT, NODES=4, TYPE=U1, PROPERTIES=6, COORDINATES=2, VARIABLES=18\n3\n")
                f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
                for eid in sorted(quad_elems.keys()):
                    c = quad_elems[eid]
                    f.write("%d, %d, %d, %d, %d\n" % (eid, c[0], c[1], c[2], c[3]))

            if tri_elems:
                f.write("*USER ELEMENT, NODES=3, TYPE=U3, PROPERTIES=6, COORDINATES=2, VARIABLES=18\n3\n")
                f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
                for eid in sorted(tri_elems.keys()):
                    c = tri_elems[eid]
                    f.write("%d, %d, %d, %d\n" % (eid, c[0], c[1], c[2]))

            # Layer 2: Mechanical Displacement UEL
            f.write("** ----------------------------------------------------------\n")
            f.write("** LAYER 2: Mechanical Displacement User Elements (DOF 1, 2)\n")
            f.write("** ----------------------------------------------------------\n")
            offset_disp = num_phys_elems
            if quad_elems:
                f.write("*USER ELEMENT, NODES=4, TYPE=U2, PROPERTIES=6, COORDINATES=2, VARIABLES=18\n1, 2\n")
                f.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
                for eid in sorted(quad_elems.keys()):
                    c = quad_elems[eid]
                    f.write("%d, %d, %d, %d, %d\n" % (eid + offset_disp, c[0], c[1], c[2], c[3]))

            if tri_elems:
                f.write("*USER ELEMENT, NODES=3, TYPE=U4, PROPERTIES=6, COORDINATES=2, VARIABLES=18\n1, 2\n")
                f.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
                for eid in sorted(tri_elems.keys()):
                    c = tri_elems[eid]
                    f.write("%d, %d, %d, %d\n" % (eid + offset_disp, c[0], c[1], c[2]))

            # Layer 3: Companion Continuum Elements
            f.write("** ----------------------------------------------------------\n")
            f.write("** LAYER 3: Companion Visualizer Elements (CPE4 / CPE3)\n")
            f.write("** ----------------------------------------------------------\n")
            offset_vis = 2 * num_phys_elems
            if quad_elems:
                f.write("*ELEMENT, TYPE=CPE4, ELSET=umatelem_quad\n")
                for eid in sorted(quad_elems.keys()):
                    c = quad_elems[eid]
                    f.write("%d, %d, %d, %d, %d\n" % (eid + offset_vis, c[0], c[1], c[2], c[3]))

            if tri_elems:
                f.write("*ELEMENT, TYPE=CPE3, ELSET=umatelem_tri\n")
                for eid in sorted(tri_elems.keys()):
                    c = tri_elems[eid]
                    f.write("%d, %d, %d, %d\n" % (eid + offset_vis, c[0], c[1], c[2]))

            # Element sets
            f.write("*ELSET, ELSET=All_elem\n")
            if quad_elems and tri_elems:
                f.write("umatelem_quad, umatelem_tri\n")
            elif quad_elems:
                f.write("umatelem_quad\n")
            else:
                f.write("umatelem_tri\n")
            f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

            # Boundary node sets
            tol = 1e-4
            bottom_nodes = []
            top_nodes = []
            pin_node = None
            min_dist_pin = 1e9

            lower_hole_nodes = []
            upper_nodes = []

            is_pin_hole = (config.loading_type == "PIN_HOLE_PULL")
            lh_c = config.lower_hole_center
            lh_r = config.lower_hole_radius
            uh_c = config.upper_hole_center
            uh_r = config.upper_hole_radius

            for nid, (x, y) in nodes.items():
                if is_pin_hole:
                    if abs(math.hypot(x - lh_c[0], y - lh_c[1]) - lh_r) < tol * 50:
                        lower_hole_nodes.append(nid)
                    if abs(math.hypot(x - uh_c[0], y - uh_c[1]) - uh_r) < tol * 50:
                        upper_nodes.append(nid)
                else:
                    if abs(y) < tol:
                        bottom_nodes.append(nid)
                    if abs(y - config.plate_h) < tol:
                        top_nodes.append(nid)
                    dist = math.hypot(x, y)
                    if dist < min_dist_pin:
                        min_dist_pin = dist
                        pin_node = nid

            f.write("** ----------------------------------------------------------\n")
            f.write("** BOUNDARY NODE SETS\n")
            f.write("** ----------------------------------------------------------\n")
            if is_pin_hole:
                f.write("*NSET, NSET=N_LOWER_HOLE\n")
                for i, nid in enumerate(sorted(lower_hole_nodes)):
                    f.write("%d%s" % (nid, ",\n" if (i+1)%10==0 or i==len(lower_hole_nodes)-1 else ", "))
                f.write("\n*NSET, NSET=N_UPPER_HOLE\n")
                for i, nid in enumerate(sorted(upper_nodes)):
                    f.write("%d%s" % (nid, ",\n" if (i+1)%10==0 or i==len(upper_nodes)-1 else ", "))
                f.write("\n*NSET, NSET=N_RP\n%d\n" % rp_nid)
            else:
                f.write("*NSET, NSET=N_BOTTOM\n")
                for i, nid in enumerate(sorted(bottom_nodes)):
                    f.write("%d%s" % (nid, ",\n" if (i+1)%10==0 or i==len(bottom_nodes)-1 else ", "))
                f.write("\n*NSET, NSET=N_TOP\n")
                for i, nid in enumerate(sorted(top_nodes)):
                    f.write("%d%s" % (nid, ",\n" if (i+1)%10==0 or i==len(top_nodes)-1 else ", "))
                f.write("\n*NSET, NSET=N_PIN\n%d\n" % pin_node)
                f.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)

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

            # Companion Material
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

            # Tie Equations
            f.write("** ----------------------------------------------------------\n")
            if is_pin_hole:
                f.write("** EQUATIONS (Upper pin hole tied to RP in DOF 2)\n")
                f.write("** ----------------------------------------------------------\n")
                for nid in sorted(upper_nodes):
                    f.write("*EQUATION\n2\n")
                    f.write("%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))
            else:
                f.write("** EQUATIONS (Rigid top tensile pull tied to RP in DOF 2)\n")
                f.write("** ----------------------------------------------------------\n")
                for nid in sorted(top_nodes):
                    f.write("*EQUATION\n2\n")
                    f.write("%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))

            # Step 1
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

        # Truthful UEL Hash Verification
        FROZEN_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
        uel_candidates = []
        if uel_source_path:
            uel_candidates.append(uel_source_path)
        sub_name = getattr(config, "uel_subroutine", None)
        if sub_name:
            base_sub_name = os.path.basename(sub_name)
            src_dir = os.path.dirname(os.path.abspath(src_phys_inp))
            uel_candidates.append(os.path.join(src_dir, base_sub_name))
            uel_candidates.append(os.path.join(src_dir, sub_name))
            dst_dir = os.path.dirname(os.path.abspath(dst_uel_inp))
            uel_candidates.append(os.path.join(dst_dir, base_sub_name))
            uel_candidates.append(os.path.join(dst_dir, sub_name))
            uel_candidates.append(os.path.join("models", "pandey_kumar_mode1", sub_name))
            uel_candidates.append(os.path.join("models", "pandey_kumar_mode1", base_sub_name))
            uel_candidates.append(os.path.join("models", "pandey_kumar_mode1", "219_f1728_five_geometry_study", sub_name))
            uel_candidates.append(os.path.join("models", "pandey_kumar_mode1", "219_f1728_five_geometry_study", base_sub_name))
            uel_candidates.append(os.path.join(os.getcwd(), base_sub_name))
            uel_candidates.append(os.path.join(os.getcwd(), sub_name))
            uel_candidates.append(sub_name)
            uel_candidates.append(base_sub_name)

        found_uel = None
        for cand in uel_candidates:
            if cand and os.path.exists(cand):
                found_uel = cand
                break

        expected_hash = (getattr(config, "expected_uel_sha256", None) or FROZEN_UEL_SHA256).lower()
        actual_uel_hash = None
        uel_verified = False
        if found_uel and os.path.exists(found_uel):
            with open(found_uel, "rb") as uf:
                actual_uel_hash = hashlib.sha256(uf.read()).hexdigest().lower()
            uel_verified = (actual_uel_hash == expected_hash)
        else:
            uel_verified = False

        return {
            "status": "SUCCESS",
            "deck_path": dst_uel_inp,
            "total_physical_elements": num_phys_elems,
            "total_layered_elements": 3 * num_phys_elems,
            "phase_elements": num_phys_elems,
            "mech_elements": num_phys_elems,
            "umat_elements": num_phys_elems,
            "total_nodes": num_nodes + 1,
            "uel_source_path": found_uel,
            "uel_sha256": actual_uel_hash,
            "expected_uel_sha256": expected_hash,
            "uel_hash_verified": uel_verified
        }


# ==============================================================================
# 5. ADVANCING DAMAGE ENVELOPE BUILDER (UNIFIED METHOD A EXTENSION)
# ==============================================================================

class AdvancingDamageEnvelopeBuilder(object):
    """
    Synthesizes authentic advancing damage envelopes from coarse coupled fracture simulations
    into native Abaqus UNIFORM_ERROR sizing donors (MISESERI / MISESAVG / EVOL).
    Eliminates linear-elastic pre-analysis stress decay across multi-ligament and distal regions
    using genuine physical phase-field damage indicator information.
    """

    @staticmethod
    def analytical_damage_sizing(d, l0, h_bg, core_factor=2.5, process_factor=1.2,
                                 d_core=0.5, d_proc=0.1, d_noise=0.01):
        """
        Physical phase-field sizing law derived from the 1D exponential damage profile:
        - d >= d_core (0.50): dense refinement to crack core h <= l0 / core_factor
        - d_proc <= d < d_core: process zone transition h in [h_core, h_proc]
        - d_noise <= d < d_proc: transition from h_proc to far-field background h_bg
        - d < d_noise: unrefined background h_bg
        """
        h_core = l0 / float(core_factor)
        h_proc = l0 / float(process_factor)
        if d >= d_core:
            return h_core
        elif d >= d_proc:
            frac = (d - d_proc) / (d_core - d_proc)
            return h_proc - frac * (h_proc - h_core)
        elif d >= d_noise:
            frac = (d - d_noise) / (d_proc - d_noise)
            return h_bg - frac * (h_bg - h_proc)
        else:
            return h_bg

    @classmethod
    def build_envelope_odb(cls, source_odb_path, target_odb_path, l0, h_bg, error_target,
                           step_name='Step-2', damage_variable='SDV1', frame_stride=5, s_base=100.0):
        if not ABAQUS_AVAILABLE:
            raise RuntimeError("Abaqus environment not available; cannot build envelope ODB.")
        from odbAccess import openOdb
        from abaqusConstants import SCALAR, WHOLE_ELEMENT

        odb_src = openOdb(source_odb_path, readOnly=True)
        root_inst = odb_src.rootAssembly.instances
        inst_name = list(root_inst.keys())[0] if len(root_inst) > 0 else 'PART-1-1'
        inst_src = root_inst[inst_name]

        # Use UMATELEM set if present (visualizer layer), else all elements
        if 'UMATELEM' in inst_src.elementSets:
            target_elements = list(inst_src.elementSets['UMATELEM'].elements)
        else:
            target_elements = list(inst_src.elements)

        elem_labels = [e.label for e in target_elements]
        node_coords = {n.label: (n.coordinates[0], n.coordinates[1]) for n in inst_src.nodes}

        elem_h_old = {}
        evol_data = []
        for elem in target_elements:
            conn = elem.connectivity
            pts = [node_coords[nl] for nl in conn if nl in node_coords]
            if len(pts) == 4:
                x1, y1 = pts[0]; x2, y2 = pts[1]; x3, y3 = pts[2]; x4, y4 = pts[3]
                area = 0.5 * abs((x1*y2 - x2*y1) + (x2*y3 - x3*y2) + (x3*y4 - x4*y3) + (x4*y1 - x1*y4))
            elif len(pts) == 3:
                x1, y1 = pts[0]; x2, y2 = pts[1]; x3, y3 = pts[2]
                area = 0.5 * abs(x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1 - y2))
            else:
                area = h_bg * h_bg
            elem_h_old[elem.label] = math.sqrt(max(1e-12, area))
            evol_data.append((area,))

        if step_name not in odb_src.steps:
            odb_src.close()
            raise ValueError('Requested damage step missing: ' + step_name)
        step_src = odb_src.steps[step_name]
        n_frames = len(step_src.frames)
        if n_frames == 0:
            raise ValueError('Empty damage step')
        seen_damage = set()

        d_max_env = {el: 0.0 for el in elem_labels}
        frame_indices = list(range(0, n_frames, max(1, frame_stride)))
        if (n_frames - 1) not in frame_indices:
            frame_indices.append(n_frames - 1)

        for f_idx in frame_indices:
            f = step_src.frames[f_idx]
            if damage_variable in f.fieldOutputs:
                fo = f.fieldOutputs[damage_variable]
                for v in fo.values:
                    el = v.elementLabel
                    if el in d_max_env:
                        if math.isnan(float(v.data)) or math.isinf(float(v.data)):
                            raise ValueError('Nonfinite damage')
                        seen_damage.add(el)
                        if v.data > d_max_env[el]:
                            d_max_env[el] = v.data

        odb_src.close()
        if seen_damage != set(elem_labels):
            raise ValueError('Incomplete damage mapping')

        eri_vals = []
        avg_vals = []
        for el in elem_labels:
            d = max(0.0, min(1.0, d_max_env[el]))
            h_tgt = cls.analytical_damage_sizing(d, l0=l0, h_bg=h_bg)
            h_old = elem_h_old[el]
            eta_hat = error_target * (h_old / h_tgt)
            eri = s_base * eta_hat
            eri_vals.append((eri,))
            avg_vals.append((s_base,))

        target_dir = os.path.dirname(target_odb_path)
        if target_dir and not os.path.exists(target_dir):
            safe_makedirs(target_dir)
        if os.path.exists(target_odb_path):
            os.remove(target_odb_path)

        shutil.copyfile(source_odb_path, target_odb_path)
        odb_dst = openOdb(target_odb_path, readOnly=False)
        inst_dst = odb_dst.rootAssembly.instances[inst_name]
        step_dst = odb_dst.steps[step_name]

        env_frame = step_dst.Frame(frameId=9999, frameValue=999.0, description="CONSTRUCTED_DAMAGE_ENVELOPE; max SDV1; not native stress error")
        fo_evol = env_frame.FieldOutput(name='EVOL', description='Element volume', type=SCALAR)
        fo_evol.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=elem_labels, data=evol_data)
        fo_eri = env_frame.FieldOutput(name='MISESERI', description='CONSTRUCTED_DAMAGE_ENVELOPE sizing encoding; not native stress error', type=SCALAR)
        fo_eri.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=elem_labels, data=eri_vals)
        fo_avg = env_frame.FieldOutput(name='MISESAVG', description='Uniform Reference Average Stress', type=SCALAR)
        fo_avg.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=elem_labels, data=avg_vals)

        odb_dst.save()
        odb_dst.close()
        return target_odb_path


# ==============================================================================
# 6. ABAQUS NATIVE REMESHING ENGINE
# ==============================================================================

class AbaqusNativeRemeshingEngine(object):
    """Executes native Abaqus RemeshingRule and adaptiveRemesh() in CAE/noGUI environment."""

    @classmethod
    def build_cae_geometry(cls, m, adapter, config, seed_size, part_name='PART-1', instance_name='PART-1-1'):
        if not ABAQUS_AVAILABLE:
            raise RuntimeError("Abaqus environment not available; cannot invoke CAE CAD builder.")

        # Estimate sheet size
        pts = adapter.get_outer_polygon_points()
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        max_dim = max(max(xs) - min(xs), max(ys) - min(ys), config.plate_w, config.plate_h)
        s = m.ConstrainedSketch(name='__profile__', sheetSize=max(max_dim * 2.5, 10.0))
        seam_line = adapter.get_seam_line()

        # Check special case for legacy Case 1 & Case 2 slit notch
        if isinstance(adapter, (StraightNotchMode1Adapter, OffAxisHoleMode1Adapter)) and (config.notch_w is None or config.notch_w <= 0.001):
            s.rectangle(point1=(0.0, 0.0), point2=(config.plate_w, config.plate_h))
            for (hx, hy, hr) in adapter.get_hole_definitions():
                s.CircleByCenterPerimeter(center=(hx, hy), point1=(hx + hr, hy))
            ny = config.notch_y if config.notch_y is not None else 0.5
            na = config.notch_a if config.notch_a is not None else 0.5
            seam_line = ((0.0, ny, 0.0), (na, ny, 0.0), (0.5 * na, ny, 0.0))

        elif isinstance(adapter, FiveHolePlateAdapter):
            s.Line(point1=(0.0, 0.0), point2=(1.0, 0.0))
            s.Line(point1=(1.0, 0.0), point2=(1.0, 0.375))
            s.Arc3Points(point1=(1.0, 0.375), point2=(1.0, 0.525), point3=(0.925, 0.450))
            s.Line(point1=(1.0, 0.525), point2=(1.0, 1.0))
            s.Line(point1=(1.0, 1.0), point2=(0.0, 1.0))
            s.Line(point1=(0.0, 1.0), point2=(0.0, 0.60))
            s.Arc3Points(point1=(0.0, 0.600), point2=(0.0, 0.400), point3=(0.100, 0.500))
            s.Line(point1=(0.0, 0.400), point2=(0.0, 0.0))
            for (hx, hy, hr) in adapter.get_hole_definitions():
                s.CircleByCenterPerimeter(center=(hx, hy), point1=(hx + hr, hy))

        else:
            # Generic 2D polygon construction
            for i in range(len(pts)):
                s.Line(point1=pts[i], point2=pts[(i+1)%len(pts)])
            for (hx, hy, hr) in adapter.get_hole_definitions():
                s.CircleByCenterPerimeter(center=(hx, hy), point1=(hx + hr, hy))

        p = m.Part(name=part_name, dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
        p.BaseShell(sketch=s)
        del m.sketches['__profile__']

        if seam_line is not None:
            p1, p2, pmid = seam_line
            p.PartitionFaceByShortestPath(faces=p.faces, point1=p1, point2=p2)
            seam_edge = p.edges.findAt((pmid, ))
            p.engineeringFeatures.assignSeam(regions=regionToolset.Region(edges=seam_edge))

        mat = m.Material(name='Steel')
        mat.Elastic(table=((config.E, config.nu), ))
        m.HomogeneousSolidSection(name='SolidSec', material='Steel', thickness=1.0)
        p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName='SolidSec')

        p.seedPart(size=seed_size, deviationFactor=0.1, minSizeFactor=0.1)
        p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
        elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
        elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
        p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
        p.generateMesh()

        p.Set(name='ALL_ELEM', faces=p.faces)
        a = m.rootAssembly
        inst = a.Instance(name=instance_name, part=p, dependent=ON)
        a.Set(name='ALL_ELEM', faces=inst.faces)

        m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0)
        m.StaticStep(name='Step-2', previous='Step-1', timePeriod=1.0)
        if config.step_name not in ("Step-1", "Step-2"):
            m.StaticStep(name=config.step_name, previous='Step-2', timePeriod=1.0)

        return p, a, inst

    @classmethod
    def execute_native_remesh(cls, config, donor_odb_path, output_dir, model_name=None):
        if not ABAQUS_AVAILABLE:
            raise RuntimeError("Abaqus environment not available; cannot execute native adaptiveRemesh.")

        adapter = get_geometry_adapter(config)
        mname = model_name or ("Model_MethodA_" + str(config.case_id))

        if mname in mdb.models:
            del mdb.models[mname]
        m = mdb.Model(name=mname)
        if "Model-1" in mdb.models:
            del mdb.models["Model-1"]

        if getattr(config, 'sizing_driver', None) != 'CONSTRUCTED_DAMAGE_ENVELOPE':
            raise ValueError('Explicit CONSTRUCTED_DAMAGE_ENVELOPE driver required')
        donor_list = [p.strip() for p in donor_odb_path.split(",")] if isinstance(donor_odb_path, str) else list(donor_odb_path)
        first_odb = session.openOdb(name=donor_list[0])

        target_part_name = list(first_odb.parts.keys())[0] if len(first_odb.parts) > 0 else "PART-1"
        target_inst_name = list(first_odb.rootAssembly.instances.keys())[0] if len(first_odb.rootAssembly.instances) > 0 else "PART-1-1"
        first_odb.close()

        seed_size = config.max_h
        p, a, inst = cls.build_cae_geometry(
            m, adapter, config, seed_size, part_name=target_part_name, instance_name=target_inst_name
        )

        if 'ALL_ELEM' not in inst.sets:
            raise RuntimeError("FAIL_CLOSED: Region set 'ALL_ELEM' does not exist on instance '%s' in model '%s'" % (
                inst.name, m.name
            ))

        coarsen_opt = NOT_ALLOWED if config.coarsening_factor == "NOT_ALLOWED" else DEFAULT_LIMIT
        out_freq_opt = ALL_INCREMENTS if getattr(config, "output_frequency", "ALL_INCREMENTS") == "ALL_INCREMENTS" else LAST_INCREMENT

        # Multi-pass sequential remeshing supporting Method A.1 (single pass) and Method A.2 (multi-state)
        for pass_idx, cur_donor in enumerate(donor_list):
            odb_donor = session.openOdb(name=cur_donor)
            step_target = config.step_name
            if step_target not in odb_donor.steps:
                if "RECOVERY_STEP" in odb_donor.steps:
                    step_target = "RECOVERY_STEP"
                elif "Step-2" in odb_donor.steps:
                    step_target = "Step-2"
                elif "Step-1" in odb_donor.steps:
                    step_target = "Step-1"
                else:
                    step_target = list(odb_donor.steps.keys())[-1]

            final = odb_donor.steps[step_target].frames[-1]
            if 'envelope' not in str(final.description).lower():
                odb_donor.close()
                raise ValueError('Constructed donor must declare damage-envelope provenance')
            if final.frameId != 9999 or 'MISESERI' not in final.fieldOutputs or 'MISESAVG' not in final.fieldOutputs:
                odb_donor.close()
                raise ValueError('Expected synthetic frame ID 9999 and sizing fields')
            # Explicitly ensure CAE model has the target step matching the donor ODB (resolving F1728-R30)
            if step_target not in m.steps:
                prev_step = list(m.steps.keys())[-1]
                m.StaticStep(name=step_target, previous=prev_step, timePeriod=1.0)

            rule_name = "Rule_MethodA_%s_p%d" % (str(config.case_id), pass_idx + 1)
            if rule_name in m.remeshingRules:
                del m.remeshingRules[rule_name]

            m.RemeshingRule(
                name=rule_name,
                stepName=step_target,
                region=inst.sets['ALL_ELEM'],
                variables=(config.variable,),
                sizingMethod=UNIFORM_ERROR,
                errorTarget=config.error_target,
                refinementFactor=config.refinement_factor,
                coarseningFactor=coarsen_opt,
                specifyMinSize=True,
                minElementSize=config.min_h,
                specifyMaxSize=True,
                maxElementSize=config.max_h,
                outputFrequency=out_freq_opt
            )

            m.adaptiveRemesh(odb=odb_donor)
            odb_donor.close()

        safe_makedirs(output_dir)
        job_base = "PK_ADAPT_" + str(config.case_id).upper()
        if job_base in mdb.jobs:
            del mdb.jobs[job_base]
        j = mdb.Job(name=job_base, model=m.name, type=ANALYSIS)
        j.writeInput(consistencyChecking=OFF)

        raw_inp = job_base + ".inp"
        out_phys_inp = os.path.join(output_dir, job_base + "_PHYS.inp")
        if os.path.exists(raw_inp):
            if os.path.exists(out_phys_inp):
                os.remove(out_phys_inp)
            shutil.move(raw_inp, out_phys_inp)

        return out_phys_inp


# ==============================================================================
# 6. UNIFIED HIGH-LEVEL ENTRYPOINT: run_method_a_case (FAIL-CLOSED)
# ==============================================================================


def prepare_damage_donor(config, source, target, existing_envelope=False):
    """Explicit construction/reuse; no native-first detection or fallback."""
    config.sizing_driver = 'CONSTRUCTED_DAMAGE_ENVELOPE'
    if existing_envelope:
        return source
    return AdvancingDamageEnvelopeBuilder.build_envelope_odb(
        source, target, config.l0, config.max_h, config.error_target / 100.0,
        step_name=config.step_name, damage_variable='SDV1', frame_stride=5, s_base=100.0)
