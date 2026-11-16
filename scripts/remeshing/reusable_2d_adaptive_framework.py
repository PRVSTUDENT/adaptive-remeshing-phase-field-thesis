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
   into native Abaqus UNIFORM_ERROR sizing donors using analytical phase-field inversion laws (Method A.1).
5b. MultiStateRecoveryDonorBuilder: Constructs authentic continuum recovery models and synthesizes
   multi-state maximum error envelope ODBs (Method A.2).
6. AbaqusNativeRemeshingEngine: Native RemeshingRule and adaptiveRemesh() execution backend
   operating headlessly under Abaqus/CAE on HPC Linux and workstations.
"""

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
    import odbAccess
    from abaqusConstants import SCALAR, WHOLE_ELEMENT
    ODB_ACCESS_AVAILABLE = True
except ImportError:
    ODB_ACCESS_AVAILABLE = False

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
    """Encapsulates and validates all parameters for a 2D adaptive remeshing benchmark."""

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

        # Structured parsed void tuples (x, y, r) for generic geometry generation
        self.void_definitions = []
        for v in self.voids:
            if isinstance(v, dict):
                self.void_definitions.append((
                    float(v.get("x", 0.0)),
                    float(v.get("y", 0.0)),
                    float(v.get("r", 0.0))
                ))
            elif isinstance(v, (list, tuple)) and len(v) >= 3:
                self.void_definitions.append((float(v[0]), float(v[1]), float(v[2])))

        if "hole_center_x" in geom and geom["hole_center_x"] is not None:
            self.hole_x = float(geom["hole_center_x"])
            self.hole_y = float(geom["hole_center_y"])
            self.hole_r = float(geom["hole_radius"])
        elif len(self.void_definitions) == 1:
            self.hole_x, self.hole_y, self.hole_r = self.void_definitions[0]
        else:
            self.hole_x = None
            self.hole_y = None
            self.hole_r = None

        self.allow_legacy_geometry_defaults = bool(
            geom.get("allow_legacy_geometry_defaults", config_data.get("allow_legacy_geometry_defaults", False))
        )

        if self.allow_legacy_geometry_defaults and len(self.void_definitions) == 0:
            if self.case_id == "case_3" or self.geometry_type in ("NOTCHED_PLATE_WITH_PIN_HOLES", "SEC43_PLATE"):
                self.void_definitions = [(36.5, 51.0, 10.0), (20.0, 20.0, 5.0), (20.0, 100.0, 5.0)]
            elif self.case_id == "case_5" or self.geometry_type in ("SEVEN_HOLE_PLATE", "SEC46_PLATE"):
                self.void_definitions = [
                    (0.15, 0.40, 0.10), (0.50, 0.55, 0.10), (0.85, 0.50, 0.10),
                    (0.30, 0.60, 0.05), (0.70, 0.60, 0.05), (0.40, 0.35, 0.05), (0.65, 0.35, 0.05)
                ]
            elif self.case_id == "case_2" or self.geometry_type in ("OFF_AXIS_HOLE_PLATE", "HOLE_PLATE"):
                self.void_definitions = [(0.65, 0.65, 0.10)]
                self.hole_x, self.hole_y, self.hole_r = self.void_definitions[0]

        # Resolve pin-hole geometry dynamically from geometry.voids
        upper_pin = None
        lower_pin = None
        for v in self.voids:
            if isinstance(v, dict):
                vname = str(v.get("name", "")).lower()
                vx = float(v.get("x", 0.0))
                vy = float(v.get("y", 0.0))
                vr = float(v.get("r", 0.0))
                if "upper" in vname or "top" in vname:
                    upper_pin = ((vx, vy), vr)
                elif "lower" in vname or "bottom" in vname:
                    lower_pin = ((vx, vy), vr)

        # Coordinate-based fallback for un-named pin voids
        if (upper_pin is None or lower_pin is None) and len(self.void_definitions) >= 2:
            sorted_by_y = sorted(self.void_definitions, key=lambda item: item[1])
            lower_pin = ((sorted_by_y[0][0], sorted_by_y[0][1]), sorted_by_y[0][2])
            upper_pin = ((sorted_by_y[-1][0], sorted_by_y[-1][1]), sorted_by_y[-1][2])

        self.derived_upper_pin = upper_pin
        self.derived_lower_pin = lower_pin

        mat = config_data.get("material", {})
        self.E = float(mat.get("youngs_modulus_mpa", mat.get("E", 210000.0)))
        if self.E < 1000.0:  # If specified in GPa (e.g. 210.0), convert to MPa
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

        if self.loading_type == "PIN_HOLE_PULL" or upper_pin is not None:
            if upper_pin is not None:
                configured_uh = upper_pin[0]
                configured_ur = upper_pin[1]
                if "upper_hole_center" in load:
                    load_uh = tuple(load["upper_hole_center"])
                    if math.hypot(load_uh[0] - configured_uh[0], load_uh[1] - configured_uh[1]) > 1e-3:
                        raise ValueError(
                            "Stale loading coordinates detected: loading.upper_hole_center %s "
                            "does not match configured geometry void position %s. "
                            "In Case 3, pin reference points and boundary sets must derive "
                            "from the configured geometry definitions." % (str(load_uh), str(configured_uh))
                        )
                self.upper_hole_center = configured_uh
                self.upper_hole_radius = configured_ur
            else:
                if not self.allow_legacy_geometry_defaults:
                    raise ValueError(
                        "Missing required pin hole definitions in geometry.voids for loading_type='PIN_HOLE_PULL'. "
                        "Configured geometry must provide pin void definitions."
                    )
                self.upper_hole_center = tuple(load.get("upper_hole_center", [20.0, 100.0]))
                self.upper_hole_radius = float(load.get("upper_hole_radius", 5.0))

            if lower_pin is not None:
                configured_lh = lower_pin[0]
                configured_lr = lower_pin[1]
                if "lower_hole_center" in load:
                    load_lh = tuple(load["lower_hole_center"])
                    if math.hypot(load_lh[0] - configured_lh[0], load_lh[1] - configured_lh[1]) > 1e-3:
                        raise ValueError(
                            "Stale loading coordinates detected: loading.lower_hole_center %s "
                            "does not match configured geometry void position %s. "
                            "In Case 3, pin support boundary sets must derive "
                            "from the configured geometry definitions." % (str(load_lh), str(configured_lh))
                        )
                self.lower_hole_center = configured_lh
                self.lower_hole_radius = configured_lr
            else:
                if not self.allow_legacy_geometry_defaults:
                    raise ValueError(
                        "Missing required pin hole definitions in geometry.voids for loading_type='PIN_HOLE_PULL'. "
                        "Configured geometry must provide pin void definitions."
                    )
                self.lower_hole_center = tuple(load.get("lower_hole_center", [20.0, 20.0]))
                self.lower_hole_radius = float(load.get("lower_hole_radius", 5.0))
        else:
            self.upper_hole_center = tuple(load.get("upper_hole_center", [20.0, 100.0]))
            self.upper_hole_radius = float(load.get("upper_hole_radius", 5.0))
            self.lower_hole_center = tuple(load.get("lower_hole_center", [20.0, 20.0]))
            self.lower_hole_radius = float(load.get("lower_hole_radius", 5.0))

        self.top_pin_hole = {"center": list(self.upper_hole_center), "radius": self.upper_hole_radius}
        self.bottom_pin_hole = {"center": list(self.lower_hole_center), "radius": self.lower_hole_radius}

        rr = config_data.get("remeshing_rule", config_data.get("remeshing", {}))
        self.error_target = float(rr.get("error_target", rr.get("error_target_pct", 5.0)))
        self.min_h = float(rr.get("min_element_size_mm", rr.get("h_min", 0.0015)))
        self.max_h = float(rr.get("max_element_size_mm", rr.get("h_max", 0.020)))
        self.refinement_factor = int(rr.get("refinement_factor", 10))
        self.coarsening_factor = str(rr.get("coarsening_factor", "NOT_ALLOWED" if not rr.get("coarsening_allowed", False) else "DEFAULT_LIMIT"))
        self.sizing_method = str(rr.get("sizing_method", "UNIFORM_ERROR")).upper()
        self.max_solution_error_target = float(rr.get("max_solution_error_target", rr.get("max_error_target", self.error_target)))
        self.min_solution_error_target = float(rr.get("min_solution_error_target", rr.get("min_error_target", max(0.1, self.error_target / 5.0))))
        self.mesh_bias = int(rr.get("mesh_bias", 1))
        self.variable = str(rr.get("variable", rr.get("indicator", "MISESERI")))
        self.step_name = str(rr.get("step_name", "Step-1"))
        self.output_frequency = str(rr.get("output_frequency", "ALL_INCREMENTS"))

        # Explicit indicator provenance and sizing parameters
        ind = config_data.get("indicator_options", config_data.get("damage_envelope", config_data.get("envelope_options", config_data.get("envelope", {}))))
        default_ind_type = "DAMAGE_INFORMED_ENVELOPE" if self.case_id in ("case_1", "case_2") else "NATIVE_STRESS_ERROR"
        self.indicator_type = str(ind.get("indicator_type", rr.get("indicator_type", default_ind_type)))
        self.indicator_description = str(ind.get("description", ind.get("provenance_description", "Abaqus recovered stress error" if "NATIVE" in self.indicator_type else "Synthesized damage-informed sizing envelope")))
        
        def _get_float(d, key, dflt):
            v = d.get(key)
            return dflt if v is None else float(v)

        def _get_int(d, key, dflt):
            v = d.get(key)
            return dflt if v is None else int(v)

        self.core_factor = _get_float(ind, "core_factor", 3.0 if self.case_id == "case_1" else 2.5)
        self.process_factor = _get_float(ind, "process_factor", 1.2)
        self.d_core = _get_float(ind, "d_core", 0.40)
        self.d_proc = _get_float(ind, "d_proc", 0.10)
        self.d_noise = _get_float(ind, "d_noise", 0.08)
        self.frame_stride = _get_int(ind, "frame_stride", 5)
        self.h_bg = _get_float(ind, "h_bg", self.max_h)
        self.notch_root_elements = _get_int(geom, "notch_root_elements", _get_int(ind, "notch_root_elements", 4))
        self.max_frame_index = _get_int(ind, "max_frame_index", None) if ind.get("max_frame_index") is not None else None
        self.max_frame_time = _get_float(ind, "max_frame_time", None) if ind.get("max_frame_time") is not None else None
        self.causal_mode = bool(ind.get("causal_mode", False))

        opts = config_data.get("deck_options", config_data.get("paths", {}))
        self.uel_subroutine = opts.get("uel_subroutine", opts.get("uel_source", "f42_mixed_uel.for"))
        self.expected_uel_sha256 = opts.get("expected_uel_sha256", opts.get("frozen_uel_sha256", FROZEN_UEL_SHA256))
        self.output_dir = opts.get("output_directory", opts.get("output_dir", "."))

        pub = config_data.get("published_benchmark", {})
        self.target_elements = pub.get("target_elements", None)
        self.target_h_min_mm = pub.get("target_h_min_mm", None)

        self._validate()

    def _validate(self):
        if self.plate_w <= 0.0 or self.plate_h <= 0.0:
            raise ValueError("Plate dimensions must be positive.")
        if self.notch_a is not None:
            if self.notch_a <= 0.0 or self.notch_a >= self.plate_w:
                raise ValueError("Notch length must be within (0, plate_width).")
        if self.has_hole:
            if len(self.void_definitions) > 1 or len(self.edge_cutouts) > 0 or self.allow_legacy_geometry_defaults:
                pass
            elif len(self.void_definitions) == 1:
                pass
            elif self.hole_x is None or self.hole_y is None or self.hole_r is None:
                raise ValueError("Missing required geometry definition 'geometry.voids' or hole coordinates when has_hole=True. (To enable historical defaults, set 'allow_legacy_geometry_defaults': true).")
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
    """Abstract base adapter for 2D fracture benchmark geometries."""

    def __init__(self, config):
        self.config = config

    def get_outer_polygon_points(self):
        """Returns ordered list of (x, y) vertices defining the outer boundary."""
        raise NotImplementedError

    def get_hole_definitions(self):
        """Returns list of (center_x, center_y, radius) tuples for internal circular voids."""
        raise NotImplementedError

    def is_inside_domain(self, x, y, tol=1e-5):
        """Analytical containment check."""
        raise NotImplementedError

    def classify_region(self, x, y, authentic_damage=None):
        """Classifies point (x, y) into physical fracture zones."""
        raise NotImplementedError

    def apply_local_seeds(self, part, seed_size):
        """Optional hook for feature edge seeding to prevent aspect ratio distortion at sharp geometric transitions."""
        pass


class StraightNotchMode1Adapter(GeometryAdapter):
    """Adapter for Case 1: Conventional 1x1 mm edge-cracked Mode-I benchmark (Sec. 4.1)."""

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

    def is_inside_domain(self, x, y, tol=1e-5):
        if x < -tol or x > self.config.plate_w + tol:
            return False
        if y < -tol or y > self.config.plate_h + tol:
            return False
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
        dx = x - self.config.notch_a
        dy = abs(y - self.config.notch_y)
        dist_tip = math.hypot(dx, dy)
        if dist_tip <= 3.0 * self.config.l0:
            return "CRACK_CORE"
        elif x >= self.config.notch_a and dy <= 3.0 * self.config.l0:
            return "PROPAGATION_CORRIDOR"
        return "FAR_FIELD"

    def apply_local_seeds(self, part, seed_size):
        """Seed the horizontal notch seam edge to avoid boundary element stretching
        where free paving transitions from the refined crack core to the far field."""
        na = self.config.notch_a if self.config.notch_a is not None else 0.5
        ny = self.config.notch_y if self.config.notch_y is not None else 0.5
        try:
            seam_edges = part.edges.findAt(((0.5 * na, ny, 0.0), ))
            if seam_edges:
                seam_seed = min(self.config.l0 / 2.0, seed_size)
                part.seedEdgeBySize(edges=seam_edges, size=seam_seed, deviationFactor=0.05, minSizeFactor=0.02, constraint=FREE)
        except Exception:
            pass


class OffAxisHoleMode1Adapter(GeometryAdapter):
    """Adapter for Case 2: Original Master Thesis 1x1 mm Plate with Off-Axis Hole."""

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
        if hasattr(self.config, "void_definitions") and len(self.config.void_definitions) > 0:
            return list(self.config.void_definitions)
        if self.config.hole_x is not None and self.config.hole_y is not None and self.config.hole_r is not None:
            return [(self.config.hole_x, self.config.hole_y, self.config.hole_r)]
        if not getattr(self.config, "allow_legacy_geometry_defaults", False):
            raise ValueError(
                "Missing required void definition for Case 2 (OffAxisHoleMode1Adapter). "
                "Normal configured operation requires explicit void definitions in configuration JSON. "
                "To enable historical fallback, set 'allow_legacy_geometry_defaults': true in configuration."
            )
        return [(0.65, 0.65, 0.10)]

    def is_inside_domain(self, x, y, tol=1e-5):
        if x < -tol or x > self.config.plate_w + tol:
            return False
        if y < -tol or y > self.config.plate_h + tol:
            return False
        if x <= self.config.notch_a + tol and abs(y - self.config.notch_y) < self.config.notch_w - tol:
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
        for hx, hy, hr in self.get_hole_definitions():
            if math.hypot(x - hx, y - hy) <= hr + 2.0 * self.config.l0:
                return "HOLE_PERIMETER"
        return "FAR_FIELD"


class NotchedPlateWithPinHolesAdapter(GeometryAdapter):
    """Adapter for Case 3: Pandey & Kumar (2025) Section 4.3 Notched Plate with Pins (65x120 mm).
    All internal hole and pin geometries are configuration-driven via geometry.voids.
    """

    def __init__(self, config):
        super(NotchedPlateWithPinHolesAdapter, self).__init__(config)
        self.notch_a = float(config.notch_a if config.notch_a is not None else 10.0)
        self.notch_y = float(config.notch_y if config.notch_y is not None else 70.0)
        self.notch_w = float(config.notch_w if config.notch_w is not None else 0.2)
        self.plate_w = float(config.plate_w)
        self.plate_h = float(config.plate_h)
        if hasattr(config, "void_definitions") and len(config.void_definitions) > 0:
            self.holes = list(config.void_definitions)
        else:
            if not getattr(config, "allow_legacy_geometry_defaults", False):
                raise ValueError(
                    "Missing required geometry definition 'geometry.voids' for Case 3 (NotchedPlateWithPinHolesAdapter). "
                    "Normal configured operation requires explicit void definitions in configuration JSON. "
                    "To enable historical fallback, set 'allow_legacy_geometry_defaults': true in configuration."
                )
            # Legacy-compatibility fallback
            self.holes = [(36.5, 51.0, 10.0), (20.0, 20.0, 5.0), (20.0, 100.0, 5.0)]

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
        return self.holes

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

        # Check proximity to notch root
        if math.hypot(x - self.notch_a, y - self.notch_y) <= 3.0 * self.config.l0:
            return "NOTCH_ROOT_VICINITY"

        # Check proximity to any configuration-driven void perimeter
        for h_idx, (hx, hy, hr) in enumerate(self.get_hole_definitions()):
            if abs(math.hypot(x - hx, y - hy) - hr) <= 2.0 * self.config.l0:
                return "HOLE_%d_BOUNDARY" % (h_idx + 1)

        return "FAR_FIELD"

    def apply_local_seeds(self, part, seed_size):
        """
        Seed the vertical blunt notch root (2 * notch_w height) to prevent stretched elements
        where the narrow root meets horizontal notch flanks.
        Seed size is derived from root height and configured resolution constraints:
            derived_seed = (2.0 * notch_w) / float(notch_root_elements)
            seed = min(derived_seed, seed_size)
        ensuring regularized quad layers across the blunt root without hardcoded magic numbers.
        """
        short_edges = []
        tol = 1e-3
        for edge in part.edges:
            pt = edge.pointOn[0]
            if pt[0] <= self.notch_a + tol and (self.notch_y - self.notch_w - tol) <= pt[1] <= (self.notch_y + self.notch_w + tol):
                short_edges.append(edge)
        if short_edges:
            n_root = int(getattr(self.config, 'notch_root_elements', 4))
            derived_seed = (2.0 * self.notch_w) / float(max(1, n_root))
            target_seed = min(derived_seed, seed_size)
            for se in short_edges:
                part.seedEdgeBySize(edges=(se,), size=target_seed, deviationFactor=0.05, minSizeFactor=0.02, constraint=FREE)


class FiveHolePlateAdapter(GeometryAdapter):
    """Adapter for Case 4: Pandey & Kumar (2025) Section 4.5 Plate with Five Holes (1x1 mm).
    Features 2 boundary semicircles and 3 interior circular holes per Table 5.
    """

    def __init__(self, config):
        super(FiveHolePlateAdapter, self).__init__(config)
        self.hole_1 = (0.35, 0.45, 0.10)
        self.hole_2 = (0.60, 0.55, 0.05)
        self.hole_3 = (0.75, 0.50, 0.075)
        self.left_arc = (0.0, 0.50, 0.10)   # center x, y, radius
        self.right_arc = (1.0, 0.45, 0.075) # center x, y, radius

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
        # Check boundary semicircular cutouts
        if math.hypot(x - self.left_arc[0], y - self.left_arc[1]) < self.left_arc[2] - tol:
            return False
        if math.hypot(x - self.right_arc[0], y - self.right_arc[1]) < self.right_arc[2] - tol:
            return False
        # Check interior holes
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

        # Inter-hole ligament segments bridging left cutout -> h1 -> h2 -> h3 -> right cutout:
        segments = [
            ((0.10, 0.50), (0.35, 0.45)),  # Ligament 1
            ((0.35, 0.45), (0.60, 0.55)),  # Ligament 2
            ((0.60, 0.55), (0.75, 0.50)),  # Ligament 3 (narrowest, 33.1 um)
            ((0.75, 0.50), (0.925, 0.45))  # Ligament 4
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
    """Adapter for Case 5: Pandey & Kumar (2025) Section 4.6 Plate with Seven Holes (1x1 mm).
    All void coordinates and radii are configuration-driven via geometry.voids.
    """

    def __init__(self, config):
        super(SevenHolePlateAdapter, self).__init__(config)
        if hasattr(config, "void_definitions") and len(config.void_definitions) > 0:
            self.holes = list(config.void_definitions)
        else:
            if not getattr(config, "allow_legacy_geometry_defaults", False):
                raise ValueError(
                    "Missing required geometry definition 'geometry.voids' for Case 5 (SevenHolePlateAdapter). "
                    "Normal configured operation requires explicit void definitions in configuration JSON. "
                    "To enable historical fallback, set 'allow_legacy_geometry_defaults': true in configuration."
                )
            # Legacy-compatibility fallback
            self.holes = [
                (0.15, 0.40, 0.10), # h1
                (0.50, 0.55, 0.10), # h2
                (0.85, 0.50, 0.10), # h3
                (0.30, 0.60, 0.05), # h4
                (0.70, 0.60, 0.05), # h5
                (0.40, 0.35, 0.05), # h6 (shielded)
                (0.65, 0.35, 0.05)  # h7 (shielded)
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

        # Check proximity to any configuration-driven void perimeter
        for h_idx, (hx, hy, hr) in enumerate(self.get_hole_definitions()):
            if abs(math.hypot(x - hx, y - hy) - hr) <= 2.0 * self.config.l0:
                return "HOLE_%d_BOUNDARY" % (h_idx + 1)

        return "FAR_FIELD"


class MultiHolePlateAdapter(GeometryAdapter):
    """General multi-void fallback adapter."""

    def __init__(self, config):
        super(MultiHolePlateAdapter, self).__init__(config)
        self.voids = getattr(config, "voids", [])
        self.internal_holes = []
        for v in self.voids:
            vx = float(v.get("x", 0.0))
            vy = float(v.get("y", 0.0))
            vr = float(v.get("r", 0.0))
            self.internal_holes.append((vx, vy, vr))

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


def get_geometry_adapter(config):
    """Factory to instantiate the appropriate geometry adapter."""
    gtype = getattr(config, "geometry_type", "").upper()
    cid = getattr(config, "case_id", "").lower()

    if gtype in ("NOTCHED_PLATE_WITH_PIN_HOLES", "SEC43_PLATE", "NOTCHED_HOLE_PLATE") or cid == "case_3":
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
            "mean_aspect_ratio": float(py_sum(aspect_ratios)/len(aspect_ratios)) if aspect_ratios else 0.0,
            "aspect_ratio_violations_gt_4": py_sum(1 for ar in aspect_ratios if ar > 4.0),
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
            "pct_elements_le_l0_third": 100.0 * n_le_l0_third / max(total_elems, 1),
            "provenance_classification": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR" if getattr(getattr(adapter, "config", None), "indicator_type", "UNKNOWN") == "NATIVE_STRESS_ERROR" else "SYNTHESIZED_DAMAGE_INFORMED_SIZING_ENVELOPE",
            "indicator_type": getattr(getattr(adapter, "config", None), "indicator_type", "UNKNOWN")
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
    def analytical_damage_sizing(d, l0, h_bg, core_factor=2.8, process_factor=1.2,
                                 d_core=0.20, d_proc=0.10, d_noise=0.05):
        """
        Physical phase-field sizing law derived from the 1D exponential damage profile:
        - d >= d_core (0.20): dense refinement to crack core h <= l0 / core_factor
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
                           step_name='Step-2', damage_variable='SDV1', frame_stride=5, s_base=100.0,
                           core_factor=2.8, process_factor=1.2, d_core=0.20, d_proc=0.10, d_noise=0.05,
                           max_frame_index=None, max_frame_time=None, causal_mode=False):
        # Validate causal parameters upfront so input validation fails closed in all environments
        if causal_mode and max_frame_index is None and max_frame_time is None:
            raise ValueError(
                "FAIL_CLOSED: Causal adaptivity requires an explicit temporal horizon (max_frame_index or max_frame_time). "
                "Scanning unconstrained future frames is prohibited under causal adaptivity."
            )

        if max_frame_index is not None:
            val = int(max_frame_index)
            if val < 0:
                raise ValueError("FAIL_CLOSED: max_frame_index cannot be negative (got %d); negative indices would sample future/end frames in Python" % val)

        if max_frame_time is not None:
            t_target = float(max_frame_time)
            if t_target < 0.0:
                raise ValueError("FAIL_CLOSED: max_frame_time cannot be negative (got %f)" % t_target)

        if not (ABAQUS_AVAILABLE or ODB_ACCESS_AVAILABLE):
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
            step_name = list(odb_src.steps.keys())[-1]
        step_src = odb_src.steps[step_name]
        n_frames = len(step_src.frames)

        # Causal frame filtering: strictly prohibit scanning future frames when causal horizon is specified
        if causal_mode and max_frame_index is None and max_frame_time is None:
            raise ValueError(
                "FAIL_CLOSED: Causal adaptivity requires an explicit temporal horizon (max_frame_index or max_frame_time). "
                "Scanning unconstrained future frames is prohibited under causal adaptivity."
            )

        if max_frame_index is not None:
            val = int(max_frame_index)
            if val < 0:
                raise ValueError("FAIL_CLOSED: max_frame_index cannot be negative (got %d); negative indices would sample future/end frames in Python" % val)
            if val >= n_frames:
                raise ValueError("FAIL_CLOSED: max_frame_index %d exceeds donor step frame count (%d frames available in step '%s')" % (val, n_frames, step_name))
            max_idx = val
        else:
            max_idx = n_frames - 1

        if max_frame_time is not None:
            t_target = float(max_frame_time)
            t_min = step_src.frames[0].frameValue
            if t_target < t_min - 1e-9:
                raise ValueError("FAIL_CLOSED: max_frame_time %f precedes first frame timestamp (%f) in step '%s'" % (t_target, t_min, step_name))
            time_bounded = [i for i, f in enumerate(step_src.frames) if f.frameValue <= t_target + 1e-9]
            if not time_bounded:
                raise ValueError("FAIL_CLOSED: No frames found at or before max_frame_time %f in step '%s'" % (t_target, step_name))
            max_idx = min(max_idx, max(time_bounded))

        # Check timestamp monotonicity up to max_idx
        for i in range(1, max_idx + 1):
            if step_src.frames[i].frameValue < step_src.frames[i-1].frameValue - 1e-9:
                raise ValueError("FAIL_CLOSED: Donor frames are not monotonically non-decreasing in time at frame %d (t_prev=%f, t_curr=%f)" % (
                    i, step_src.frames[i-1].frameValue, step_src.frames[i].frameValue
                ))

        d_max_env = {el: 0.0 for el in elem_labels}
        frame_indices = list(range(0, max_idx + 1, max(1, frame_stride)))
        if max_idx not in frame_indices:
            frame_indices.append(max_idx)

        found_damage_var = False
        for f_idx in frame_indices:
            f = step_src.frames[f_idx]
            if damage_variable in f.fieldOutputs:
                found_damage_var = True
                fo = f.fieldOutputs[damage_variable]
                for v in fo.values:
                    el = v.elementLabel
                    if el in d_max_env:
                        if v.data > d_max_env[el]:
                            d_max_env[el] = v.data

        if not found_damage_var:
            raise ValueError("FAIL_CLOSED: Required damage variable '%s' not found in any sampled frame of step '%s'" % (damage_variable, step_name))

        odb_src.close()

        eri_vals = []
        avg_vals = []
        for el in elem_labels:
            d = max(0.0, min(1.0, d_max_env[el]))
            h_tgt = cls.analytical_damage_sizing(d, l0=l0, h_bg=h_bg, core_factor=core_factor,
                                                 process_factor=process_factor, d_core=d_core,
                                                 d_proc=d_proc, d_noise=d_noise)
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

        if causal_mode or max_frame_index is not None or max_frame_time is not None:
            desc = "Synthesized Causal Damage Sizing Target (Horizon: frame <= %d; Derived from %s via 1D PF sizing; strictly non-hindsight)" % (max_idx, damage_variable)
        else:
            desc = "Synthesized Damage-Informed Sizing Envelope (Derived from %s via 1D PF sizing; NOT a native stress error)" % damage_variable

        env_frame = step_dst.Frame(
            frameId=9999,
            frameValue=999.0,
            description=desc
        )
        fo_evol = env_frame.FieldOutput(name='EVOL', description='Element volume', type=SCALAR)
        fo_evol.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=elem_labels, data=evol_data)
        fo_eri = env_frame.FieldOutput(
            name='MISESERI',
            description='Synthesized Damage-Informed Sizing Target (Encoded as MISESERI for Abaqus UNIFORM_ERROR remeshing; not native stress error)',
            type=SCALAR
        )
        fo_eri.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=elem_labels, data=eri_vals)
        fo_avg = env_frame.FieldOutput(name='MISESAVG', description='Uniform Reference Scaling Base', type=SCALAR)
        fo_avg.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=elem_labels, data=avg_vals)

        odb_dst.save()
        odb_dst.close()
        return target_odb_path

    @classmethod
    def build_envelope_from_config(cls, config, source_odb_path, target_odb_path, damage_variable='SDV1', step_name=None,
                                   max_frame_index=None, max_frame_time=None, causal_mode=None):
        """Builds an advancing damage envelope directly using parameters configured in AdaptiveConfig.
        Ensures consistent error-target unit convention: error_target is defined on an identical percentage scale
        between the synthesized sizing target and the Abaqus RemeshingRule(errorTarget=...).
        Supports causal frame filtering to strictly prohibit hindsight scanning of future frames.
        """
        s_name = step_name or config.step_name
        if s_name not in ("Step-2", "RECOVERY_STEP"):
            s_name = "Step-2"

        m_idx = max_frame_index if max_frame_index is not None else getattr(config, 'max_frame_index', None)
        m_time = max_frame_time if max_frame_time is not None else getattr(config, 'max_frame_time', None)
        c_mode = causal_mode if causal_mode is not None else getattr(config, 'causal_mode', False)

        return cls.build_envelope_odb(
            source_odb_path=source_odb_path,
            target_odb_path=target_odb_path,
            l0=config.l0,
            h_bg=getattr(config, 'h_bg', config.max_h),
            error_target=config.error_target,
            step_name=s_name,
            damage_variable=damage_variable,
            frame_stride=getattr(config, 'frame_stride', 5),
            core_factor=getattr(config, 'core_factor', 2.5),
            process_factor=getattr(config, 'process_factor', 1.2),
            d_core=getattr(config, 'd_core', 0.40),
            d_proc=getattr(config, 'd_proc', 0.10),
            d_noise=getattr(config, 'd_noise', 0.08),
            max_frame_index=m_idx,
            max_frame_time=m_time,
            causal_mode=c_mode
        )


# ==============================================================================
# 5b. MULTI-STATE RECOVERY DONOR BUILDER (METHOD A.2)
# ==============================================================================

class MultiStateRecoveryDonorBuilder(object):
    """
    Method A.2: Reusable multi-state degraded-modulus continuum recovery donor engine.
    Constructs authentic continuum recovery models with elementwise degraded elasticity
    E_deg = E_0 * ((1 - d)^2 + k_res) across sequential crack propagation states,
    solves linear recovery steps in Abaqus/Standard, and synthesizes the native MISESERI
    maximum error envelope ODB across benchmark geometries.
    """

    @classmethod
    def synthesize_envelope_odb(cls, solved_odbs, target_odb_path, step_name='RECOVERY_STEP',
                                frame_desc="Multi-State Maximum Error Envelope"):
        """
        Synthesizes a multi-state maximum error envelope ODB from a list of solved recovery ODBs.
        Computes elementwise maximum MISESERI and mean MISESAVG across all states and writes
        a new envelope frame into the target ODB.
        """
        if not (ABAQUS_AVAILABLE or ODB_ACCESS_AVAILABLE):
            raise RuntimeError("FAIL_CLOSED: odbAccess or Abaqus environment is required to synthesize envelope ODB.")

        if not solved_odbs:
            raise ValueError("FAIL_CLOSED: solved_odbs list cannot be empty.")

        for p in solved_odbs:
            if not os.path.exists(p):
                raise IOError("FAIL_CLOSED: Solved recovery ODB does not exist: %s" % p)

        target_dir = os.path.dirname(target_odb_path)
        if target_dir and not os.path.exists(target_dir):
            safe_makedirs(target_dir)

        if os.path.exists(target_odb_path):
            os.remove(target_odb_path)

        shutil.copyfile(solved_odbs[0], target_odb_path)

        all_eri = {}
        all_avg = {}
        evol_dict = {}

        for path in solved_odbs:
            o = odbAccess.openOdb(path, readOnly=True)
            if step_name not in o.steps:
                avail = list(o.steps.keys())
                o.close()
                raise KeyError("FAIL_CLOSED: Step '%s' not found in '%s' (available: %s)" % (step_name, path, avail))
            step = o.steps[step_name]
            f = step.frames[-1]
            if "MISESERI" not in f.fieldOutputs or "MISESAVG" not in f.fieldOutputs:
                avail_f = list(f.fieldOutputs.keys())
                o.close()
                raise KeyError("FAIL_CLOSED: Required error fields missing in '%s' (available: %s)" % (path, avail_f))
            eri = f.fieldOutputs["MISESERI"]
            avg = f.fieldOutputs["MISESAVG"]
            ev = f.fieldOutputs.get("EVOL", None)
            for v in eri.values:
                all_eri.setdefault(v.elementLabel, []).append(float(v.data))
            for v in avg.values:
                all_avg.setdefault(v.elementLabel, []).append(float(v.data))
            if ev is not None:
                for v in ev.values:
                    evol_dict[v.elementLabel] = float(v.data)
            o.close()

        elem_labels = sorted(all_eri.keys())
        env_eri = tuple([[max(all_eri[el])] for el in elem_labels])
        env_avg = tuple([[py_sum(all_avg[el]) / float(len(all_avg[el]))] for el in elem_labels])

        odb_multi = odbAccess.openOdb(target_odb_path, readOnly=False)
        step_multi = odb_multi.steps[step_name]
        inst_multi = list(odb_multi.rootAssembly.instances.values())[0]

        env_frame_id = len(step_multi.frames)
        env_frame = step_multi.Frame(frameId=env_frame_id, frameValue=1.0, description=frame_desc)

        if evol_dict:
            env_evol = tuple([[evol_dict.get(el, 1.0)] for el in elem_labels])
            fo_evol = env_frame.FieldOutput(name='EVOL', description='Element volume', type=SCALAR)
            fo_evol.addData(position=WHOLE_ELEMENT, instance=inst_multi, labels=elem_labels, data=env_evol)

        fo_eri = env_frame.FieldOutput(name='MISESERI', description='Multi-state maximum MISESERI', type=SCALAR)
        fo_eri.addData(position=WHOLE_ELEMENT, instance=inst_multi, labels=elem_labels, data=env_eri)

        fo_avg = env_frame.FieldOutput(name='MISESAVG', description='Mean domain MISESAVG', type=SCALAR)
        fo_avg.addData(position=WHOLE_ELEMENT, instance=inst_multi, labels=elem_labels, data=env_avg)

        odb_multi.save()
        odb_multi.close()

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

        s = m.ConstrainedSketch(name='__profile__', sheetSize=max(config.plate_w, config.plate_h) * 2.5)
        seam_line = None

        if isinstance(adapter, (StraightNotchMode1Adapter, OffAxisHoleMode1Adapter)) and (config.notch_w is None or config.notch_w <= 0.001):
            s.rectangle(point1=(0.0, 0.0), point2=(config.plate_w, config.plate_h))
            for (hx, hy, hr) in adapter.get_hole_definitions():
                s.CircleByCenterPerimeter(center=(hx, hy), point1=(hx + hr, hy))
            ny = config.notch_y if config.notch_y is not None else 0.5
            na = config.notch_a if config.notch_a is not None else 0.5
            seam_line = ((0.0, ny, 0.0), (na, ny, 0.0), (0.5 * na, ny, 0.0))

        elif isinstance(adapter, FiveHolePlateAdapter):
            # Counterclockwise outer boundary with 2 edge arcs
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
            pts = adapter.get_outer_polygon_points()
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

        p.seedPart(size=seed_size, deviationFactor=0.05, minSizeFactor=0.02)
        adapter.apply_local_seeds(p, seed_size)
        p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
        elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
        elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
        p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
        p.generateMesh()

        p.Set(name='ALL_ELEM', faces=p.faces)
        a = m.rootAssembly
        inst = a.Instance(name=instance_name, part=p, dependent=ON)
        a.Set(name='ALL_ELEM', faces=inst.faces)

        # Steps matching potential donor names
        m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0)
        m.StaticStep(name='Step-2', previous='Step-1', timePeriod=1.0)
        if config.step_name not in ("Step-1", "Step-2"):
            m.StaticStep(name=config.step_name, previous='Step-2', timePeriod=1.0)

        return p, a, inst

    @classmethod
    def build_rule_kwargs(cls, config, rule_name, step_name, region=None, coarsen_opt=None, out_freq_opt=None):
        """Constructs RemeshingRule keyword arguments supporting UNIFORM_ERROR and MINIMUM_MAXIMUM."""
        kwargs = {
            'name': rule_name,
            'stepName': step_name,
            'variables': (config.variable,),
            'refinementFactor': config.refinement_factor,
            'specifyMinSize': True,
            'minElementSize': config.min_h,
            'specifyMaxSize': True,
            'maxElementSize': config.max_h,
        }
        if region is not None:
            kwargs['region'] = region

        if coarsen_opt is not None:
            kwargs['coarseningFactor'] = coarsen_opt
        elif config.coarsening_factor == "NOT_ALLOWED":
            kwargs['coarseningFactor'] = NOT_ALLOWED if 'NOT_ALLOWED' in globals() else "NOT_ALLOWED"
        else:
            kwargs['coarseningFactor'] = DEFAULT_LIMIT if 'DEFAULT_LIMIT' in globals() else "DEFAULT_LIMIT"

        if out_freq_opt is not None:
            kwargs['outputFrequency'] = out_freq_opt
        elif getattr(config, "output_frequency", "ALL_INCREMENTS") == "ALL_INCREMENTS":
            kwargs['outputFrequency'] = ALL_INCREMENTS if 'ALL_INCREMENTS' in globals() else "ALL_INCREMENTS"
        else:
            kwargs['outputFrequency'] = LAST_INCREMENT if 'LAST_INCREMENT' in globals() else "LAST_INCREMENT"

        if str(config.sizing_method).upper() == "MINIMUM_MAXIMUM":
            kwargs['sizingMethod'] = MINIMUM_MAXIMUM if 'MINIMUM_MAXIMUM' in globals() else "MINIMUM_MAXIMUM"
            kwargs['maxSolutionErrorTarget'] = float(config.max_solution_error_target)
            kwargs['minSolutionErrorTarget'] = float(config.min_solution_error_target)
            kwargs['meshBias'] = int(config.mesh_bias)
        else:
            kwargs['sizingMethod'] = UNIFORM_ERROR if 'UNIFORM_ERROR' in globals() else "UNIFORM_ERROR"
            kwargs['errorTarget'] = float(config.error_target)

        return kwargs

    @classmethod
    def execute_native_remesh(cls, config, donor_odb_path, output_dir, model_name=None, adapter_override=None, output_job_name=None):
        if not ABAQUS_AVAILABLE:
            raise RuntimeError("Abaqus environment not available; cannot execute native adaptiveRemesh.")

        adapter = adapter_override if adapter_override is not None else get_geometry_adapter(config)
        mname = model_name or ("Model_MethodA_" + str(config.case_id))

        if mname in mdb.models:
            del mdb.models[mname]
        m = mdb.Model(name=mname)
        if "Model-1" in mdb.models:
            del mdb.models["Model-1"]

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
                if getattr(config, 'causal_mode', False):
                    odb_donor.close()
                    raise ValueError(
                        "FAIL_CLOSED: Target step '%s' does not exist in donor ODB '%s' (available steps: %s)" % (
                            step_target, cur_donor, list(odb_donor.steps.keys())
                        )
                    )
                if "RECOVERY_STEP" in odb_donor.steps:
                    step_target = "RECOVERY_STEP"
                elif "Step-2" in odb_donor.steps:
                    step_target = "Step-2"
                elif "Step-1" in odb_donor.steps:
                    step_target = "Step-1"
                else:
                    step_target = list(odb_donor.steps.keys())[-1]

            step_obj = odb_donor.steps[step_target]
            n_donor_frames = len(step_obj.frames)
            if n_donor_frames == 0:
                odb_donor.close()
                raise ValueError("FAIL_CLOSED: Donor step '%s' in '%s' contains 0 frames." % (step_target, cur_donor))

            # Fail-closed causal horizon enforcement
            c_mode = getattr(config, 'causal_mode', False)
            m_idx = getattr(config, 'max_frame_index', None)
            m_time = getattr(config, 'max_frame_time', None)

            if c_mode or m_idx is not None or m_time is not None:
                if c_mode and m_idx is None and m_time is None:
                    odb_donor.close()
                    raise ValueError(
                        "FAIL_CLOSED: Causal adaptivity requires an explicit temporal horizon (max_frame_index or max_frame_time)."
                    )

                if m_idx is not None:
                    val = int(m_idx)
                    if val < 0:
                        odb_donor.close()
                        raise ValueError("FAIL_CLOSED: max_frame_index cannot be negative (got %d)" % val)
                    if val >= n_donor_frames:
                        odb_donor.close()
                        raise ValueError("FAIL_CLOSED: max_frame_index %d exceeds donor step '%s' frame count (%d)" % (
                            val, step_target, n_donor_frames
                        ))
                    if c_mode and (n_donor_frames - 1) > val:
                        odb_donor.close()
                        raise ValueError(
                            "FAIL_CLOSED: Donor step '%s' contains %d frames, exceeding causal horizon max_frame_index=%d. "
                            "Unconstrained future frames are forbidden in native causal donor." % (
                                step_target, n_donor_frames, val
                            )
                        )

                if m_time is not None:
                    t_target = float(m_time)
                    t_first = step_obj.frames[0].frameValue
                    if t_target < t_first - 1e-9:
                        odb_donor.close()
                        raise ValueError("FAIL_CLOSED: max_frame_time %f precedes first frame timestamp (%f) in step '%s'" % (
                            t_target, t_first, step_target
                        ))
                    if c_mode and step_obj.frames[-1].frameValue > t_target + 1e-9:
                        odb_donor.close()
                        raise ValueError(
                            "FAIL_CLOSED: Donor step '%s' final frame time %f exceeds causal horizon max_frame_time=%f. "
                            "Future frames are forbidden in native causal donor." % (
                                step_target, step_obj.frames[-1].frameValue, t_target
                            )
                        )

                for i in range(1, n_donor_frames):
                    if step_obj.frames[i].frameValue < step_obj.frames[i-1].frameValue - 1e-9:
                        odb_donor.close()
                        raise ValueError("FAIL_CLOSED: Donor step '%s' frames are non-monotonic in time at frame %d" % (
                            step_target, i
                        ))

            target_frame = step_obj.frames[-1]
            if config.variable not in target_frame.fieldOutputs:
                odb_donor.close()
                raise ValueError(
                    "FAIL_CLOSED: Required indicator variable '%s' not found in donor step '%s' frame %d field outputs." % (
                        config.variable, step_target, target_frame.frameId
                    )
                )

            # Explicitly ensure CAE model has the target step matching the donor ODB (resolving F1728-R30)
            if step_target not in m.steps:
                prev_step = list(m.steps.keys())[-1]
                m.StaticStep(name=step_target, previous=prev_step, timePeriod=1.0)

            rule_name = "Rule_MethodA_%s_p%d" % (str(config.case_id), pass_idx + 1)
            if rule_name in m.remeshingRules:
                del m.remeshingRules[rule_name]

            rule_kwargs = cls.build_rule_kwargs(
                config=config,
                rule_name=rule_name,
                step_name=step_target,
                region=inst.sets['ALL_ELEM'],
                coarsen_opt=coarsen_opt,
                out_freq_opt=out_freq_opt
            )
            m.RemeshingRule(**rule_kwargs)

            m.adaptiveRemesh(odb=odb_donor)
            odb_donor.close()

        safe_makedirs(output_dir)
        job_base = output_job_name if output_job_name is not None else ("PK_ADAPT_" + str(config.case_id).upper())
        if job_base.endswith("_PHYS"):
            base_name = job_base[:-5]
        else:
            base_name = job_base
        if base_name in mdb.jobs:
            del mdb.jobs[base_name]
        j = mdb.Job(name=base_name, model=m.name, type=ANALYSIS)
        j.writeInput(consistencyChecking=OFF)

        raw_inp = base_name + ".inp"
        out_phys_inp = os.path.join(output_dir, base_name + "_PHYS.inp")
        if os.path.exists(raw_inp):
            if os.path.exists(out_phys_inp):
                os.remove(out_phys_inp)
            shutil.move(raw_inp, out_phys_inp)

        return out_phys_inp


# ==============================================================================
# 6. UNIFIED HIGH-LEVEL ENTRYPOINT: run_method_a_case (FAIL-CLOSED)
# ==============================================================================

def run_method_a_case(case_config, authentic_donor_odb=None, output_directory=None, abaqus_model_name=None, fail_closed=True):
    """
    Unified high-level entrypoint executing the complete Method A pipeline.
    Fail-closed: requires valid donor, Abaqus CAE environment, successful native remeshing,
    passing FE quality audit (det(J) > 0), and valid 3-layer production deck.
    """
    if isinstance(case_config, str):
        cfg = AdaptiveConfig.from_json(case_config)
    else:
        cfg = case_config

    out_dir = output_directory or cfg.output_dir
    safe_makedirs(out_dir)

    # 1. Fail-closed Donor ODB Validation
    if not authentic_donor_odb:
        err_msg = "Donor ODB path not specified for case %s. Native remeshing requires an authentic donor ODB." % cfg.case_id
        if fail_closed:
            raise FileNotFoundError(err_msg)
        return {"status": "FAILED", "error": err_msg}

    donor_list = [p.strip() for p in authentic_donor_odb.split(",")] if isinstance(authentic_donor_odb, str) else list(authentic_donor_odb)
    for dp in donor_list:
        if not os.path.exists(dp):
            err_msg = "Donor ODB does not exist: %s" % dp
            if fail_closed:
                raise FileNotFoundError(err_msg)
            return {"status": "FAILED", "error": err_msg}

    # 2. Fail-closed Abaqus Environment Check
    if not ABAQUS_AVAILABLE:
        err_msg = "Abaqus CAE environment not available (ABAQUS_AVAILABLE=False). Native remeshing cannot execute."
        if fail_closed:
            raise RuntimeError(err_msg)
        return {"status": "FAILED", "error": err_msg}

    adapter = get_geometry_adapter(cfg)
    job_base = "PK_F1728_" + str(cfg.case_id).upper()
    phys_inp_path = os.path.join(out_dir, job_base + "_ADAPT_PHYS.inp")
    prod_inp_path = os.path.join(out_dir, job_base + "_PROD.inp")
    audit_json_path = os.path.join(out_dir, job_base + "_AUDIT.json")

    # 3. Stale File Rejection Guard: purge any pre-existing output files before remeshing
    for stale_path in [phys_inp_path, prod_inp_path, audit_json_path]:
        if os.path.exists(stale_path):
            os.remove(stale_path)

    # 4. Execute Native Remeshing
    gen_phys = AbaqusNativeRemeshingEngine.execute_native_remesh(
        cfg, authentic_donor_odb, out_dir, model_name=abaqus_model_name
    )

    if not gen_phys or not os.path.exists(gen_phys) or os.path.getsize(gen_phys) == 0:
        err_msg = "AbaqusNativeRemeshingEngine failed to produce a valid physical mesh at %s" % str(gen_phys)
        if fail_closed:
            raise RuntimeError(err_msg)
        return {"status": "FAILED", "error": err_msg}

    if gen_phys != phys_inp_path:
        if os.path.exists(phys_inp_path):
            os.remove(phys_inp_path)
        shutil.move(gen_phys, phys_inp_path)

    # 5. Fail-Closed Mesh Quality Audit
    audit_res = MeshQualityAuditEngine.evaluate_mesh(phys_inp_path, l0_mm=cfg.l0, adapter=adapter)
    total_elements = audit_res.get("total_elements", 0)
    if total_elements <= 0:
        err_msg = "Mesh quality audit failed: generated mesh contains 0 elements."
        if fail_closed:
            raise ValueError(err_msg)
        return {"status": "FAILED", "error": err_msg}

    distorted = audit_res.get("distorted_elements", 0)
    jacobian_valid = audit_res.get("jacobian_valid", True)
    if distorted > 0 or not jacobian_valid:
        err_msg = "Mesh quality audit failed: detected %d distorted elements or non-positive Jacobians." % distorted
        if fail_closed:
            raise ValueError(err_msg)
        return {"status": "FAILED", "error": err_msg, "audit_metrics": audit_res}

    # 6. Build 3-Layer Production Deck
    deck_res = ProductionDeckBuilder.build_deck(
        phys_inp_path, prod_inp_path, job_base + "_PROD", cfg
    )
    if not os.path.exists(prod_inp_path) or os.path.getsize(prod_inp_path) == 0:
        err_msg = "ProductionDeckBuilder failed to generate production deck at %s" % prod_inp_path
        if fail_closed:
            raise RuntimeError(err_msg)
        return {"status": "FAILED", "error": err_msg}

    audit_res["production_deck"] = deck_res
    audit_res["case_id"] = cfg.case_id
    audit_res["benchmark_name"] = cfg.benchmark_name
    audit_res["geometry_type"] = cfg.geometry_type
    audit_res["remesh_performed_in_session"] = True
    audit_res["donor_odb"] = authentic_donor_odb

    with open(audit_json_path, "w") as f:
        json.dump(audit_res, f, indent=2)

    return {
        "status": "SUCCESS",
        "case_id": cfg.case_id,
        "physical_mesh": phys_inp_path,
        "production_deck": prod_inp_path,
        "audit_json": audit_json_path,
        "audit_metrics": audit_res
    }


# ==============================================================================
# 7. CLI INTERFACE
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Reusable 2D Adaptive Framework Engine")
    parser.add_argument("--config", type=str, required=True, help="Path to benchmark JSON configuration")
    parser.add_argument("--run-case", action="store_true", default=False, help="Run complete Method A pipeline")
    parser.add_argument("--odb", type=str, default=None, help="Path to authentic donor ODB")
    parser.add_argument("--audit-mesh", type=str, default=None, help="Audit FE quality of physical INP deck")
    parser.add_argument("--build-deck", type=str, default=None, help="Convert physical INP deck to 3-layer UEL deck")
    parser.add_argument("--output-deck", type=str, default=None, help="Target path for 3-layer UEL deck")
    parser.add_argument("--output-dir", type=str, default=None, help="Target output directory")
    parser.add_argument("--step1-only", action="store_true", default=False, help="Build Step 1 only")
    parser.add_argument("--build-envelope", action="store_true", default=False, help="Synthesize advancing damage envelope donor ODB")
    parser.add_argument("--source-odb", type=str, default=None, help="Source coupled fracture ODB for envelope synthesis")
    parser.add_argument("--output-odb", type=str, default=None, help="Output path for synthesized envelope ODB")
    parser.add_argument("--max-frame-index", type=int, default=None, help="Maximum frame index for causal horizon (t <= t_remesh)")
    parser.add_argument("--max-frame-time", type=float, default=None, help="Maximum frame time for causal horizon (t <= t_remesh)")
    parser.add_argument("--causal-mode", action="store_true", default=False, help="Enforce causal adaptivity without hindsight")
    argv = sys.argv[1:]
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    args, unknown = parser.parse_known_args(argv)

    cfg = AdaptiveConfig.from_json(args.config)
    adapter = get_geometry_adapter(cfg)
    print("Loaded Benchmark: %s (Case: %s, Type: %s)" % (cfg.benchmark_name, cfg.case_id, cfg.geometry_type))

    if args.build_envelope:
        src = args.source_odb or args.odb
        dst = args.output_odb
        if not src or not dst:
            sys.stderr.write("ERROR: --build-envelope requires --source-odb (or --odb) and --output-odb\n")
            sys.exit(1)
        print("\nSynthesizing Advancing Damage Envelope Donor ODB via Config-Driven Builder...")
        AdvancingDamageEnvelopeBuilder.build_envelope_from_config(
            config=cfg,
            source_odb_path=src,
            target_odb_path=dst,
            max_frame_index=args.max_frame_index,
            max_frame_time=args.max_frame_time,
            causal_mode=args.causal_mode
        )
        print("Successfully created envelope donor: %s" % dst)
        return

    if args.run_case:
        print("\nExecuting Unified Method A Pipeline for %s (FAIL-CLOSED)..." % cfg.case_id)
        try:
            res = run_method_a_case(
                cfg, authentic_donor_odb=args.odb, output_directory=args.output_dir, fail_closed=True
            )
            print("Pipeline Status: %s" % res["status"])
            print("  Physical Mesh:   %s" % str(res["physical_mesh"]))
            print("  Production Deck: %s" % str(res["production_deck"]))
            print("  Audit Summary:   %s" % str(res["audit_json"]))
        except Exception as exc:
            import traceback
            traceback.print_exc()
            sys.stderr.write("FATAL ERROR in run_method_a_case: %s\n" % str(exc))
            sys.exit(1)
        return

    if args.audit_mesh:
        print("\nAuditing mesh: %s" % args.audit_mesh)
        res = MeshQualityAuditEngine.evaluate_mesh(args.audit_mesh, l0_mm=cfg.l0, adapter=adapter)
        print("Audit Results:")
        for k, v in res.items():
            print("  %s: %s" % (k, str(v)))

    if args.build_deck and args.output_deck:
        print("\nBuilding 3-layer UEL production deck...")
        job_name = os.path.splitext(os.path.basename(args.output_deck))[0]
        res = ProductionDeckBuilder.build_deck(
            args.build_deck, args.output_deck, job_name, cfg, step1_only=args.step1_only
        )
        print("Built UEL Deck: %s (%d layered elements)" % (res["deck_path"], res["total_layered_elements"]))
        print("UEL Hash Verified: %s" % str(res.get("uel_hash_verified")))


if __name__ == "__main__":
    main()
