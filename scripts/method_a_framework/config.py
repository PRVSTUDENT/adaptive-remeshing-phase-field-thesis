# -*- coding: utf-8 -*-
"""
scripts/method_a_framework/config.py
====================================
Configuration management and validation for the Reusable Method A Adaptive-Remeshing Framework.

Governing Review Reference: /goal F1715
"""

import os
import json


class FrameworkConfig(object):
    """
    Configuration specification for an automated Method A adaptive-remeshing
    and phase-field fracture simulation workflow.
    """

    DEFAULT_CONSTITUTIVE_SPLIT = "amor"  # "amor", "spectral", "isotropic"
    DEFAULT_K_RESIDUAL = 1.0e-7
    DEFAULT_REFINEMENT_FACTOR = 10.0
    DEFAULT_H_MAX = 0.020  # mm
    DEFAULT_H_MIN = 0.001  # mm

    def __init__(self, data=None):
        self.benchmark_name = "unnamed_benchmark"
        self.geometry = {
            "plate_width": 1.0,
            "plate_height": 1.0,
            "notch": None,       # dict or None
            "voids": []          # list of dicts: {"type": "circle"|"semicircle_left"|"semicircle_right", "x": ..., "y": ..., "r": ...}
        }
        self.material = {
            "E": 210.0,          # GPa (or kN/mm^2)
            "nu": 0.30,
            "Gc": 2.7e-3,        # kN/mm (or kJ/m^2)
            "l0": 0.008,         # mm (length scale)
            "k_residual": self.DEFAULT_K_RESIDUAL,
            "constitutive_split": self.DEFAULT_CONSTITUTIVE_SPLIT
        }
        self.remeshing = {
            "indicator": "MISESERI",
            "sizing_method": "UNIFORM_ERROR",
            "error_target_pct": 1.85,
            "h_min": self.DEFAULT_H_MIN,
            "h_max": self.DEFAULT_H_MAX,
            "refinement_factor": self.DEFAULT_REFINEMENT_FACTOR,
            "coarsening_allowed": False
        }
        self.loading = {
            "step1_disp": 0.0050,
            "step2_disp": 0.0100,
            "step1_dt": 5.0e-4,
            "step2_dt": 2.0e-4,
            "dt_min": 1.0e-9
        }
        self.paths = {
            "coarse_inp": "",
            "adapted_phys_inp": "",
            "production_inp": "",
            "uel_source": "",
            "output_dir": ""
        }

        if data:
            self.load_from_dict(data)

    def load_from_dict(self, d):
        if "benchmark_name" in d:
            self.benchmark_name = str(d["benchmark_name"])
        for section in ["geometry", "material", "remeshing", "loading", "paths"]:
            if section in d and isinstance(d[section], dict):
                getattr(self, section).update(d[section])

    def validate(self):
        """
        Validate all parameters against physical and numerical feasibility bounds.
        Raises ValueError if invalid.
        """
        # Material validation
        mat = self.material
        if mat["E"] <= 0.0:
            raise ValueError("Young's modulus E must be strictly positive, got: %s" % mat["E"])
        if not (-1.0 < mat["nu"] < 0.5):
            raise ValueError("Poisson's ratio nu must be in (-1, 0.5), got: %s" % mat["nu"])
        if mat["Gc"] <= 0.0:
            raise ValueError("Critical fracture energy Gc must be positive, got: %s" % mat["Gc"])
        if mat["l0"] <= 0.0:
            raise ValueError("Phase-field length scale l0 must be positive, got: %s" % mat["l0"])
        if mat["constitutive_split"] not in ["amor", "spectral", "isotropic", "mixed"]:
            raise ValueError("Unsupported constitutive split: %s" % mat["constitutive_split"])

        # Remeshing bounds validation
        remesh = self.remeshing
        if remesh["h_min"] <= 0.0 or remesh["h_max"] <= 0.0:
            raise ValueError("Sizing bounds h_min and h_max must be positive.")
        if remesh["h_min"] >= remesh["h_max"]:
            raise ValueError("h_min (%s) must be strictly less than h_max (%s)" % (remesh["h_min"], remesh["h_max"]))
        if remesh["error_target_pct"] <= 0.0:
            raise ValueError("error_target_pct must be positive, got: %s" % remesh["error_target_pct"])

        # Spatial resolution check: h_min should be at most l0 / 2 for regularized phase-field
        if remesh["h_min"] > mat["l0"] / 2.0:
            raise ValueError("h_min (%s) exceeds l0/2 (%s); cannot resolve phase-field process zone." %
                             (remesh["h_min"], mat["l0"] / 2.0))

        # Geometry validation
        geo = self.geometry
        if geo["plate_width"] <= 0.0 or geo["plate_height"] <= 0.0:
            raise ValueError("Plate dimensions must be positive.")

        return True

    def to_dict(self):
        return {
            "benchmark_name": self.benchmark_name,
            "geometry": self.geometry,
            "material": self.material,
            "remeshing": self.remeshing,
            "loading": self.loading,
            "paths": self.paths
        }

    def save(self, filepath):
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath):
        with open(filepath, "r") as f:
            d = json.load(f)
        cfg = cls(d)
        cfg.validate()
        return cfg
