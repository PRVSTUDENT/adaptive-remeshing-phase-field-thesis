# -*- coding: utf-8 -*-
"""
scripts/method_a_framework/postprocessor.py
===========================================
Scientific postprocessing, reaction force equilibrium extraction,
volume-integrated energy assembly, and damage validation for the
Reusable Method A Adaptive-Remeshing Framework.
"""

import os
import json
import math


class SimulationPostprocessor(object):
    """
    Postprocesses phase-field fracture simulation results from extracted
    telemetry dictionaries or Abaqus ODB output structures.
    """

    def __init__(self, config):
        self.config = config
        self.fu_curve = []       # list of (u, F) tuples
        self.energy_data = []    # list of dicts: {"displacement_mm": ..., "elastic_energy": ..., "fracture_energy": ...}
        self.damage_fields = {}  # milestone -> {eid: d}

    def process_telemetry(self, raw_telemetry):
        """
        Processes and validates raw extracted telemetry:
        raw_telemetry: {"fu_history": [...], "energy_history": [...], "milestone_damage_fields": {...}}
        """
        # 1. Process F-u curve
        fu_history = raw_telemetry.get("fu_history", [])
        self.fu_curve = []
        peak_f = 0.0
        peak_u = 0.0

        for r in fu_history:
            u = float(r.get("displacement_mm", 0.0))
            f_val = float(r.get("tensile_force_kN", 0.0))
            if math.isnan(f_val):
                raise ValueError("Encountered NaN in tensile reaction force at displacement u = %s" % u)
            self.fu_curve.append((u, f_val))
            if f_val > peak_f:
                peak_f = f_val
                peak_u = u

        # Compute initial elastic stiffness K0 from early linear loading
        k0 = 0.0
        if len(self.fu_curve) >= 2:
            u_early, f_early = self.fu_curve[1]
            if u_early > 0:
                k0 = f_early / u_early

        # Compute external work W_ext by trapezoidal integration: W = sum 0.5*(F_i + F_{i-1})*(u_i - u_{i-1})
        w_ext = 0.0
        for i in range(1, len(self.fu_curve)):
            u_prev, f_prev = self.fu_curve[i - 1]
            u_curr, f_curr = self.fu_curve[i]
            du = u_curr - u_prev
            if du > 0:
                w_ext += 0.5 * (f_curr + f_prev) * du

        # 2. Process energy histories
        energy_history = raw_telemetry.get("energy_history", [])
        self.energy_data = []
        for r in energy_history:
            u = float(r.get("displacement_mm", 0.0))
            e_elas = float(r.get("elastic_energy_kNmm", 0.0))
            e_frac = float(r.get("fracture_energy_kNmm", 0.0))
            e_tot = float(r.get("total_energy_kNmm", 0.0))
            if math.isnan(e_elas) or math.isnan(e_frac):
                raise ValueError("Encountered NaN in volume-integrated element energy at u = %s" % u)
            self.energy_data.append({
                "displacement_mm": u,
                "elastic_energy_kNmm": e_elas,
                "fracture_energy_kNmm": e_frac,
                "total_energy_kNmm": e_tot
            })

        # 3. Process milestone damage fields & check bounds
        milestone_data = raw_telemetry.get("milestone_damage_fields", {})
        self.damage_fields = {}
        for mkey, mdata in milestone_data.items():
            d_map = mdata.get("element_damage", {})
            invalid_elements = []
            for eid, d_val in d_map.items():
                if d_val < -1.0e-5 or d_val > 1.05:  # small numerical tolerance for projection
                    invalid_elements.append((eid, d_val))
            if invalid_elements:
                raise ValueError(
                    "Damage bounds violated in milestone %s: %d elements out of [0, 1]. Sample: %s"
                    % (mkey, len(invalid_elements), invalid_elements[:5])
                )
            self.damage_fields[mkey] = d_map

        summary = {
            "benchmark": self.config.benchmark_name,
            "peak_force_kN": round(peak_f, 5),
            "displacement_at_peak_mm": round(peak_u, 5),
            "initial_stiffness_kN_per_mm": round(k0, 2),
            "external_work_kNmm": round(w_ext, 6),
            "data_points_fu": len(self.fu_curve),
            "data_points_energy": len(self.energy_data),
            "milestones_count": len(self.damage_fields)
        }
        return summary
